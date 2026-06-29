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

MAX_ACTIVE_SAGAS = 8
MIN_SHARED_NPCS = 1
MIN_SHARED_KEYWORDS = 1   # With shared NPC, only 1 keyword overlap needed
MIN_KEYWORDS_NO_NPC = 2   # Without shared NPC, need 2 keyword overlap
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


# ── Direction Hint Templates (100 templates, 3 narrative phases) ────────────

# 酝酿期 (Brewing): momentum < 35, saga just forming, hints are subtle/mysterious
_HINTS_BREWING = [
    "与{npc}的纠葛尚未了结，命运的齿轮仍在转动",
    "{npc}相关的因果暗线正在汇聚，一场宿命般的重逢即将到来",
    "围绕「{theme}」的故事还在延续，更大的波澜正在蕴酿",
    "多年前种下的种子正在生根发芽，{npc}的命运将再次与你交织",
    "围绕「{theme}」的长卷正徐徐展开，你不过是翻过了扉页",
    "曾经的际遇正在编织成一条更宏大的命运线索",
    "你偶尔会想起{npc}，总觉得此事并未真正了结",
    "关于「{theme}」的种种巧合令你心生警觉——这绝非偶然",
    "天道因果之中，{npc}与你的缘分似乎才刚刚开始",
    "一股若有若无的气息萦绕不去，似与「{theme}」有关",
    "修行路上的蛛丝马迹正指向同一个方向——{npc}",
    "你隐约感到，围绕「{theme}」的一切正在暗中铺排",
    "{npc}留下的痕迹比你想象中更加深远",
    "冥冥之中，「{theme}」的伏线正悄然编织",
    "几桩看似无关的事件，隐约指向同一个核心——{npc}",
    "你修行中偶然感悟，竟与「{theme}」暗合，令人不安",
    "{npc}的身影在你记忆中时隐时现，仿佛在等待什么契机",
    "一条隐秘的因果线正从「{theme}」延伸而出",
    "道途之上，{npc}的存在如同一颗悬而未落的棋子",
    "过往种种正如溪流汇聚，「{theme}」终将形成洪波",
    "你察觉到围绕{npc}的诸多事件之间存在某种关联",
    "「{theme}」相关的灵气波动越来越频繁，似在酝酿变局",
    "有些事你暂时看不清全貌，但直觉告诉你与{npc}脱不了关系",
    "命运的织锦中，「{theme}」这根线正在逐渐显露",
    "你偶然发现一些蛛丝马迹，都与{npc}有千丝万缕的联系",
    "关于「{theme}」的预感越来越强烈，仿佛暴风雨前的宁静",
    "天地间有一股无形的力量在牵引，将你与{npc}的命运拧在一起",
    "你开始注意到，「{theme}」相关的事件并非各自孤立",
    "{npc}在你的修行轨迹上留下了太多巧合，这不可能是偶然",
    "一个更大的局面正在成形，而「{theme}」不过是序章",
    "你心中隐有所感：{npc}的故事，才走到第一个转折",
    "围绕「{theme}」的因果之网正在编织，而你身处其中",
    "几段看似了结的往事，实则暗藏后手——皆与{npc}有关",
    "「{theme}」如同一粒落入平湖的石子，涟漪正在扩散",
    "你隐约觉得，与{npc}之间的这段因果，将比想象中漫长得多",
]

# 高潮期 (Climax): 35 <= momentum < 70, saga in full swing, dramatic tension
_HINTS_CLIMAX = [
    "{npc}的命运正朝不可逆的方向疾驰，你必须做出选择",
    "「{theme}」的风暴已然成形，退路已绝",
    "围绕{npc}的一切正在加速收束，大劫将至",
    "你感到「{theme}」的因果之力骤然增强，犹如弦满待发",
    "与{npc}的羁绊已深入骨髓，这场宿命之局必须有个了断",
    "「{theme}」引发的连锁反应正在蔓延，天地为之变色",
    "{npc}已站在命运的十字路口，而你无法置身事外",
    "所有围绕「{theme}」的暗线同时收紧，决战之期已近",
    "你与{npc}之间的因果纠缠已到了无法回避的地步",
    "「{theme}」的激流正将你卷入漩涡中心",
    "命运的巨轮轰然转动，{npc}的抉择将影响一切",
    "「{theme}」相关的因果正以惊人的速度聚合",
    "{npc}的处境已到生死攸关之际，你必须面对",
    "围绕「{theme}」的这盘棋正在走向终局",
    "天地灵气剧烈波动，皆因「{theme}」所引发的因果共振",
    "{npc}的命运之弦已绷到极限，断裂只在旦夕之间",
    "你无法再旁观——「{theme}」的故事正需要你亲身介入",
    "一切围绕{npc}的伏笔正在同时揭开",
    "「{theme}」的因果洪流已势不可挡，万事万物都在被卷入",
    "{npc}向你投来求助的目光——或是挑衅的眼神",
    "此刻退缩便是万劫不复，「{theme}」已不容犹豫",
    "你与{npc}的纠葛如烈火烹油，再无转圜余地",
    "「{theme}」的故事即将迎来最剧烈的转折",
    "命运之手将你和{npc}推上同一个舞台，大幕已经拉开",
    "「{theme}」引发的浩劫正在席卷而来",
    "{npc}做出了一个令所有人震惊的决定",
    "围绕「{theme}」的多股力量终于正面碰撞",
    "你感到{npc}身上的气息正在发生剧变",
    "「{theme}」的因果铁链已将你和{npc}锁死在一起",
    "这是最关键的时刻——「{theme}」的走向取决于此",
    "天地异象频现，皆指向{npc}所在的方向",
    "「{theme}」的暗流已汇成惊涛骇浪",
    "一切筹谋与伏线都在此刻汇聚——{npc}的真意终将大白",
    "你和{npc}之间悬而未决的因果，今日必须了断",
    "「{theme}」所积蓄的力量即将倾泻而出",
]

# 尾声期 (Denouement): momentum >= 70 or saga age > 120 years
_HINTS_DENOUEMENT = [
    "你与{npc}的这段因果即将走到尽头",
    "「{theme}」的篇章正在缓缓合拢",
    "尘埃将落，围绕{npc}的一切即将尘埃落定",
    "「{theme}」的故事已近终章，余韵犹在",
    "你隐约感到，与{npc}的缘分正在走向最后的句号",
    "「{theme}」的涟漪正在平息，但留下的印记永远不会消失",
    "回望这段与{npc}纠缠的岁月，你感慨万千",
    "「{theme}」的因果已近圆满，天道自有定数",
    "一段漫长的故事即将落幕，{npc}在远方似乎也感应到了",
    "「{theme}」的宏大叙事正收束为一个简洁有力的结局",
    "你与{npc}的最终一面，或许就在不远的将来",
    "围绕「{theme}」的因果即将了结——不论结果如何",
    "命运给了你与{npc}最后一个机会，去为这段故事画上句号",
    "「{theme}」的回响正在渐弱，但你知道结局已经注定",
    "岁月流转，{npc}与你的这段因果终将化为传说",
    "「{theme}」曾掀起的惊涛已化作暗涌——一切都在走向终局",
    "{npc}的故事或许即将结束，但你会记住一切",
    "「{theme}」的长卷终于翻到了最后几页",
    "你心中平静如水——与{npc}的一切纠葛，即将各归其位",
    "无论结局是悲是喜，「{theme}」都将成为你修行路上最浓重的一笔",
    "天道因果循环，你与{npc}的这一劫即将功德圆满",
    "所有关于「{theme}」的谜题只剩最后一个尚未解答",
    "{npc}的命运线与你的终将分开——或永远交织",
    "你凝望远方，知道「{theme}」的最终章就在眼前",
    "百年因果，{npc}与你的故事终于要给世间一个交代",
    "「{theme}」的余波渐平，修行路上却多了一段铭心往事",
    "你预感到，下一次与{npc}相遇便是最后一次",
    "「{theme}」的宿命即将揭开谜底",
    "这段与{npc}有关的漫长旅程，正在走向它应有的终点",
    "你心中既有释然也有不舍——「{theme}」的尾声，总是令人五味杂陈",
]

# Legacy flat list (kept for backward compat if needed elsewhere)
DIRECTION_HINT_TEMPLATES = _HINTS_BREWING + _HINTS_CLIMAX + _HINTS_DENOUEMENT

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
        Also persists omen records in state.saga_omens for foreshadowing injection.
        Returns None if no omen is appropriate this turn.
        """
        # Only trigger omen if no saga formed recently and enough arcs exist
        if len(state.completed_arcs_history) < 2:
            return None

        # Avoid omen spam: at most once every 20 years
        last_omen_age = getattr(state, '_last_omen_age', 0)
        if state.age - last_omen_age < 20:
            return None

        # Track previously used omen themes to avoid repetition
        used_omen_keys: set = getattr(state, '_used_omen_keys', set())

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

                    # Skip if this npc+theme combination was already used
                    omen_key = f"{npc}_{theme}"
                    if omen_key in used_omen_keys:
                        continue

                    template = random.choice(_OMEN_TEMPLATES)
                    state._last_omen_age = state.age
                    # Record this omen to avoid future repetition
                    used_omen_keys.add(omen_key)
                    state._used_omen_keys = used_omen_keys

                    # Persist omen record for foreshadowing system
                    omen_record = {
                        "theme": theme,
                        "involved_npcs": [n for n in [npc_a, npc_b] if n],
                        "omen_keywords": list(kw_a & kw_b),
                        "created_at_age": state.age,
                        "omen_key": omen_key,
                    }
                    # Avoid duplicate omen records
                    existing_keys = {o.get("omen_key") for o in state.saga_omens}
                    if omen_key not in existing_keys:
                        state.saga_omens.append(omen_record)
                        # Cap at 5 omens
                        if len(state.saga_omens) > 5:
                            state.saga_omens = state.saga_omens[-5:]

                    return template.format(npc=npc, theme=theme)

        return None

    @staticmethod
    def _would_form_saga(npc_overlap: bool, kw_overlap: int) -> bool:
        """Check if overlaps are strong enough to actually form a saga."""
        return (npc_overlap and kw_overlap >= MIN_SHARED_KEYWORDS) or kw_overlap >= MIN_KEYWORDS_NO_NPC + 1

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
            elif keyword_overlap >= MIN_KEYWORDS_NO_NPC + 1:
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

        # Clean up matching omens (omen → saga upgrade)
        npc_set = set(involved_npcs)
        state.saga_omens = [
            o for o in state.saga_omens
            if not (set(o.get("involved_npcs", [])) & npc_set)
        ]

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

        # Fallback: phase-based template selection
        momentum = saga.get("momentum", 0)
        created = saga.get("created_at_age", 0)
        # Determine narrative phase
        if momentum >= 70:
            pool = _HINTS_DENOUEMENT
        elif momentum >= 35:
            pool = _HINTS_CLIMAX
        else:
            pool = _HINTS_BREWING
        template = random.choice(pool)
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
        # Pre-build name→alive lookup for O(1) checks
        alive_names: set[str] = {
            npc_dict.get("name", "")
            for npc_dict in state.npc_registry.values()
            if npc_dict.get("is_alive", True)
        }

        for saga in state.sagas:
            if not saga.get("is_active"):
                continue

            # Check NPC death
            npcs = saga.get("involved_npcs", [])
            if npcs and not any(n in alive_names for n in npcs):
                saga["is_active"] = False
                logger.info("Saga completed (NPCs dead): '%s'", saga.get("theme", ""))
                continue

            # Gradual momentum decay — starts at 50 years, accelerates over time
            created = saga.get("created_at_age", 0)
            years_since = state.age - created
            if years_since > 50:
                # Decay rate: 2/turn for 50-150 years, 5/turn for 150+ years
                decay_rate = 2.0 if years_since <= 150 else 5.0
                saga["momentum"] = max(0, saga.get("momentum", 0) - decay_rate)
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
