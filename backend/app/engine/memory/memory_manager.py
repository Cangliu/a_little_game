"""Memory Manager — three-layer human-like memory system.

Implements a forgetting curve that mimics human memory:
- Working Memory: realm-adaptive capacity (5/7/9 events, full text)
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
WORKING_MEMORY_BASE_SIZE = 5  # Base capacity (realm 0-1)
SHORT_TERM_MAX_AGE = 50  # Events older than 50 years get compressed
COMPRESSION_INTERVAL = 30  # Compress every 30 years
LONG_TERM_MAX_SIZE = 100  # Max long-term memory entries (evict oldest normal when exceeded)
SHORT_TERM_MAX_SIZE = 80  # Max short-term entries before emergency compression


class MemoryManager:
    """Three-layer memory system with decay and retrieval.

    Layer 1 - Working Memory:
        Realm-adaptive capacity (5/7/9 events), full text preserved.
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

    @staticmethod
    def _get_working_memory_size(state: "GameState") -> int:
        """Realm-adaptive working memory capacity.

        - realm 0-1 (凡人/练气): 5 entries (dense yearly events)
        - realm 2-3 (筑基/金丹): 7 entries (larger time steps need more context)
        - realm 4-5 (元婴/化神): 9 entries (decades per step, max depth)
        """
        realm = getattr(state, "realm", 0)
        if realm >= 4:
            return 9
        elif realm >= 2:
            return 7
        return 5

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

        # Overflow: move oldest to short-term (realm-adaptive capacity)
        capacity = self._get_working_memory_size(state)
        while len(state.memory_working) > capacity:
            overflow = state.memory_working.pop(0)
            # Convert to summary form for short-term
            # 保留更丰富的文本供检索: 优先用expanded_text摘要, 其次用完整text
            expanded = overflow.get("expanded_text", "")
            raw_text = overflow.get("text", "")
            # 短期记忆文本: expanded前120字(含足够语义) + 骨架text兜底
            search_text = (expanded[:120] if expanded else raw_text) or raw_text
            summary_entry = {
                "text": search_text,
                "age": overflow.get("age", 0),
                "type": overflow.get("type", "normal"),
                "category": overflow.get("category", "common"),
                "tags": overflow.get("tags", []),
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

        Also triggers emergency compression if short-term exceeds capacity.
        """
        years_since_compression = state.age - self._last_compression_age

        # Emergency compression if short-term is overflowing
        if len(state.memory_short_term) > SHORT_TERM_MAX_SIZE:
            logger.debug(
                "Short-term overflow (%d > %d), forcing compression",
                len(state.memory_short_term), SHORT_TERM_MAX_SIZE
            )
            self._run_compression(state)
            self._last_compression_age = state.age
        elif years_since_compression >= COMPRESSION_INTERVAL:
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
        """BM25+Embedding hybrid retrieval across short-term and long-term memory.

        Searches all stored memories for content related to the query.
        Applies recency decay: recent memories rank higher at equal relevance.
        """
        # Combine all searchable memories
        all_memories = state.memory_short_term + state.memory_long_term

        if not all_memories:
            return []

        # Build index on-the-fly (memories are small enough)
        self._retriever.index(all_memories)
        return self._retriever.search(query, top_k=top_k, current_age=state.age)

    def retrieve_for_event(
        self, state: "GameState", candidate_texts: list[str], top_k: int = 3
    ) -> str:
        """Retrieve memories relevant to current candidate events.

        Uses top candidate event texts as query, returns formatted context
        for injection into EventDirector prompt.

        Excludes events already in working memory to avoid redundancy.
        """
        if not candidate_texts:
            return ""

        all_memories = state.memory_short_term + state.memory_long_term
        if not all_memories:
            return ""

        # Build query from top 3 candidate event texts (most relevant ones)
        query = "。".join(candidate_texts[:3])

        # Get working memory texts to deduplicate
        working_texts = {m.get("text", "")[:30] for m in state.memory_working}

        self._retriever.index(all_memories)
        results = self._retriever.search(query, top_k=top_k + 2, current_age=state.age)  # fetch extra for dedup

        # Filter out entries that overlap with working memory
        filtered = []
        for r in results:
            r_text = r.get("text", "")
            # Skip if first 30 chars match any working memory entry
            if r_text[:30] in working_texts:
                continue
            filtered.append(r)
            if len(filtered) >= top_k:
                break

        if not filtered:
            return ""

        # Format as context lines
        lines = []
        for m in filtered:
            age = m.get("age", "?")
            text = m.get("text", "")[:60]
            npc = m.get("involved_npc", "")
            suffix = f" [{npc}]" if npc else ""
            lines.append(f"  {age}岁: {text}{suffix}")

        return "\n".join(lines)

    # ── Private methods ───────────────────────────────────────────────

    def get_recent_context(self, state: "GameState") -> str:
        """Build realm-adaptive recent experience context.

        Low realms (0-1): last 5 working memory items (every year matters).
        High realms (2-3): last 5 working memory + 4 milestone samples.
        Very high realms (4+): last 5 working memory + 4 milestone samples.
        """
        lines = []

        if state.realm < 2:
            # Low realm: simple recent events
            for m in state.memory_working[-5:]:
                lines.append(f"  {m.get('age', '?')}岁: {m.get('text', '')}")
        else:
            # High realm: immediate context (5 items) + retrospective milestones
            for m in state.memory_working[-5:]:
                lines.append(f"  {m.get('age', '?')}岁: {m.get('text', '')}")

            if state.memory_short_term:
                milestones = self._sample_milestones(
                    state.memory_short_term, count=4
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

        # Evict oldest non-important entries if long-term exceeds capacity
        self._evict_long_term(state)

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

    @staticmethod
    def _evict_long_term(state: "GameState") -> None:
        """Evict oldest non-important entries when long-term memory exceeds capacity.

        Strategy:
        - Keep all 'important'/'danger' and NPC-related entries
        - Remove oldest 'compressed'/'compressed_batch' entries first
        - If still over limit, remove oldest normal entries
        """
        if len(state.memory_long_term) <= LONG_TERM_MAX_SIZE:
            return

        # Separate protected vs evictable
        protected = []
        evictable = []
        for m in state.memory_long_term:
            m_type = m.get("type", "")
            has_npc = bool(m.get("involved_npc", ""))
            is_protected = (
                m_type in ("important", "danger")
                or has_npc
            )
            if is_protected:
                protected.append(m)
            else:
                evictable.append(m)

        # If protected alone exceeds limit, keep all protected + newest evictable
        if len(protected) >= LONG_TERM_MAX_SIZE:
            state.memory_long_term = protected
            logger.debug("Long-term memory eviction: kept %d protected entries", len(protected))
            return

        # Keep enough evictable entries (newest first) to fill remaining slots
        slots_for_evictable = LONG_TERM_MAX_SIZE - len(protected)
        # Sort evictable by age ascending (oldest first), keep newest ones
        evictable.sort(key=lambda m: m.get("age", 0))
        kept_evictable = evictable[-slots_for_evictable:] if slots_for_evictable > 0 else []

        evicted_count = len(evictable) - len(kept_evictable)
        state.memory_long_term = protected + kept_evictable

        if evicted_count > 0:
            logger.debug(
                "Long-term memory eviction: removed %d old entries, kept %d total",
                evicted_count, len(state.memory_long_term)
            )
