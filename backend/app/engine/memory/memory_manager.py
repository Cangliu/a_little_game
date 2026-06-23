"""Memory Manager — three-layer human-like memory system.

Implements a forgetting curve that mimics human memory:
- Working Memory: last 5 events (full text)
- Short-term Memory: last 50 years (summaries)
- Long-term Memory: older events (heavily compressed, only important ones)

Special "unforgettable" events (breakthroughs, NPC meetings, life/death)
never decay and are always available for retrieval.
"""
from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

from .retriever import HybridRetriever
from .compressor import MemoryCompressor

if TYPE_CHECKING:
    from ...models import GameState
    from ..ai.llm_client import LLMClient
    from ..ai.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

# Configuration
WORKING_MEMORY_SIZE = 5
SHORT_TERM_MAX_AGE = 50  # Events older than 50 years get compressed
COMPRESSION_INTERVAL = 30  # Compress every 30 years


class MemoryManager:
    """Three-layer memory system with decay and retrieval.

    Layer 1 - Working Memory:
        Last 5 events, full text preserved.
        Used for: immediate AI narrative context.

    Layer 2 - Short-term Memory:
        Events from the last 50 years, summary form (1-2 sentences).
        Used for: AI needing to review recent history.

    Layer 3 - Long-term Memory:
        Events older than 50 years, heavily compressed.
        Only "important"/"danger" events and NPC interactions survive.
        Normal events are discarded (simulating forgetting).
        Used for: BM25 retrieval when triggered by keywords.
    """

    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        prompt_builder: Optional["PromptBuilder"] = None,
    ):
        self._retriever = HybridRetriever()
        self._compressor = MemoryCompressor(
            llm_client=llm_client,
            prompt_builder=prompt_builder,
            use_llm=(llm_client is not None),
        )
        self._last_compression_age: int = 0

    def record_event(self, state: "GameState", event: dict) -> None:
        """Record a single event into working memory.

        If working memory exceeds capacity, oldest event moves to short-term.
        """
        memory_entry = {
            "text": event.get("text", ""),
            "expanded_text": event.get("expanded_text", ""),
            "age": state.age,
            "type": event.get("event_type", "normal"),
            "category": event.get("category", "common"),
            "tags": event.get("tags", []),
            "involved_npc": event.get("involved_npc", ""),
        }

        state.memory_working.append(memory_entry)

        # Overflow: move oldest to short-term
        while len(state.memory_working) > WORKING_MEMORY_SIZE:
            overflow = state.memory_working.pop(0)
            # Convert to summary form for short-term
            summary_entry = {
                "text": overflow.get("text", "")[:60],
                "age": overflow.get("age", 0),
                "type": overflow.get("type", "normal"),
                "tags": overflow.get("tags", [])[:3],
                "involved_npc": overflow.get("involved_npc", ""),
            }
            state.memory_short_term.append(summary_entry)

    def record_events(self, state: "GameState", events: list) -> None:
        """Record multiple events from a year's advancement."""
        for event in events:
            self.record_event(state, event)

    def tick_year(self, state: "GameState") -> None:
        """Called at end of each year. Handles periodic compression.

        Every COMPRESSION_INTERVAL years:
        - Short-term events older than SHORT_TERM_MAX_AGE → compress to long-term
        - Rebuild BM25 index
        - Update biography summary
        """
        years_since_compression = state.age - self._last_compression_age

        if years_since_compression >= COMPRESSION_INTERVAL:
            self._run_compression(state)
            self._last_compression_age = state.age

    def build_context_for_ai(self, state: "GameState", query_event: Optional[dict] = None) -> str:
        """Assemble memory context for AI prompt (~1500 tokens budget).

        Output format:
        [传记摘要] ...
        [重要记忆] ...
        [近期经历] ...
        [人际关系] (handled separately by NPCManager)
        """
        parts = []

        # 1. Biography summary
        bio = state.biography_summary
        if bio:
            parts.append(f"[传记摘要] {bio}")
        else:
            parts.append("[传记摘要] 尚无往事可述")

        # 2. Important long-term memories (always available)
        if state.memory_long_term:
            important = [
                m for m in state.memory_long_term
                if m.get("type") in ("important", "danger") or m.get("tags")
            ][:8]  # Limit to 8 entries
            if important:
                important_lines = [
                    f"  {m.get('age', '?')}岁: {m.get('text', '')[:40]}"
                    for m in important
                ]
                parts.append("[重要记忆]\n" + "\n".join(important_lines))

        # 3. Recent experiences (working memory - full text)
        if state.memory_working:
            recent_lines = [
                f"  {m.get('age', '?')}岁: {m.get('text', '')}"
                for m in state.memory_working[-5:]
            ]
            parts.append("[近期经历]\n" + "\n".join(recent_lines))

        # 4. Query-relevant memories (BM25 retrieval)
        if query_event:
            query_text = query_event.get("text", "")
            if query_text:
                relevant = self.retrieve(state, query_text, top_k=3)
                if relevant:
                    relevant_lines = [
                        f"  {m.get('age', '?')}岁: {m.get('text', '')[:40]}"
                        for m in relevant
                    ]
                    parts.append("[相关记忆]\n" + "\n".join(relevant_lines))

        return "\n\n".join(parts)

    def retrieve(self, state: "GameState", query: str, top_k: int = 5) -> list:
        """BM25 keyword retrieval across short-term and long-term memory.

        Searches all stored memories for content related to the query.
        """
        # Combine all searchable memories
        all_memories = state.memory_short_term + state.memory_long_term

        if not all_memories:
            return []

        # Build index on-the-fly (memories are small enough)
        self._retriever.index(all_memories)
        return self._retriever.search(query, top_k=top_k)

    # ── Private methods ───────────────────────────────────────────────

    def get_recent_context(self, state: "GameState") -> str:
        """Build realm-adaptive recent experience context.

        Low realms (0-1): last 5 working memory items (every year matters).
        High realms (2+): last 3 working memory + 2-3 milestone samples
            from short-term memory for temporal depth.
        """
        lines = []

        if state.realm < 2:
            # Low realm: simple recent events
            for m in state.memory_working[-5:]:
                lines.append(f"  {m.get('age', '?')}岁: {m.get('text', '')}")
        else:
            # High realm: immediate + retrospective milestones
            for m in state.memory_working[-3:]:
                lines.append(f"  {m.get('age', '?')}岁: {m.get('text', '')}")

            if state.memory_short_term:
                milestones = self._sample_milestones(
                    state.memory_short_term, count=3
                )
                if milestones:
                    lines.append("  ---回顾---")
                    for m in milestones:
                        lines.append(
                            f"  {m.get('age', '?')}岁: {m.get('text', '')[:40]}"
                        )

        return "\n".join(lines)

    @staticmethod
    def _sample_milestones(memories: list, count: int = 3) -> list:
        """Sample milestones from short-term memory with time spread.

        Prioritizes important/danger events, then falls back to
        evenly-spaced sampling across the time range.
        """
        if len(memories) <= count:
            return memories

        # Prefer important events
        important = [
            m for m in memories
            if m.get("type") in ("important", "danger")
        ]
        if len(important) >= count:
            step = len(important) // count
            return [important[i * step] for i in range(count)]

        # Not enough important ones: use important + evenly sampled normals
        result = list(important)
        remaining_count = count - len(result)
        if remaining_count > 0:
            # Evenly sample from all memories (skip already-selected)
            important_set = {id(m) for m in important}
            normals = [m for m in memories if id(m) not in important_set]
            if normals:
                step = max(1, len(normals) // remaining_count)
                for i in range(remaining_count):
                    idx = min(i * step, len(normals) - 1)
                    result.append(normals[idx])

        # Sort by age for chronological order
        result.sort(key=lambda m: m.get("age", 0))
        return result

    def _run_compression(self, state: "GameState") -> None:
        """Compress old short-term memories to long-term.

        Moves events older than SHORT_TERM_MAX_AGE from short-term
        to long-term after compression.
        Important/danger events are preserved in short-term regardless of age.
        """
        if not state.memory_short_term:
            return

        cutoff_age = state.age - SHORT_TERM_MAX_AGE

        # Partition short-term into "old" and "recent"
        # Important/danger events are never aged out (kept in recent)
        old_memories = []
        recent_memories = []
        for m in state.memory_short_term:
            mem_age = m.get("age", 0)
            mem_type = m.get("type", "")
            is_protected = mem_type in ("important", "danger")
            if mem_age < cutoff_age and not is_protected:
                old_memories.append(m)
            else:
                recent_memories.append(m)

        if not old_memories:
            return

        logger.debug(
            "Compressing %d old memories (before age %d)",
            len(old_memories), cutoff_age
        )

        # Compress old memories
        compressed = self._compressor.compress_events(old_memories, state.age)

        # Move compressed to long-term
        state.memory_long_term.extend(compressed)

        # Keep only recent in short-term
        state.memory_short_term = recent_memories

        # Update biography
        all_important = [
            m for m in (state.memory_working + state.memory_short_term + state.memory_long_term)
            if m.get("type") in ("important", "danger")
               or any(kw in m.get("text", "") for kw in ["突破", "觉醒", "飞升", "拜师"])
        ]
        if all_important:
            state.biography_summary = self._compressor.generate_biography(
                all_important,
                current_bio=state.biography_summary,
                age=state.age,
            )

        logger.debug(
            "Compression complete. Short-term: %d, Long-term: %d",
            len(state.memory_short_term), len(state.memory_long_term)
        )
