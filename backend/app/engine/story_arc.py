"""Story Arc Planner — LLM-driven narrative arc generation.

At key moments (realm breakthroughs), the planner asks the LLM to
generate 2-3 narrative arcs for the upcoming period. These arcs
influence event selection and provide thematic coherence.

Falls back gracefully when LLM is unavailable: uses pre-defined
archetype arcs based on realm and existing NPC relationships.
"""
from __future__ import annotations

import json
import re
import random
import logging
import uuid
from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from ..models import GameState
    from .ai.llm_client import LLMClient
    from .ai.prompt_builder import PromptBuilder
    from .npc.npc_manager import NPCManager

logger = logging.getLogger(__name__)


class StoryArc(BaseModel):
    """A narrative arc spanning part of the player's journey."""
    arc_id: str
    theme: str                          # "师徒情仇" / "道侣生死" / "问道之路"
    npc_id: str = ""                    # Primary NPC involved (if any)
    npc_name: str = ""                  # NPC name for display
    phase: str = "setup"                # "setup" / "rising" / "climax" / "resolution"
    planned_beats: list = []            # Narrative beats (strings)
    current_beat_index: int = 0         # Progress tracker
    created_at_realm: int = 0           # Realm when arc was created
    is_completed: bool = False


# ── Archetype arcs (fallback when LLM unavailable) ──────────────────────────

ARCHETYPE_ARCS = {
    1: [  # 练气
        {
            "theme": "初入仙途",
            "beats": ["感受灵气运转之妙", "修炼初见成效", "首次遭遇修炼瓶颈", "突破自我认知"],
        },
        {
            "theme": "师徒之谊",
            "npc_slot": "master",
            "beats": ["师父初授心法", "在师父指导下历练", "师父留下考验", "独立完成师父托付"],
        },
    ],
    2: [  # 筑基
        {
            "theme": "根基之路",
            "beats": ["寻找筑基之物", "灵根淬炼之痛", "根基渐稳", "感悟天地灵气本源"],
        },
        {
            "theme": "同门情谊",
            "npc_slot": "fellow",
            "beats": ["与同门切磋论道", "共同执行宗门任务", "同门陷入危机", "携手化险为夷"],
        },
    ],
    3: [  # 金丹
        {
            "theme": "问道金丹",
            "beats": ["金丹初成之感", "以金丹之力探索禁地", "遭遇金丹期强敌", "金丹圆满之悟"],
        },
        {
            "theme": "宿敌恩怨",
            "npc_slot": "rival",
            "beats": ["宿敌挑衅", "暗中较量", "正面对决", "恩怨了结或延续"],
        },
    ],
    4: [  # 元婴
        {
            "theme": "元婴蜕变",
            "beats": ["元婴初成天地共鸣", "探索元婴之秘", "元婴与天道感应", "窥见化神之路"],
        },
        {
            "theme": "道侣之缘",
            "npc_slot": "lover",
            "beats": ["与道侣并肩修炼", "道侣面临劫难", "生死与共", "双修圆满"],
        },
    ],
    5: [  # 化神
        {
            "theme": "天道之问",
            "beats": ["触碰天道壁障", "寻找飞升线索", "天劫预兆", "直面天劫"],
        },
        {
            "theme": "故人因果",
            "npc_slot": "any_known",
            "beats": ["故人重现", "往事重提", "了结因果", "释然前行"],
        },
    ],
}


class StoryArcPlanner:
    """Plans and manages narrative arcs throughout the game."""

    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        prompt_builder: Optional["PromptBuilder"] = None,
        npc_manager: Optional["NPCManager"] = None,
    ):
        self._llm = llm_client
        self._prompt_builder = prompt_builder
        self._npc_manager = npc_manager

    def plan_arcs_for_realm(self, state: "GameState", new_realm: int) -> list:
        """Generate story arcs when player enters a new realm.

        Tries LLM first, falls back to archetype arcs.
        Returns list of StoryArc dicts.
        Max 5 active arcs to prevent unbounded growth.
        """
        # Remove completed arcs
        state.active_arcs = [
            arc for arc in state.active_arcs
            if not arc.get("is_completed", False)
        ]

        # Don't stack too many arcs (hard cap: 5)
        if len(state.active_arcs) >= 5:
            return state.active_arcs

        # Try LLM planning
        if self._llm and self._prompt_builder:
            arcs = self._plan_with_llm(state, new_realm)
            if arcs:
                state.active_arcs.extend(arcs)
                state.active_arcs = state.active_arcs[:5]  # Enforce cap
                return state.active_arcs

        # Fallback: archetype arcs
        arcs = self._plan_with_archetypes(state, new_realm)
        state.active_arcs.extend(arcs)
        state.active_arcs = state.active_arcs[:5]  # Enforce cap
        return state.active_arcs

    def advance_arc_beat(self, state: "GameState", event: dict) -> Optional[dict]:
        """Check if an event advances any active story arc.

        Matches event text/tags against current arc beats to
        progress the narrative.

        Returns: The arc dict if it just completed, else None.
        """
        if not state.active_arcs:
            return None

        event_text = event.get("text", "")
        event_tags = set(event.get("tags", []))
        event_category = event.get("category", "")
        event_npc = event.get("involved_npc", "")
        completed_arc = None

        for arc in state.active_arcs:
            if arc.get("is_completed"):
                continue

            beats = arc.get("planned_beats", [])
            idx = arc.get("current_beat_index", 0)

            if idx >= len(beats):
                arc["is_completed"] = True
                arc["phase"] = "resolution"
                completed_arc = arc
                continue

            current_beat = beats[idx] if idx < len(beats) else ""
            arc_npc = arc.get("npc_name", "")

            # Check if event matches current beat
            phase = arc.get("phase", "setup")
            threshold = 4 if phase == "climax" else 3
            if self._event_matches_beat(event_text, event_tags, event_category, current_beat, event_npc, arc_npc, threshold=threshold):
                arc["current_beat_index"] = idx + 1

                # Update phase based on progress
                progress = (idx + 1) / len(beats)
                if progress < 0.3:
                    arc["phase"] = "setup"
                elif progress < 0.7:
                    arc["phase"] = "rising"
                elif progress < 1.0:
                    arc["phase"] = "climax"
                else:
                    arc["phase"] = "resolution"
                    arc["is_completed"] = True
                    completed_arc = arc

                logger.debug(
                    "Arc '%s' advanced to beat %d/%d (phase: %s)",
                    arc.get("theme", "?"), idx + 1, len(beats), arc["phase"]
                )

        return completed_arc

    def get_arcs_context_for_ai(self, state: "GameState") -> str:
        """Build context string about active arcs for AI prompts."""
        if not state.active_arcs:
            return ""
        active = [a for a in state.active_arcs if not a.get("is_completed")]
        if not active:
            return ""

        lines = ["当前剧情线:"]
        for arc in active:
            theme = arc.get("theme", "")
            phase = arc.get("phase", "setup")
            phase_names = {"setup": "铺垫", "rising": "发展", "climax": "高潮", "resolution": "收束"}
            npc_name = arc.get("npc_name", "")
            beats = arc.get("planned_beats", [])
            idx = arc.get("current_beat_index", 0)

            line = f"  - {theme} [{phase_names.get(phase, phase)}]"
            if npc_name:
                line += f" (关联: {npc_name})"
            if idx < len(beats):
                line += f" 当前: {beats[idx]}"
            lines.append(line)

        return "\n".join(lines)

    # ── Private helpers ───────────────────────────────────────────────

    def _plan_with_llm(self, state: "GameState", realm: int) -> list:
        """Use LLM to generate story arcs."""
        try:
            from .ai import prompt_templates as T

            npc_context = ""
            if self._npc_manager:
                npc_context = self._npc_manager.get_npc_context_string(state)

            hooks_desc = ""
            for hook in state.plot_hooks:
                if not hook.get("is_resolved"):
                    hooks_desc += f"- {hook.get('description', '')} ({hook.get('npc_name', '无关联NPC')})\n"

            from ..models import REALM_NAMES, Realm
            realm_name = REALM_NAMES.get(Realm(realm), "未知")

            system_prompt = T.ARC_PLANNING_SYSTEM
            user_prompt = T.ARC_PLANNING_USER.format(
                realm_name=realm_name,
                realm=realm,
                age=state.age,
                biography=state.biography_summary or "尚无传记",
                npc_relationships=npc_context,
                unresolved_hooks=hooks_desc or "无",
            )

            response = self._llm.generate_sync(
                system_prompt, user_prompt,
                max_tokens=500, temperature=0.9,
            )

            if not response:
                return []

            return self._parse_llm_arcs(response, state, realm)
        except Exception as e:
            logger.warning("StoryArcPlanner LLM planning failed: %s", e)
            return []

    def _parse_llm_arcs(self, response: str, state: "GameState", realm: int) -> list:
        """Parse LLM response into StoryArc list."""
        try:
            # Try to extract JSON
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
            else:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    obj = json.loads(response[start:end])
                    data = obj.get("arcs", [obj])
                else:
                    return []

            arcs = []
            for item in data[:3]:  # Max 3 arcs
                arc = StoryArc(
                    arc_id=f"arc_{uuid.uuid4().hex[:6]}",
                    theme=item.get("theme", "未知"),
                    npc_name=item.get("npc", ""),
                    planned_beats=item.get("beats", [])[:5],
                    created_at_realm=realm,
                ).model_dump()
                arcs.append(arc)

            return arcs

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning("Failed to parse LLM arc response: %s", e)
            return []

    def _plan_with_archetypes(self, state: "GameState", realm: int) -> list:
        """Generate arcs from predefined archetypes (no LLM needed)."""
        templates = ARCHETYPE_ARCS.get(realm, [])
        if not templates:
            return []

        # Pick 1-2 arcs
        picks = random.sample(templates, min(2, len(templates)))
        arcs = []

        for tmpl in picks:
            npc_name = ""
            npc_id = ""

            # Try to bind NPC from slot
            slot = tmpl.get("npc_slot")
            if slot and self._npc_manager:
                from .npc.models import NPC
                for rel in state.relationships:
                    rel_type_match = {
                        "master": "师父",
                        "fellow": "同门",
                        "rival": "宿敌",
                        "lover": "道侣",
                    }
                    expected_type = rel_type_match.get(slot, "")
                    if expected_type and rel.get("relation_type") == expected_type:
                        npc_dict = state.npc_registry.get(rel.get("npc_id", ""))
                        if npc_dict and npc_dict.get("is_alive", True):
                            npc_name = npc_dict.get("name", "")
                            npc_id = rel.get("npc_id", "")
                            break

            arc = StoryArc(
                arc_id=f"arc_{uuid.uuid4().hex[:6]}",
                theme=tmpl["theme"],
                npc_id=npc_id,
                npc_name=npc_name,
                planned_beats=tmpl.get("beats", []),
                created_at_realm=realm,
            ).model_dump()
            arcs.append(arc)

        return arcs

    @staticmethod
    def _event_matches_beat(
        event_text: str,
        event_tags: set,
        event_category: str,
        beat_text: str,
        event_npc: str = "",
        arc_npc: str = "",
        threshold: int = 3,
    ) -> bool:
        """Check if an event roughly matches a story beat.

        Multi-dimensional matching:
        1. Keyword overlap (2-4 char Chinese terms extracted from beat)
        2. Tag-based matching (beat keywords found in event tags)
        3. NPC binding bonus (arc NPC matches event NPC)
        4. Category-based matching

        threshold: minimum score to count as match (default 3, climax uses 4)
        """
        if not beat_text:
            return False

        score = 0

        # --- Dimension 1: Keyword extraction and matching ---
        # Use jieba segmentation (same pipeline as event keyword extraction)
        from .event_system import extract_keywords
        beat_keywords = set(extract_keywords(beat_text, max_keywords=8))

        # Count keyword matches in event text
        for kw in beat_keywords:
            if kw in event_text:
                score += 1

        # --- Dimension 2: Tag matching ---
        # Check if beat keywords appear in event tags
        tag_str = ' '.join(event_tags)
        beat_tag_keywords = {
            '师父': {'master_event', 'master'},
            '同门': {'fellow_event', 'fellow'},
            '宿敌': {'rival_event', 'rival'},
            '道侣': {'lover_event', 'lover'},
            '突破': {'breakthrough'},
            '传承': {'master_event', 'inheritance'},
            '历练': {'adventure', 'combat'},
            '切磋': {'fellow_event', 'sparring'},
            '重逢': {'reunion_event'},
            '炼丹': {'alchemy'},
            '剑': {'sword_path', 'combat'},
            '闭关': {'meditation', 'practice'},
            '秘境': {'adventure', 'exploration'},
            '劫难': {'danger', 'tribulation'},
            '飞升': {'ascension', 'tribulation'},
        }
        for keyword, related_tags in beat_tag_keywords.items():
            if keyword in beat_text and (event_tags & related_tags):
                score += 2  # Tag match is a strong signal

        # --- Dimension 3: NPC binding bonus ---
        if arc_npc and event_npc and arc_npc == event_npc:
            score += 2  # Same NPC involved = very likely related

        # --- Dimension 4: Category relevance ---
        category_keywords = {
            'cultivation': ['修炼', '突破', '功法', '心法', '修为', '闭关', '感悟'],
            'social': ['师父', '同门', '道侣', '宿敌', '重逢', '结交'],
            'fortune': ['机缘', '奇遇', '宝物', '传承', '秘境'],
            'calamity': ['劫难', '走火入魔', '危机', '生死'],
        }
        related_cats = category_keywords.get(event_category, [])
        for kw in related_cats:
            if kw in beat_text:
                score += 1
                break

        # Threshold: score >= threshold required (need multiple signals to advance arc)
        return score >= threshold
