"""Event Director — unified LLM call for event selection + narration + branching.

Replaces the old multi-call approach (separate event selection, narrative expansion,
and choice generation) with a single LLM call that:
1. Chooses the best event from top-10 candidates
2. Generates immersive narrative (200-300 chars)
3. Optionally generates choice branches (if event is dramatic enough)

Falls back to weighted random pick + raw text when LLM is unavailable.
"""
from __future__ import annotations

import json
import logging
import random
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .ai.llm_client import LLMClient
    from .npc.npc_manager import NPCManager
    from .plot_hooks import PlotHookManager
    from .story_arc import StoryArcPlanner
    from .main_storyline import MainStorylinePlanner
    from ..models import GameState

from .ai.prompt_templates import EVENT_DIRECTOR_SYSTEM, EVENT_DIRECTOR_USER
from .life_phase import LifePhase, LifePhaseManager

logger = logging.getLogger(__name__)


class EventDirector:
    """Unified LLM call: choose event + narrate + optional branches.

    This is the central narrative intelligence of the game. Given a set of
    candidate events pre-filtered by the rule system, it uses a single LLM
    call to select the most narratively appropriate event, generate rich
    prose, and optionally create meaningful player choices.
    """

    def __init__(
        self,
        llm_client: "LLMClient",
        npc_manager: "NPCManager",
        hook_manager: "PlotHookManager",
        arc_planner: "StoryArcPlanner",
        storyline_planner: "MainStorylinePlanner",
    ):
        self._llm = llm_client
        self._npc_manager = npc_manager
        self._hook_manager = hook_manager
        self._arc_planner = arc_planner
        self._storyline_planner = storyline_planner

    def direct_event(self, candidates: list[dict], state: "GameState") -> dict:
        """Single LLM call to choose event, generate narrative, and optionally branch.

        Args:
            candidates: List of candidate dicts from EventSystem.select_candidates()
                        Each has: {"event": dict, "weight": float, "summary": str, "index": int}
            state: Current game state

        Returns:
            {
                "chosen_index": int,      # Index into candidates list
                "narrative": str,         # 200-300 char narrative text
                "has_choice": bool,       # Whether branches are generated
                "branches": list | None,  # Choice branches if has_choice
            }
        """
        if not candidates:
            return self._empty_result()

        # Try LLM generation
        if self._llm and self._llm.available:
            result = self._generate_via_llm(candidates, state)
            if result:
                return result

        # Fallback: weighted random + raw text
        return self._fallback(candidates, state)

    def _generate_via_llm(self, candidates: list[dict], state: "GameState") -> Optional[dict]:
        """Generate unified response via LLM."""
        try:
            system_prompt, user_prompt = self._build_director_prompt(candidates, state)
            raw = self._llm.generate_sync(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=800,
                temperature=0.85,
            )
            if not raw:
                return None

            return self._parse_response(raw, candidates, state)
        except Exception as e:
            logger.warning("EventDirector LLM call failed: %s", e)
            return None

    def _build_director_prompt(
        self, candidates: list[dict], state: "GameState"
    ) -> tuple[str, str]:
        """Build system + user prompt pair for the unified director call."""
        from ..models import REALM_NAMES, Realm

        realm_name = REALM_NAMES.get(Realm(state.realm), "未知")
        gender = "男" if state.gender == "male" else "女"

        # Narrative tone from life phase
        try:
            phase = LifePhase(state.life_phase)
            tone = LifePhaseManager.get_narrative_tone(phase)
        except (ValueError, KeyError):
            tone = "平淡叙事"

        # Build candidates text
        candidates_lines = []
        for i, cand in enumerate(candidates):
            ev = cand["event"]
            ev_type = ev.get("event_type", "normal")
            tags = ", ".join(ev.get("tags", [])[:3]) if ev.get("tags") else ""
            resolves = ev.get("resolves_hook", "")
            priority_hint = cand.get("priority_hint", "")

            # 带★标记的特殊事件排在前面，让LLM立即注意到
            prefix = f"{i + 1}."
            if priority_hint:
                prefix = f"{i + 1}. {priority_hint}"

            line = f"{prefix} {ev.get('text', '')[:80]} [{ev_type}]"
            if tags:
                line += f" 标签:{tags}"
            if resolves:
                line += f" (可解决因果:{resolves})"

            # Show effects briefly
            effects = ev.get("effects", {})
            if effects:
                parts = []
                for k, v in effects.items():
                    if k in ("cultivation", "constitution", "comprehension",
                             "fortune", "charisma", "willpower") and v:
                        sign = "+" if v > 0 else ""
                        parts.append(f"{k}{sign}{v}")
                if parts:
                    line += f" 效果:{','.join(parts[:4])}"

            candidates_lines.append(line)

        candidates_text = "\n".join(candidates_lines)

        # Sect info
        sect_info = "散修"
        if state.sect_membership:
            mem = state.sect_membership
            sects = state.sect_world.get("sects", {})
            sect = sects.get(mem.get("sect_id", ""), {})
            if sect:
                sect_info = f"{sect.get('name', '未知')}·{mem.get('rank', '弟子')}"

        # NPC relationships
        npc_str = "暂无重要人际关系"
        if self._npc_manager:
            npc_str = self._npc_manager.get_npc_context_string(state) or npc_str

        # NPC interaction history (for any NPC involved in top candidates)
        npc_history = ""
        if self._npc_manager:
            # Check if any top candidates involve an NPC
            for cand in candidates[:3]:
                npc_id = cand["event"].get("involved_npc_id", "")
                if npc_id:
                    npc_history = self._npc_manager.get_npc_interaction_history(
                        state, npc_id, max_entries=5
                    )
                    break

        # Unresolved hooks
        hooks_str = "无"
        if self._hook_manager:
            h = self._hook_manager.get_hooks_context_for_ai(state)
            if h:
                hooks_str = h

        # Arc + storyline context
        arc_context = ""
        if self._arc_planner:
            arc_context = self._arc_planner.get_arcs_context_for_ai(state) or ""
        if self._storyline_planner:
            try:
                storyline_ctx = self._storyline_planner.get_storyline_context_for_ai(state)
                if storyline_ctx:
                    arc_context = (arc_context + "\n" + storyline_ctx).strip() if arc_context else storyline_ctx
            except Exception:
                pass

        # Biography
        bio = state.biography_summary or "尚无传记"

        # Recent experiences
        recent = ""
        if state.memory_working:
            recent_items = state.memory_working[-5:]
            recent = "\n".join(f"- {m.get('text', '')[:50]}" for m in recent_items)

        attrs = state.attributes
        system_prompt = EVENT_DIRECTOR_SYSTEM.format(
            realm_name=realm_name,
            gender=gender,
        )
        user_prompt = EVENT_DIRECTOR_USER.format(
            candidates_text=candidates_text,
            realm_name=realm_name,
            age=state.age,
            gender=gender,
            constitution=attrs.constitution,
            comprehension=attrs.comprehension,
            fortune=attrs.fortune,
            charisma=attrs.charisma,
            willpower=attrs.willpower,
            sect_info=sect_info,
            tension=int(state.tension),
            narrative_tone=tone,
            npc_relationships=npc_str,
            npc_history=npc_history or "无相关交往史",
            unresolved_hooks=hooks_str,
            arc_context=arc_context or "无活跃剧情线",
            biography=bio,
            recent_events=recent or "暂无近期经历",
        )

        return system_prompt, user_prompt

    def _parse_response(self, raw: str, candidates: list[dict], state: "GameState") -> Optional[dict]:
        """Parse LLM JSON response, validate, and sanitize."""
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (fences)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    data = json.loads(text[start:end])
                except json.JSONDecodeError:
                    logger.warning("EventDirector: failed to parse JSON response")
                    return None
            else:
                return None

        # Validate chosen index
        chosen = data.get("chosen", 1)
        # LLM outputs 1-based index, convert to 0-based
        if isinstance(chosen, int):
            chosen_index = chosen - 1
        else:
            chosen_index = 0

        if chosen_index < 0 or chosen_index >= len(candidates):
            chosen_index = 0

        # Extract narrative
        narrative = data.get("narrative", "")
        if not narrative or len(narrative) < 20:
            # Use raw event text as fallback
            narrative = candidates[chosen_index]["event"].get("text", "")

        # Extract choice branches
        has_choice = bool(data.get("has_choice", False))
        branches = None
        if has_choice:
            raw_branches = data.get("branches", [])
            if raw_branches and isinstance(raw_branches, list):
                branches = self._sanitize_branches(raw_branches)
                if not branches:
                    has_choice = False

        return {
            "chosen_index": chosen_index,
            "narrative": narrative,
            "has_choice": has_choice,
            "branches": branches,
        }

    def _sanitize_branches(self, branches: list) -> Optional[list[dict]]:
        """Validate and sanitize choice branches from LLM output."""
        if not branches or len(branches) < 2:
            return None

        sanitized = []
        for b in branches[:3]:  # Max 3 branches
            if not isinstance(b, dict):
                continue
            text = b.get("text", "")
            if not text:
                continue

            # Sanitize effects
            effects = b.get("effects", {})
            clean_effects = {}
            for k, v in effects.items():
                if k == "cultivation" and isinstance(v, (int, float)):
                    clean_effects[k] = max(-30, min(50, int(v)))
                elif k in ("constitution", "comprehension", "fortune",
                           "charisma", "willpower") and isinstance(v, (int, float)):
                    clean_effects[k] = max(-3, min(3, int(v)))
                elif k == "add_tag" and isinstance(v, str):
                    clean_effects[k] = v[:20]

            branch = {
                "text": text[:20],
                "effects": clean_effects,
                "result_text": b.get("result_text", "")[:150],
                "consequence_tag": b.get("consequence_tag", "") or "",
                "consequence_desc": b.get("consequence_desc", "") or "",
            }
            sanitized.append(branch)

        return sanitized if len(sanitized) >= 2 else None

    def _fallback(self, candidates: list[dict], state: "GameState") -> dict:
        """Fallback when LLM is unavailable: weighted random pick + raw text."""
        # Weighted random selection
        total_weight = sum(c["weight"] for c in candidates)
        if total_weight <= 0:
            chosen_index = 0
        else:
            r = random.uniform(0, total_weight)
            cum = 0.0
            chosen_index = 0
            for i, c in enumerate(candidates):
                cum += c["weight"]
                if r <= cum:
                    chosen_index = i
                    break

        ev = candidates[chosen_index]["event"]
        # Use expanded_text if available, else raw text
        narrative = ev.get("expanded_text", "") or ev.get("text", "")

        return {
            "chosen_index": chosen_index,
            "narrative": narrative,
            "has_choice": False,
            "branches": None,
        }

    @staticmethod
    def _empty_result() -> dict:
        """Return empty result when no candidates available."""
        return {
            "chosen_index": 0,
            "narrative": "平静的一年，无事发生。",
            "has_choice": False,
            "branches": None,
        }
