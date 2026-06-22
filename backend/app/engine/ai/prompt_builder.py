"""Prompt builder — assembles structured prompts with hard constraints.

Injects game state, memory context, and NPC info into prompt templates
while enforcing narrative guardrails.
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from ...models import GameState, REALM_NAMES, Realm
from ..life_phase import LifePhase, LifePhaseManager
from . import prompt_templates as T

if TYPE_CHECKING:
    from ..npc.models import NPC, Relationship


class PromptBuilder:
    """Constructs prompt pairs (system, user) for various AI tasks."""

    def build_narrative_prompt(
        self,
        event: dict,
        state: GameState,
        memory_context: str = "",
        npc_context: str = "",
    ) -> tuple:
        """Build prompts for event narrative generation.

        Returns (system_prompt, user_prompt).
        """
        realm_name = REALM_NAMES.get(Realm(state.realm), "未知")
        gender = "男" if state.gender == "male" else "女"

        try:
            phase = LifePhase(state.life_phase)
            tone = LifePhaseManager.get_narrative_tone(phase)
        except (ValueError, KeyError):
            tone = "平淡叙事"

        # Build recent events summary
        recent = ""
        if state.memory_working:
            recent_items = state.memory_working[-5:]
            recent = "\n".join(
                f"- {m.get('text', '')[:50]}" for m in recent_items
            )

        system_prompt = T.NARRATIVE_SYSTEM.format(
            realm_name=realm_name,
            gender=gender,
            narrative_tone=tone,
            biography_summary=state.biography_summary or "尚无传记",
            npc_relationships=npc_context or "暂无已知人际关系",
            recent_events=recent or "暂无近期经历",
        )

        # Describe effects
        effects_desc = self._describe_effects(event)
        involved_npc = event.get("involved_npc", "无")

        user_prompt = T.NARRATIVE_USER.format(
            event_text=event.get("text", ""),
            event_type=event.get("event_type", "normal"),
            effects_description=effects_desc,
            involved_npc=involved_npc,
        )

        return system_prompt, user_prompt

    def build_compression_prompt(
        self, events: list, current_age: int = 0
    ) -> tuple:
        """Build prompts for memory compression.

        Returns (system_prompt, user_prompt).
        """
        events_text = "\n".join(
            f"({e.get('age', '?')}岁) {e.get('text', '')[:60]}"
            for e in events
        )

        system_prompt = T.COMPRESSION_SYSTEM
        user_prompt = T.COMPRESSION_USER.format(
            count=len(events),
            events_text=events_text,
        )

        return system_prompt, user_prompt

    def build_npc_interaction_prompt(
        self,
        npc_name: str,
        npc_personality: str,
        npc_realm: str,
        relationship_type: str,
        sentiment: int,
        npc_backstory: str,
        situation: str,
        state: GameState,
    ) -> tuple:
        """Build prompts for NPC interaction narrative.

        Returns (system_prompt, user_prompt).
        """
        realm_name = REALM_NAMES.get(Realm(state.realm), "未知")

        try:
            phase = LifePhase(state.life_phase)
            tone = LifePhaseManager.get_narrative_tone(phase)
        except (ValueError, KeyError):
            tone = "平淡叙事"

        system_prompt = T.NPC_INTERACTION_SYSTEM.format(
            npc_name=npc_name,
            npc_personality=npc_personality,
            npc_realm=npc_realm,
            relationship_type=relationship_type,
            sentiment=sentiment,
            npc_backstory=npc_backstory,
            narrative_tone=tone,
        )

        user_prompt = T.NPC_INTERACTION_USER.format(
            situation=situation,
            player_realm=realm_name,
            player_age=state.age,
        )

        return system_prompt, user_prompt

    def build_biography_prompt(
        self,
        state: GameState,
        recent_summary: str,
        cultivation_path: str = "散修",
    ) -> tuple:
        """Build prompts for biography update.

        Returns (system_prompt, user_prompt).
        """
        realm_name = REALM_NAMES.get(Realm(state.realm), "未知")

        system_prompt = T.BIOGRAPHY_SYSTEM
        user_prompt = T.BIOGRAPHY_USER.format(
            current_biography=state.biography_summary or "暂无传记",
            recent_summary=recent_summary,
            realm_name=realm_name,
            age=state.age,
            cultivation_path=cultivation_path,
        )

        return system_prompt, user_prompt

    def build_contextual_narrative_prompt(
        self,
        event: dict,
        state: GameState,
        npc_context: str = "",
        npc_interaction_history: str = "",
        arc_context: str = "",
        hooks_context: str = "",
        recent_events: str = "",
    ) -> tuple:
        """Build context-aware prompts for narrative expansion.

        This is the primary prompt builder for the enhanced narrative system.
        It includes full NPC history, story arc context, and plot hooks.

        Returns (system_prompt, user_prompt).
        """
        realm_name = REALM_NAMES.get(Realm(state.realm), "未知")
        gender = "男" if state.gender == "male" else "女"

        try:
            phase = LifePhase(state.life_phase)
            tone = LifePhaseManager.get_narrative_tone(phase)
        except (ValueError, KeyError):
            tone = "平淡叙事"

        system_prompt = T.CONTEXTUAL_NARRATIVE_SYSTEM.format(
            realm_name=realm_name,
            gender=gender,
            narrative_tone=tone,
            biography_summary=state.biography_summary or "尚无传记",
            npc_relationships=npc_context or "暂无已知人际关系",
            arc_context=arc_context or "无活跃剧情线",
            npc_interaction_history=npc_interaction_history or "无相关交往史",
            unresolved_hooks=hooks_context or "无未了之事",
            recent_events=recent_events or "暂无近期经历",
        )

        # Describe effects
        effects_desc = self._describe_effects(event)
        involved_npc = event.get("involved_npc", "无")

        user_prompt = T.CONTEXTUAL_NARRATIVE_USER.format(
            event_text=event.get("text", ""),
            event_type=event.get("event_type", "normal"),
            effects_description=effects_desc,
            involved_npc=involved_npc,
            player_age=state.age,
        )

        return system_prompt, user_prompt

    # ── Private helpers ───────────────────────────────────────────────

    @staticmethod
    def _describe_effects(event: dict) -> str:
        """Convert event effects dict to readable Chinese description."""
        effects = event.get("effects", {})
        if not effects:
            return "无明显效果"

        parts = []
        effect_names = {
            "cultivation": "修为",
            "lifespan": "寿元",
            "constitution": "根骨",
            "comprehension": "悟性",
            "fortune": "福缘",
            "charisma": "魅力",
            "willpower": "心性",
        }
        for key, label in effect_names.items():
            val = effects.get(key)
            if val and val != 0:
                sign = "+" if val > 0 else ""
                parts.append(f"{label}{sign}{val}")

        if effects.get("add_tag"):
            parts.append(f"获得特质[{effects['add_tag']}]")
        if effects.get("realm_up"):
            parts.append("境界提升")

        return "、".join(parts) if parts else "无明显效果"
