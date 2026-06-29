"""Narrative layer — context-aware LLM expansion for events.

When an event is selected, the narrative provider checks if it needs
LLM expansion (brief outline -> rich narrative). The expansion now
includes full NPC interaction history, story arc context, and
unresolved plot hooks for maximum narrative coherence.

Falls back to raw text when LLM is unavailable.
"""
from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .ai.llm_client import LLMClient
    from .ai.prompt_builder import PromptBuilder
    from .npc.npc_manager import NPCManager
    from .memory.memory_manager import MemoryManager
    from .causality import CausalityManager
    from .story_arc import StoryArcPlanner
    from .main_storyline import MainStorylinePlanner
    from ..models import GameState

logger = logging.getLogger(__name__)


class NarrativeProvider:
    """Generate or retrieve narrative text for game events.

    Strategy:
    1. If event has rich expanded_text (>50 chars), use it directly
    2. If LLM is available, expand with full context:
       - NPC interaction history with the involved NPC
       - Active story arc progress
       - Unresolved plot hooks
       - Biography + recent memories
    3. Fallback: return the raw text as-is
    """

    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        prompt_builder: Optional["PromptBuilder"] = None,
        npc_manager: Optional["NPCManager"] = None,
        memory_manager: Optional["MemoryManager"] = None,
        hook_manager: Optional["CausalityManager"] = None,
        arc_planner: Optional["StoryArcPlanner"] = None,
        storyline_planner: Optional["MainStorylinePlanner"] = None,
    ):
        self._llm = llm_client
        self._prompt_builder = prompt_builder
        self._npc_manager = npc_manager
        self._memory_manager = memory_manager
        self._hook_manager = hook_manager
        self._arc_planner = arc_planner
        self._storyline_planner = storyline_planner

    def get_event_narrative(
        self, event: dict, state: Optional["GameState"] = None
    ) -> str:
        """Return narrative text for an event, expanding if needed.

        Priority:
        1. Existing rich expanded_text (>50 chars)
        2. LLM expansion with full context
        3. Raw text fallback
        """
        # Check for existing high-quality text
        expanded = event.get("expanded_text", "")
        if expanded and len(expanded) > 50:
            return expanded

        # Try LLM expansion with full context
        if self._llm and self._llm.available and self._prompt_builder and state:
            try:
                # Build context-aware prompt
                system_prompt, user_prompt = self._build_contextual_prompt(
                    event, state
                )
                result = self._llm.generate_sync(
                    system_prompt, user_prompt,
                    max_tokens=300, temperature=0.85,
                )
                if result:
                    return result
            except Exception as e:
                logger.debug("LLM narrative expansion failed: %s", e)

        # Fallback: raw text
        return event.get("text", "")

    def get_breakthrough_narrative(
        self, event: dict, state: Optional["GameState"] = None
    ) -> str:
        """Return narrative text for a breakthrough event."""
        expanded = event.get("expanded_text", "")
        if expanded and len(expanded) > 50:
            return expanded
        # Breakthroughs are important - always try LLM
        if self._llm and self._llm.available and self._prompt_builder and state:
            try:
                system_prompt, user_prompt = self._build_contextual_prompt(
                    event, state
                )
                result = self._llm.generate_sync(
                    system_prompt, user_prompt,
                    max_tokens=400, temperature=0.8,
                )
                if result:
                    return result
            except Exception as e:
                logger.debug("LLM breakthrough narrative failed: %s", e)
        return event.get("text", "")

    def _build_contextual_prompt(self, event: dict, state: "GameState") -> tuple:
        """Build a context-aware prompt with all available narrative context."""
        # NPC interaction history (if event involves an NPC)
        npc_history = ""
        involved_npc_id = event.get("involved_npc_id", "")
        if involved_npc_id and self._npc_manager:
            npc_history = self._npc_manager.get_npc_interaction_history(
                state, involved_npc_id, max_entries=8
            )

        # NPC relationships overview
        npc_context = ""
        if self._npc_manager:
            npc_context = self._npc_manager.get_npc_context_string(state)

        # Unresolved hooks
        hooks_context = ""
        if self._hook_manager:
            hooks_context = self._hook_manager.get_hooks_context_for_ai(state)

        # Story arc context
        arc_context = ""
        if self._arc_planner:
            arc_context = self._arc_planner.get_arcs_context_for_ai(state)

        # Main storyline context (骨骼上下文)
        storyline_context = ""
        if self._storyline_planner:
            storyline_context = self._storyline_planner.get_storyline_context_for_ai(state)

        # Combine arc and storyline context
        if storyline_context:
            arc_context = (arc_context + "\n\n" + storyline_context).strip() if arc_context else storyline_context

        # Recent experiences
        recent = ""
        if state.memory_working:
            recent_items = state.memory_working[-5:]
            recent = "\n".join(
                f"- {m.get('text', '')[:50]}" for m in recent_items
            )

        # Use the full contextual prompt template
        from .foreshadowing import build_foreshadowing_context, build_emotional_tokens_context, build_repertoire_context, build_emotional_state_context
        foreshadowing = build_foreshadowing_context(state)
        emotional_tokens_ctx = build_emotional_tokens_context(state)
        repertoire_ctx = build_repertoire_context(state)
        emotional_state_ctx = build_emotional_state_context(state)

        return self._prompt_builder.build_contextual_narrative_prompt(
            event=event,
            state=state,
            npc_context=npc_context,
            npc_interaction_history=npc_history,
            arc_context=arc_context,
            hooks_context=hooks_context,
            recent_events=recent,
            foreshadowing_hints=foreshadowing,
            emotional_tokens_context=emotional_tokens_ctx,
            repertoire_context=repertoire_ctx,
            emotional_state_context=emotional_state_ctx,
        )

    def polish_narrative(
        self, raw_text: str, state: Optional["GameState"] = None
    ) -> str:
        """Polish existing text with AI (passthrough if unavailable).

        Adds atmospheric detail and emotional resonance to short texts.
        Only polishes texts shorter than 80 chars; longer texts are
        already considered rich enough.
        """
        if not raw_text or len(raw_text) >= 80:
            return raw_text

        if not (self._llm and self._llm.available and self._prompt_builder):
            return raw_text

        try:
            system_prompt = (
                "你是一位修仙小说作家，请将下面的简短叙述扩写为50-100字的生动描写。"
                "保持原意不变，增加氛围和感染力。直接输出结果，不要加引号或前缀。"
            )
            result = self._llm.generate_sync(
                system_prompt, raw_text,
                max_tokens=150, temperature=0.85,
            )
            if result and len(result.strip()) > len(raw_text):
                return result.strip()
        except Exception as e:
            logger.debug("polish_narrative failed: %s", e)

        return raw_text
