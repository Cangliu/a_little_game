"""Game context — structured character summary for AI narrative generation.

Aggregates identity, recent history, cultivation path, and world state
into a single object that can be serialized and passed to an LLM.
"""
from __future__ import annotations

from ..models import GameState, REALM_NAMES, Realm
from .life_phase import LifePhase, LifePhaseManager


class GameContext:
    """Builds and maintains a structured context summary for a character.

    This context is consumed by NarrativeProvider (and eventually an AI)
    to generate coherent, personalized narratives.
    """

    def build_summary(self, state: GameState) -> dict:
        """Return a structured summary of the character's current state."""
        return {
            "identity": {
                "gender": state.gender,
                "age": state.age,
                "realm": state.realm,
                "realm_name": REALM_NAMES.get(Realm(state.realm), "未知"),
                "phase": state.life_phase,
                "phase_name": LifePhase(state.life_phase).name,
            },
            "attributes": {
                "lifespan": state.attributes.lifespan,
                "constitution": state.attributes.constitution,
                "comprehension": state.attributes.comprehension,
                "fortune": state.attributes.fortune,
                "charisma": state.attributes.charisma,
                "willpower": state.attributes.willpower,
            },
            "personality_tags": list(state.tags),
            "recent_events": self._recent_events(state),
            "cultivation_path": self._infer_path(state),
            "narrative_tone": LifePhaseManager.get_narrative_tone(
                LifePhase(state.life_phase)
            ),
        }

    def update(self, state: GameState, year_events: list[dict]) -> None:
        """Update context after a year has passed.

        Maintains a rolling tension trend and last significant event
        for AI context window management.
        """
        if not year_events:
            return

        # Track the most dramatic event this year for future AI context
        best_event = None
        best_priority = -1
        priority_map = {"danger": 3, "important": 2, "fortune": 1}
        for ev in year_events:
            p = priority_map.get(ev.get("event_type", ""), 0)
            if p > best_priority:
                best_priority = p
                best_event = ev

        if best_event and best_priority > 0:
            state.last_significant_event = {
                "text": best_event.get("text", "")[:60],
                "age": state.age,
                "type": best_event.get("event_type", "normal"),
            }

    # ── Private helpers ──────────────────────────────────────────────

    @staticmethod
    def _recent_events(state: GameState, n: int = 5) -> list[dict]:
        """Return the last *n* events from the log."""
        return state.events_log[-n:] if state.events_log else []

    @staticmethod
    def _infer_path(state: GameState) -> str:
        """Infer cultivation path from tags."""
        tags = set(state.tags)
        if "sword_path" in tags:
            return "剑修"
        if "alchemy_path" in tags:
            return "丹修"
        if "body_refining" in tags:
            return "体修"
        if "formation_master" in tags:
            return "阵修"
        if "talisman_master" in tags:
            return "符修"
        if state.realm >= 1:
            return "散修"
        return "凡人"
