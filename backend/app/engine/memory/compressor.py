"""Memory compressor — rule-based and LLM-based memory compression.

Handles the decay of memories from short-term to long-term storage,
implementing a forgetting curve that mimics human memory.
"""
from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..ai.llm_client import LLMClient
    from ..ai.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

# Events with these keywords are "unforgettable"
UNFORGETTABLE_KEYWORDS = [
    "突破", "飞升", "觉醒", "灵根", "渡劫", "拜师", "传承",
    "道侣", "结仇", "走火入魔", "陨落", "大机缘", "生死",
    "空间节点", "化神", "金丹", "元婴", "筑基", "npc_interaction",
    # 情感类关键词 — 确保情感记忆不被压缩丢失
    "悲伤", "愤怒", "感动", "挚爱", "死别", "离别", "经此",
    "永远", "背叛", "牺牲", "仇恨", "感激", "误解", "和解",
    "遗言", "师恩", "报恩",
]

# Event types that are always kept
IMPORTANT_EVENT_TYPES = {"important", "danger"}


class MemoryCompressor:
    """Compresses memories using rule-based or LLM-based strategies.

    Strategy A (default, no LLM): Rule-based compression
    - Keep first 20 chars of text + tags + effects summary
    - Discard "normal" events older than threshold
    - Always keep "important"/"danger" events

    Strategy B (with LLM): AI compression
    - Batch 10 events and ask LLM to compress into 3-5 sentences
    - Only used when LLM is available and explicitly enabled
    """

    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        prompt_builder: Optional["PromptBuilder"] = None,
        use_llm: bool = False,
    ):
        self._llm = llm_client
        self._prompt_builder = prompt_builder
        self._use_llm = use_llm and llm_client is not None

    @property
    def llm_available(self) -> bool:
        return self._use_llm and self._llm is not None and self._llm.available

    def compress_events(self, events: list, current_age: int = 0) -> list:
        """Compress a batch of events into long-term memory entries.

        Args:
            events: List of memory dicts from short-term memory
            current_age: Current character age (for decay calculation)

        Returns:
            List of compressed memory entries (fewer items, shorter text)
        """
        if not events:
            return []

        # Separate unforgettable from forgettable
        unforgettable = []
        forgettable = []

        for event in events:
            if self._is_unforgettable(event):
                unforgettable.append(event)
            else:
                forgettable.append(event)

        # Unforgettable events get rule-compressed (keep summary)
        compressed_unforgettable = [
            self._rule_compress_single(e) for e in unforgettable
        ]

        # Forgettable events: try LLM batch compression, fallback to rule-based
        compressed_forgettable = []
        if forgettable:
            if self.llm_available:
                batch_summary = self._llm_compress_batch(forgettable, current_age)
                if batch_summary:
                    compressed_forgettable.append({
                        "text": batch_summary,
                        "age": forgettable[-1].get("age", current_age),
                        "type": "compressed_batch",
                        "source_count": len(forgettable),
                    })
                else:
                    # LLM failed, fall back to rule-based
                    compressed_forgettable = self._rule_compress_batch(forgettable)
            else:
                compressed_forgettable = self._rule_compress_batch(forgettable)

        return compressed_unforgettable + compressed_forgettable

    def generate_biography(self, events: list, current_bio: str = "", age: int = 0) -> str:
        """Generate or update a biography summary from recent events.

        Without LLM: concatenate key event summaries.
        With LLM: ask AI to write a coherent biography paragraph.
        """
        if not events:
            return current_bio

        # Extract key moments
        key_moments = [
            e for e in events if self._is_unforgettable(e)
        ]
        if not key_moments:
            key_moments = events[-5:]  # Last 5 if no key moments

        if self.llm_available and self._prompt_builder:
            system_prompt, user_prompt = self._prompt_builder.build_compression_prompt(
                key_moments, current_age=age
            )
            result = self._llm.generate_sync(system_prompt, user_prompt, max_tokens=200)
            if result:
                return result

        # Rule-based biography
        parts = []
        for e in key_moments[-5:]:
            text = e.get("text", "")[:30]
            event_age = e.get("age", "?")
            parts.append(f"{event_age}岁{text}")

        return "；".join(parts) if parts else current_bio

    # ── Private methods ───────────────────────────────────────────────

    @staticmethod
    def _is_unforgettable(event: dict) -> bool:
        """Check if an event should never be forgotten."""
        # Check event type
        event_type = event.get("type", event.get("event_type", "normal"))
        if event_type in IMPORTANT_EVENT_TYPES:
            return True

        # Check text content
        text = event.get("text", "")
        for kw in UNFORGETTABLE_KEYWORDS:
            if kw in text:
                return True

        # Check tags
        tags = set(event.get("tags", []))
        if tags & {"npc_interaction", "breakthrough", "death", "awakening"}:
            return True

        return False

    @staticmethod
    def _rule_compress_single(event: dict) -> dict:
        """Rule-based compression for a single event.

        Preserves emotional keywords and NPC names in compressed text.
        """
        text = event.get("text", "")
        # Smart truncation: find a sentence boundary near the limit
        limit = 60 if any(kw in text for kw in ("悲伤", "愤怒", "感动", "死别", "离别", "背叛", "牺牲", "仇恨", "遗言")) else 40
        if len(text) > limit:
            # Try to break at punctuation for natural reading
            for sep in ("。", "，", "！", "…"):
                pos = text.rfind(sep, 0, limit)
                if pos > limit // 2:
                    compressed_text = text[:pos + 1]
                    break
            else:
                compressed_text = text[:limit]
        else:
            compressed_text = text

        return {
            "text": compressed_text,
            "age": event.get("age", 0),
            "type": event.get("type", event.get("event_type", "normal")),
            "tags": event.get("tags", [])[:3],  # Keep top 3 tags
            "compressed": True,
        }

    @staticmethod
    def _rule_compress_batch(events: list) -> list:
        """Rule-based batch compression: keep only 1 in 3 normal events.

        Uses smart truncation that preserves sentence boundaries.
        """
        if len(events) <= 3:
            result = []
            for e in events:
                text = e.get("text", "")
                # Try sentence boundary truncation
                limit = 40
                if len(text) > limit:
                    for sep in ("。", "，", "！"):
                        pos = text.rfind(sep, 0, limit)
                        if pos > limit // 2:
                            text = text[:pos + 1]
                            break
                    else:
                        text = text[:limit]
                result.append({
                    "text": text,
                    "age": e.get("age", 0),
                    "type": "compressed",
                    "compressed": True,
                })
            return result

        # Keep every 2nd event (simulating gradual memory fading)
        kept = events[::2]
        result = []
        for e in kept:
            text = e.get("text", "")
            limit = 40
            if len(text) > limit:
                for sep in ("。", "，", "！"):
                    pos = text.rfind(sep, 0, limit)
                    if pos > limit // 2:
                        text = text[:pos + 1]
                        break
                else:
                    text = text[:limit]
            result.append({
                "text": text,
                "age": e.get("age", 0),
                "type": "compressed",
                "source_count": 2,
                "compressed": True,
            })
        return result

    def _llm_compress_batch(self, events: list, current_age: int) -> Optional[str]:
        """Use LLM to compress a batch of events into a summary."""
        if not self._prompt_builder or not self._llm:
            return None

        system_prompt, user_prompt = self._prompt_builder.build_compression_prompt(
            events, current_age=current_age
        )

        return self._llm.generate_sync(
            system_prompt, user_prompt,
            max_tokens=200, temperature=0.5
        )
