"""Saga Emergence System — long-term narrative threads from completed arcs.

Long storylines are not pre-planned but emerge from completed short StoryArcs.
When the system detects multiple completed arcs sharing NPCs or theme keywords,
it links them into a Saga.

Key design:
- Pure rule-based emergence detection (NPC/keyword intersection)
- Zero LLM calls
- Direction hints: template-based rules, injected into arc planning context
- Saga context injected into EventDirector prompt
"""
from __future__ import annotations

import uuid
import logging
import random
from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from ..models import GameState
    from .ai.llm_client import LLMClient

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────

MAX_ACTIVE_SAGAS = 3
MIN_SHARED_NPCS = 1
MIN_SHARED_KEYWORDS = 2
MAX_COMPLETED_ARC_HISTORY = 30  # Keep last N completed arcs for saga detection


# ── Data Model ──────────────────────────────────────────────────────────

class Saga(BaseModel):
    """A long-term narrative thread emerging from linked arcs."""
    saga_id: str
    theme: str                       # Emerged theme (inferred from shared elements)
    involved_npcs: list[str] = []    # NPC names that span the saga
    linked_arc_ids: list[str] = []   # Composing arc IDs
    momentum: float = 0.0            # 0-100, story momentum
    direction_hint: str = ""         # Next development hint (injected to arc planning)
    created_at_age: int = 0
    is_active: bool = True


# ── Direction Hint Templates ─────────────────────────────────────────────

DIRECTION_HINT_TEMPLATES = [
    "与{npc}的纠葛尚未了结，命运的齿轮仍在转动",
    "{npc}相关的因果暗线正在汇聚，一场宿命般的重逢即将到来",
    "围绕「{theme}」的故事还在延续，更大的波澜正在蕴酿",
    "多年前种下的种子正在生根发芽，{npc}的命运将再次与你交织",
    "「{theme}」的篇章远未结束，新的转折正在逼近",
    "曾经的际遇正在编织成一条更宏大的命运线索",
]

# ── Saga Omen (Pre-formation Foreshadowing) ─────────────────────────────
_OMEN_KEYWORD_THRESHOLD = 1       # keyword overlap >= N triggers omen
_OMEN_TEMPLATES = [
    "近日你总感觉心神不宁，仿佛有什么即将发生……",
    "一缕模糊的气息在识海中浮现，似与{npc}有关……",
    "你偶尔梦见「{theme}」的片段，醒来后却记不清细节。",
    "天地灵气隐有异动，与「{theme}」相关的因果正在悄然汇聚。",
    "一股熟悉的气息从远方传来，{npc}似乎正在某处……",
]


# ── SagaManager ──────────────────────────────────────────────────────────

class SagaManager:
    """Detects and manages emergent long-term narrative sagas."""

    def __init__(self, llm_client: Optional["LLMClient"] = None):
        self._llm = llm_client

    def on_arc_completed(self, state: "GameState", completed_arc: dict) -> None:
        """Called when a StoryArc completes. Checks for saga emergence.

        Args:
            state: Current game state
            completed_arc: The arc dict that just completed
        """
        # Record in completed arcs history
        arc_summary = {
            "arc_id": completed_arc.get("arc_id", ""),
            "theme": completed_arc.get("theme", ""),
            "npc_id": completed_arc.get("npc_id", ""),
            "npc_name": completed_arc.get("npc_name", ""),
            "keywords": self._extract_arc_keywords(completed_arc),
            "completed_age": state.age,
        }
        state.completed_arcs_history.append(arc_summary)

        # Trim history
        if len(state.completed_arcs_history) > MAX_COMPLETED_ARC_HISTORY:
            state.completed_arcs_history = state.completed_arcs_history[-MAX_COMPLETED_ARC_HISTORY:]

        # Check for saga emergence
        self._check_emergence(state, arc_summary)

    def check_omen(self, state: "GameState") -> Optional[str]:
        """Check if conditions are ripe for a saga omen (pre-formation foreshadowing).

        Scans completed arcs history for near-threshold patterns and returns
        an atmospheric hint text if a saga is about to form.
        Returns None if no omen is appropriate this turn.
        """
        # Only trigger omen if no saga formed recently and enough arcs exist
        if len(state.completed_arcs_history) < 2:
            return None

        # Avoid omen spam: at most once every 20 years
        last_omen_age = getattr(state, '_last_omen_age', 0)
        if state.age - last_omen_age < 20:
            return None

        # Check near-threshold patterns between recent arcs
        recent_arcs = state.completed_arcs_history[-6:]
        for i, arc_a in enumerate(recent_arcs):
            for arc_b in recent_arcs[i + 1:]:
                npc_a = arc_a.get("npc_name", "")
                npc_b = arc_b.get("npc_name", "")
                kw_a = set(arc_a.get("keywords", []))
                kw_b = set(arc_b.get("keywords", []))

                npc_overlap = bool(npc_a and npc_b and npc_a == npc_b)
                kw_overlap = len(kw_a & kw_b)

                # Near threshold but not yet saga-worthy
                if kw_overlap >= _OMEN_KEYWORD_THRESHOLD and not self._would_form_saga(npc_overlap, kw_overlap):
                    npc = npc_a or npc_b or "某人"
                    theme = "、".join(list(kw_a & kw_b)[:2]) or "命运"
                    template = random.choice(_OMEN_TEMPLATES)
                    state._last_omen_age = state.age
                    return template.format(npc=npc, theme=theme)

        return None

    @staticmethod
    def _would_form_saga(npc_overlap: bool, kw_overlap: int) -> bool:
        """Check if overlaps are strong enough to actually form a saga."""
        return (npc_overlap and kw_overlap >= MIN_SHARED_KEYWORDS) or kw_overlap >= MIN_SHARED_KEYWORDS + 1

    def _check_emergence(self, state: "GameState", new_arc: dict) -> None:
        """Check if the new completed arc can form or extend a saga."""
        new_npc = new_arc.get("npc_name", "")
        new_keywords = set(new_arc.get("keywords", []))
        new_arc_id = new_arc.get("arc_id", "")

        # First: try to extend existing active sagas
        for saga in state.sagas:
            if not saga.get("is_active"):
                continue
            saga_npcs = set(saga.get("involved_npcs", []))
            # Check NPC overlap
            if new_npc and new_npc in saga_npcs:
                # Add to existing saga
                if new_arc_id not in saga.get("linked_arc_ids", []):
                    saga["linked_arc_ids"].append(new_arc_id)
                    saga["momentum"] = min(100.0, saga.get("momentum", 0) + 20.0)
                    self._update_direction_hint(saga)
                    logger.info(
                        "Saga extended: '%s' += arc '%s' (momentum=%.0f)",
                        saga.get("theme", ""), new_arc_id, saga["momentum"]
                    )
                return

        # Second: try to form a new saga from completed arcs history
        if len(state.sagas) >= MAX_ACTIVE_SAGAS:
            return

        for old_arc in state.completed_arcs_history[:-1]:  # Exclude the new one
            if old_arc.get("arc_id") == new_arc_id:
                continue

            old_npc = old_arc.get("npc_name", "")
            old_keywords = set(old_arc.get("keywords", []))

            # Check NPC sharing
            npc_overlap = bool(new_npc and old_npc and new_npc == old_npc)
            # Check keyword sharing
            keyword_overlap = len(new_keywords & old_keywords)

            if npc_overlap and keyword_overlap >= MIN_SHARED_KEYWORDS:
                self._create_saga(state, new_arc, old_arc)
                return
            elif keyword_overlap >= MIN_SHARED_KEYWORDS + 1:
                # Strong keyword overlap even without shared NPC
                self._create_saga(state, new_arc, old_arc)
                return

    def _create_saga(self, state: "GameState", arc1: dict, arc2: dict) -> None:
        """Create a new saga from two related arcs."""
        involved_npcs = []
        for arc in (arc1, arc2):
            npc = arc.get("npc_name", "")
            if npc and npc not in involved_npcs:
                involved_npcs.append(npc)

        # Infer theme from shared keywords
        kw1 = set(arc1.get("keywords", []))
        kw2 = set(arc2.get("keywords", []))
        shared = kw1 & kw2
        theme = "、".join(list(shared)[:3]) if shared else arc1.get("theme", "命运纠葛")

        saga = Saga(
            saga_id=f"saga_{uuid.uuid4().hex[:6]}",
            theme=theme,
            involved_npcs=involved_npcs,
            linked_arc_ids=[arc1.get("arc_id", ""), arc2.get("arc_id", "")],
            momentum=30.0,
            created_at_age=state.age,
            is_active=True,
        )

        # Generate direction hint (force=True for new saga)
        saga_dict = saga.model_dump()
        self._update_direction_hint(saga_dict, force=True)
        state.sagas.append(saga_dict)

        logger.info(
            "Saga emerged: '%s' from arcs %s (NPCs: %s)",
            theme, saga_dict["linked_arc_ids"], involved_npcs
        )

    def _update_direction_hint(self, saga: dict, force: bool = False) -> None:
        """Update the saga's direction hint. LLM first, template fallback.

        Throttle: only call LLM if forced (creation) OR momentum has shifted
        by >= 20 since the last LLM-generated hint.
        """
        npcs = saga.get("involved_npcs", [])
        theme = saga.get("theme", "")
        if not theme or theme == "命运":
            theme = "命运"
        npc = npcs[0] if npcs else "某人"

        current_momentum = saga.get("momentum", 0)
        last_llm_momentum = saga.get("_last_hint_momentum", -100)
        momentum_shift = abs(current_momentum - last_llm_momentum)

        # Try LLM generation when forced or momentum shifted significantly
        if (force or momentum_shift >= 20) and self._llm and self._llm.available:
            hint = self._generate_hint_via_llm(saga)
            if hint:
                saga["direction_hint"] = hint
                saga["_last_hint_momentum"] = current_momentum
                return

        # Skip update if hint already exists and momentum hasn't shifted enough
        if not force and saga.get("direction_hint") and momentum_shift < 20:
            return

        # Fallback: template-based
        template = random.choice(DIRECTION_HINT_TEMPLATES)
        saga["direction_hint"] = template.format(npc=npc, theme=theme)

    def _generate_hint_via_llm(self, saga: dict) -> Optional[str]:
        """Generate a rich saga direction hint via LLM (~100 tokens, negligible cost)."""
        try:
            from .ai.prompt_templates import SAGA_DIRECTION_SYSTEM, SAGA_DIRECTION_USER

            npcs = ", ".join(saga.get("involved_npcs", [])) or "某人"
            user_prompt = SAGA_DIRECTION_USER.format(
                theme=saga.get("theme", "命运"),
                npcs=npcs,
                arc_count=len(saga.get("linked_arc_ids", [])),
                momentum=int(saga.get("momentum", 0)),
            )

            result = self._llm.generate_sync(
                system_prompt=SAGA_DIRECTION_SYSTEM,
                user_prompt=user_prompt,
                max_tokens=60,
                temperature=0.9,
            )

            if result and len(result.strip()) >= 5:
                return result.strip()[:50]  # Cap at 50 chars
            return None
        except Exception as e:
            logger.debug("Saga LLM hint generation failed: %s", e)
            return None

    @staticmethod
    def _extract_arc_keywords(arc: dict) -> list[str]:
        """Extract keywords from a completed arc for saga matching.

        Uses jieba segmentation to extract meaningful 2+ char Chinese words
        instead of single-character splitting.
        """
        from .event_system import extract_keywords

        keywords: list[str] = []
        theme = arc.get("theme", "")
        if theme:
            keywords.extend(extract_keywords(theme, max_keywords=5))

        # Extract from planned beats
        beats = arc.get("planned_beats", [])
        for beat in beats:
            if isinstance(beat, str):
                keywords.extend(extract_keywords(beat, max_keywords=4))

        # NPC name as keyword
        npc_name = arc.get("npc_name", "")
        if npc_name:
            keywords.append(npc_name)

        # Deduplicate and limit
        return list(set(keywords))[:15]

    def check_saga_completion(self, state: "GameState") -> None:
        """Check if any active sagas should be completed.

        A saga completes when:
        - Key NPCs are all dead
        - Related causal chains are all resolved
        - Momentum decays to 0
        """
        for saga in state.sagas:
            if not saga.get("is_active"):
                continue

            # Check NPC death
            npcs = saga.get("involved_npcs", [])
            all_npcs_dead = True
            for npc_name in npcs:
                for npc_dict in state.npc_registry.values():
                    if npc_dict.get("name") == npc_name and npc_dict.get("is_alive", True):
                        all_npcs_dead = False
                        break
                if not all_npcs_dead:
                    break

            if all_npcs_dead and npcs:
                saga["is_active"] = False
                logger.info("Saga completed (NPCs dead): '%s'", saga.get("theme", ""))
                continue

            # Decay momentum over time
            created = saga.get("created_at_age", 0)
            years_since = state.age - created
            if years_since > 200:
                saga["momentum"] = max(0, saga.get("momentum", 0) - 5.0)
                if saga["momentum"] <= 0:
                    saga["is_active"] = False
                    logger.info("Saga faded (momentum=0): '%s'", saga.get("theme", ""))

    def get_saga_context_for_ai(self, state: "GameState") -> str:
        """Build context string about active sagas for AI prompts."""
        active = [s for s in state.sagas if s.get("is_active")]
        if not active:
            return ""

        lines = []
        for saga in active[:MAX_ACTIVE_SAGAS]:
            theme = saga.get("theme", "")
            npcs = ", ".join(saga.get("involved_npcs", []))
            hint = saga.get("direction_hint", "")
            momentum = saga.get("momentum", 0)

            line = f"「{theme}」"
            if npcs:
                line += f" (涉及: {npcs})"
            if momentum >= 60:
                line += " [高潮渐近]"
            if hint:
                line += f" — {hint}"
            lines.append(line)

        return "\n".join(lines)

    def get_direction_hints(self, state: "GameState") -> list[str]:
        """Get active saga direction hints for arc planning context."""
        hints = []
        for saga in state.sagas:
            if saga.get("is_active") and saga.get("direction_hint"):
                hints.append(saga["direction_hint"])
        return hints
