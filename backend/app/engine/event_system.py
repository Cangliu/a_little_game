"""Event system — three-layer filtering pipeline.

ALL_EVENTS
  → Phase Filter    (filter by current life phase whitelist / blacklist)
  → Condition Filter (explicit conditions: age, realm, tags, gender …)
  → Weight Scoring  (realm-aware weight calculation)
  → Dedup Filter    (skip already-triggered events)
  → Random Select   (weighted random pick with category quotas)
"""
import json
import os
import re
import random
import logging
from typing import Optional

import jieba

from ..models import GameState
from .life_phase import LifePhase, LifePhaseManager
from .config import FORESHADOW_THRESHOLD

logger = logging.getLogger(__name__)

# ── Jieba custom dictionary for cultivation domain ───────────────────────
# Boost segmentation accuracy for xiuxian-specific terms
_CUSTOM_WORDS = [
    # 修行
    "修炼", "修行", "修为", "修真", "修士", "修仙", "闭关", "入定",
    "打坐", "参悟", "顿悟", "悟道", "感悟", "领悟", "炼化", "炼气",
    "功法", "心法", "秘法", "法诀", "口诀", "真诀",
    # 境界
    "灵根", "觉醒", "筑基", "金丹", "元婴", "化神", "渡劫", "飞升",
    "突破", "蜕变", "圆满", "大成", "小成", "入门", "境界",
    # 战斗
    "遭遇", "击败", "重伤", "逃脱", "围攻", "追杀", "切磋", "比试",
    "偷袭", "反噬", "走火入魔", "走火", "心魔", "天劫",
    # 社交
    "传承", "宗门", "同门", "弟子", "散修", "魔修", "邪修", "守护",
    "拜师", "道侣", "师父", "师兄", "师姐", "师弟", "师妹",
    "掌门", "长老", "真人", "前辈", "晚辈",
    # 物品/场所
    "机缘", "宝物", "秘境", "遗迹", "丹药", "灵石", "法宝", "灵宝",
    "灵芝", "灵草", "灵丹", "灵脉", "灵泉", "灵兽", "妖兽", "灵气",
    "丹炉", "洞府", "坊市", "拍卖", "令牌", "玉简",
    # 天地/大道
    "天地", "法则", "本源", "大道", "道心", "天道", "真谛",
    "灵力", "神通", "仙术", "阵法", "封印", "禁制",
    # 劫难
    "陨落", "生死", "背叛", "情劫", "天灾", "浩劫", "灾难",
    # 其他常见修仙词汇
    "御剑", "飞剑", "剑气", "剑意", "仙途", "仙路", "仙缘",
    "探险", "探索", "历练", "磨难", "考验", "挑战",
    "丰收", "庄稼", "暗河", "深渊", "禁忌", "远古",
    "还魂草", "九转还魂草",
]

# Initialize jieba with custom words (suppress jieba's own logging)
jieba.setLogLevel(logging.WARNING)
for _w in _CUSTOM_WORDS:
    jieba.add_word(_w, freq=10000)


# ── Chinese stopwords for keyword extraction ─────────────────────────────
_STOPWORDS = frozenset({
    # Pronouns & common function words
    "你", "我", "他", "她", "它", "们", "的", "了", "在", "是",
    "有", "被", "将", "把", "从", "对", "与", "和", "也", "都",
    "就", "又", "还", "这", "那", "着", "过", "到", "去", "来",
    "上", "下", "中", "里", "时", "后", "前", "间", "此",
    # Common 2-char function words
    "你的", "你在", "你与", "你和", "你被", "你将", "你从", "你对",
    "一个", "一位", "一只", "一把", "一座", "一些", "一次", "一种",
    "一场", "一阵", "一番", "一股", "一道", "一片", "一丝", "一缕",
    "之中", "之后", "之间", "之时", "之下", "之上", "之前", "之际",
    "不过", "但是", "然而", "或者", "因为", "所以", "如果", "不禁",
    "虽然", "即使", "于是", "而且", "这是", "那是", "这个",
    "突然", "竟然", "居然", "忽然", "果然", "仿佛", "似乎",
    "可以", "可能", "已经", "正在", "开始", "继续", "终于",
    "非常", "十分", "略微", "稍微", "颇为", "甚至",
    "什么", "怎么", "如何", "为何", "哪里", "哪个",
    "自己", "自身", "别人", "他人", "众人", "旁人",
    "觉得", "感到", "心中", "心想", "心生", "心里",
    "发现", "看到", "听到", "想到", "感觉",
    "其中", "其他", "其实", "因此", "所有",
})


def extract_keywords(text: str, max_keywords: int = 12) -> list[str]:
    """Extract meaningful Chinese keywords from event text using jieba.

    Uses jieba word segmentation with a cultivation-domain custom dictionary
    to produce clean, meaningful keywords. Filters stopwords and single chars.
    Prioritizes 2-char words (matching KEYWORD_PALETTE format).
    """
    # Segment with jieba
    words = jieba.lcut(text)

    seen: set[str] = set()
    two_char: list[str] = []
    multi_char: list[str] = []

    for w in words:
        w = w.strip()
        if len(w) < 2:
            continue
        # Only keep Chinese words
        if not re.match(r'^[\u4e00-\u9fff]+$', w):
            continue
        if w in seen or w in _STOPWORDS:
            continue
        seen.add(w)
        if len(w) == 2:
            two_char.append(w)
        else:
            multi_char.append(w)

    # 2-char first (matches KEYWORD_PALETTE), then 3+ char
    keywords = two_char + multi_char
    return keywords[:max_keywords]


# ── Event loading ────────────────────────────────────────────────────────
EVENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "events")
ALL_EVENTS: list[dict] = []


def load_events() -> None:
    """Load all events from the all_events.json file and pre-extract keywords."""
    global ALL_EVENTS
    path = os.path.join(EVENTS_DIR, "all_events.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            ALL_EVENTS = json.load(f)

    # Use pre-computed keywords from JSON; fallback to runtime extraction
    extracted = 0
    for ev in ALL_EVENTS:
        if ev.get("keywords"):
            ev["_keywords"] = ev["keywords"]  # Pre-computed in JSON
        else:
            ev["_keywords"] = extract_keywords(ev.get("text", ""))
            extracted += 1

    kw_count = sum(len(ev.get("_keywords", [])) for ev in ALL_EVENTS)
    print(f"[EventSystem] Loaded {len(ALL_EVENTS)} events, "
          f"{kw_count} keywords ({kw_count / max(len(ALL_EVENTS), 1):.1f} avg/event"
          f", {extracted} runtime-extracted)")


# Load on import
load_events()


# ── Utility ──────────────────────────────────────────────────────────────

def _extract_narrative_age(text: str) -> Optional[int]:
    """Extract the character age from event text (e.g. '你3岁时' -> 3)."""
    m = re.search(r'(\d+)\s*岁', text)
    if m:
        return int(m.group(1))
    return None


# ── Condition checking ───────────────────────────────────────────────────

def check_conditions(event: dict, state: GameState) -> bool:
    """Check explicit conditions on an event dict against current state.

    Unlike the old engine, we do NOT add implicit safety-net rules here.
    Phase filtering is handled separately by LifePhaseManager.is_event_allowed().
    """
    cond = event.get("conditions", {})

    # Reject events whose narrative age is already in the past
    narrative_age = _extract_narrative_age(event.get("text", ""))
    if narrative_age is not None and narrative_age < state.age:
        return False

    # Age constraints
    if cond.get("min_age") is not None and state.age < cond["min_age"]:
        return False
    if cond.get("max_age") is not None and state.age > cond["max_age"]:
        return False

    # Realm constraints
    if cond.get("min_realm") is not None and state.realm < cond["min_realm"]:
        return False
    if cond.get("max_realm") is not None and state.realm > cond["max_realm"]:
        return False

    # Cultivation
    if cond.get("min_cultivation") is not None and state.cultivation < cond["min_cultivation"]:
        return False

    # Required talents
    for talent in cond.get("required_talents", []):
        if talent not in state.talents:
            return False

    # Required tags
    for tag in cond.get("required_tags", []):
        if tag not in state.tags:
            return False

    # Excluded tags
    for tag in cond.get("excluded_tags", []):
        if tag in state.tags:
            return False

    # Gender
    req_gender = cond.get("gender")
    if req_gender and req_gender != state.gender:
        return False

    # Min attributes
    if cond.get("min_attribute"):
        for attr, min_val in cond["min_attribute"].items():
            if hasattr(state.attributes, attr) and getattr(state.attributes, attr) < min_val:
                return False

    return True


# ── Weight scoring ───────────────────────────────────────────────────────

def calc_realm_relevance(event: dict, state: GameState) -> float:
    """Compute realm-relevance weight multiplier for *event*.

    Events whose target realm range is far from the player's current realm
    get a lower weight.  This makes low-tier events gradually fade out
    instead of hard-cutting, producing smoother progression.
    """
    cond = event.get("conditions", {})
    event_min = cond.get("min_realm", 0)
    event_max = cond.get("max_realm", 5)
    target_realm = (event_min + event_max) / 2
    distance = abs(state.realm - target_realm)
    return max(0.1, 1.0 - distance * 0.25)


def _compute_weight(event: dict, state: GameState) -> float:
    """Compute final weight for a single event."""
    w = float(event.get("weight", 50))

    # Event-type modifiers (fortune / danger)
    et = event.get("event_type")
    fortune_mod = 1 + state.attributes.fortune * 0.05
    if et == "fortune":
        w *= fortune_mod
    elif et == "danger":
        w *= max(0.5, 1 - state.attributes.fortune * 0.02)

    # Realm-relevance decay
    w *= calc_realm_relevance(event, state)

    # Legacy 'adult' tag realm multiplier (kept for backward compat)
    ADULT_REALM_MULTIPLIER = {0: 0.4, 1: 7.0, 2: 3.2, 3: 1.6, 4: 0.9, 5: 0.5}
    if "adult" in event.get("tags", []):
        w *= ADULT_REALM_MULTIPLIER.get(state.realm, 1.0)

    return max(w, 0.01)  # never fully zero


# ── Event selection pipeline ─────────────────────────────────────────────

class EventSystem:
    """Three-layer event filtering pipeline."""

    def __init__(self) -> None:
        self.phase_manager = LifePhaseManager()

    def select_events(
        self,
        state: GameState,
        count: Optional[int] = None,
        hook_adjustments: Optional[dict] = None,
        arc_keywords: Optional[list] = None,
    ) -> list[dict]:
        """Select *count* events for this year, respecting phase + conditions.

        Args:
            state: Current game state
            count: Number of events to select (auto if None)
            hook_adjustments: dict of {resolves_hook_id: weight_multiplier}
                              from PlotHookManager
            arc_keywords: list of keywords from active story arcs to boost
                          matching events

        If *count* is None, it is determined by character age.
        """
        if count is None:
            if state.age <= 3:
                count = 1
            elif state.age <= 12:
                count = 2
            else:
                count = random.randint(1, 3)

        phase = LifePhase(state.life_phase)
        used_ids = set(state.used_event_ids)

        # ── Layer 1-3: Phase + Condition + Dedup ─────────────────────
        eligible: list[dict] = []
        for ev in ALL_EVENTS:
            if ev.get("category") == "death":
                continue
            if ev.get("id") in used_ids:
                continue
            if not self.phase_manager.is_event_allowed(ev, phase):
                continue
            if not check_conditions(ev, state):
                continue
            eligible.append(ev)

        if not eligible:
            return [_fallback_event()]

        # ── Layer 4: Weight scoring ──────────────────────────────────
        weighted: list[tuple[dict, float]] = [
            (ev, _compute_weight(ev, state)) for ev in eligible
        ]

        # ── Layer 5: Hook weight adjustments ──────────────────────────
        if hook_adjustments:
            weighted = [
                (ev, w * hook_adjustments.get(ev.get("resolves_hook", ""), 1.0))
                for ev, w in weighted
            ]

        # ── Layer 6: Story arc + destiny keyword boost ──────────────────
        #   Uses pre-extracted event keywords (_keywords) for precise matching,
        #   plus fallback text scan for broader coverage.
        if arc_keywords:
            arc_kw_set = set(arc_keywords)
            boosted = []
            for ev, w in weighted:
                ev_keywords = set(ev.get("_keywords", []))
                ev_tags = set(ev.get("tags", []))

                # Dimension 1: keyword-to-keyword intersection (precise)
                kw_overlap = len(arc_kw_set & ev_keywords)

                # Dimension 2: arc keywords as substring in event text (broader)
                ev_text = ev.get("text", "")
                text_hits = sum(1 for kw in arc_keywords if kw in ev_text and kw not in ev_keywords)

                # Dimension 3: tag-based relevance
                tag_score = 0
                tag_map = {
                    "修炼": {"practice", "meditation", "cultivation"},
                    "突破": {"breakthrough"},
                    "危机": {"danger", "calamity"},
                    "机缘": {"fortune", "treasure"},
                    "师父": {"master_event"},
                    "道侣": {"lover_event"},
                    "宿敌": {"rival_event"},
                    "飞升": {"ascension", "tribulation"},
                    "闭关": {"meditation", "insight"},
                    "剑": {"sword", "weapon"},
                }
                for kw in arc_keywords:
                    related_tags = tag_map.get(kw)
                    if related_tags and (ev_tags & related_tags):
                        tag_score += 1

                total_score = kw_overlap + text_hits + tag_score

                if total_score >= 3:
                    boosted.append((ev, w * 5.0))  # Strong match: ×5
                elif total_score == 2:
                    boosted.append((ev, w * 3.5))  # Good match: ×3.5
                elif total_score == 1:
                    boosted.append((ev, w * 2.5))  # Partial match: ×2.5
                else:
                    boosted.append((ev, w))
            weighted = boosted

        # ── Category quota: guarantee ≥1 cultivation event per year ──
        selected = self._quota_pick(weighted, state, count)

        # Sort by narrative age for chronological display
        selected.sort(key=lambda e: _extract_narrative_age(e.get("text", "")) or 9999)

        return selected

    # ─────────────────────────────────────────────────────────────────
    def _quota_pick(
        self,
        weighted: list[tuple[dict, float]],
        state: GameState,
        count: int,
    ) -> list[dict]:
        """Weighted random pick with optional cultivation-event quota."""
        selected: list[dict] = []

        # If cultivator, try to guarantee at least 1 cultivation event
        if state.realm >= 1 and count >= 2:
            cult_pool = [(ev, w) for ev, w in weighted if ev.get("category") == "cultivation"]
            if cult_pool:
                pick = self._weighted_pick_one(cult_pool)
                if pick:
                    selected.append(pick)
                    weighted = [(ev, w) for ev, w in weighted if ev.get("id") != pick.get("id")]
                    count -= 1

        # Fill remaining slots
        for _ in range(count):
            if not weighted:
                break
            pick = self._weighted_pick_one(weighted)
            if pick is None:
                break
            selected.append(pick)
            weighted = [(ev, w) for ev, w in weighted if ev.get("id") != pick.get("id")]

        return selected if selected else [_fallback_event()]

    @staticmethod
    def _weighted_pick_one(pool: list[tuple[dict, float]]) -> Optional[dict]:
        total = sum(w for _, w in pool)
        if total <= 0:
            return None
        r = random.uniform(0, total)
        cum = 0.0
        for ev, w in pool:
            cum += w
            if r <= cum:
                return ev
        return pool[-1][0]  # float rounding safety

    # ── Effect application ───────────────────────────────────────────

    @staticmethod
    def apply_effects(event: dict, state: GameState) -> None:
        """Apply an event's effects to game state."""
        effects = event.get("effects", {})

        if effects.get("cultivation"):
            state.cultivation += effects["cultivation"]
            if state.cultivation < 0:
                state.cultivation = 0

        # Attribute modifications
        for attr in ("lifespan", "constitution", "comprehension",
                     "fortune", "charisma", "willpower"):
            if effects.get(attr):
                old = getattr(state.attributes, attr)
                setattr(state.attributes, attr, old + effects[attr])

        # Tag management
        if effects.get("add_tag"):
            tag = effects["add_tag"]
            if tag not in state.tags:
                state.tags.append(tag)

        if effects.get("add_tags"):
            for tag in effects["add_tags"]:
                if tag not in state.tags:
                    state.tags.append(tag)

        if effects.get("remove_tag"):
            tag = effects["remove_tag"]
            if tag in state.tags:
                state.tags.remove(tag)

        # Realm up (rarely used from events, but kept for compat)
        from .config import MAX_REALM
        if effects.get("realm_up") and state.realm < MAX_REALM:
            state.realm += 1
            state.cultivation = 0


# ── Fallback event ───────────────────────────────────────────────────────

def _fallback_event() -> dict:
    return {
        "id": "nothing",
        "text": "平静的一年，无事发生。",
        "expanded_text": (
            "这一年风调雨顺，门前的桃树几乎是一夜之间就开满了。"
            "你起居如常，读书、修炼，都没出什么意外。"
            "偶尔抬头看一眼远处的山，那云彩变幻万千，"
            "仿佛有许多话要说，却又一句也说不出口。"
            "平静也是一种造化，你心中隐隐如是想。"
        ),
        "event_type": "normal",
        "category": "common",
    }
