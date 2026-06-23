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
from .config import (
    FORESHADOW_THRESHOLD,
    TENSION_HIGH_THRESHOLD, TENSION_LOW_THRESHOLD,
    TENSION_WEIGHT_HIGH, TENSION_WEIGHT_MID, TENSION_WEIGHT_LOW,
)

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
    """Compute final weight for a single event.

    Weight modifiers stack multiplicatively:
    1. event_type boost (fortune/danger/important/special)
    2. Special-tag floor (adult/calamity/combat)
    3. Realm-relevance decay
    4. Adult realm multiplier (legacy)
    5. Tension curve influence
    """
    w = float(event.get("weight", 50))

    # ── 1. Event-type modifiers ───────────────────────────────────
    et = event.get("event_type")
    fortune_mod = 1 + state.attributes.fortune * 0.05
    if et == "fortune":
        w *= fortune_mod
    elif et == "danger":
        w *= max(0.5, 1 - state.attributes.fortune * 0.02)
    elif et == "important":
        w *= 1.4  # 重要人生事件提权，确保进入候选池
    elif et == "special":
        w *= 2.0  # 稀有特殊事件大幅提权

    # ── 2. Special-tag weight floor / boost ───────────────────────
    # 确保特殊事件不会因基础weight过低而完全消失在候选池中
    tags = set(event.get("tags", []))
    if "adult" in tags and et in ("funny", "special", "fortune"):
        # 情色/浪漫事件：设置最低权重地板，不至于被weight=12埋没
        w = max(w, 20.0)
    if tags & {"calamity", "combat"} and et not in ("danger",):
        # 生死大事：已有danger加成时不重复，否则轻微提权
        w *= 1.15

    # ── 3. Realm-relevance decay ──────────────────────────────────
    w *= calc_realm_relevance(event, state)

    # ── 4. Legacy adult tag realm multiplier ──────────────────────
    ADULT_REALM_MULTIPLIER = {0: 0.4, 1: 7.0, 2: 3.2, 3: 1.6, 4: 0.9, 5: 0.5}
    if "adult" in tags:
        w *= ADULT_REALM_MULTIPLIER.get(state.realm, 1.0)

    # ── 5. Tension curve influence ────────────────────────────────
    # 高张力时压低 danger/important、提升 fortune（给玩家喘息）
    # 低张力时提升 danger/important、压低 fortune（制造冲突）
    if et in ("danger", "fortune", "important"):
        tension = state.tension
        if tension >= TENSION_HIGH_THRESHOLD:
            d_mult, f_mult = TENSION_WEIGHT_HIGH
        elif tension < TENSION_LOW_THRESHOLD:
            d_mult, f_mult = TENSION_WEIGHT_LOW
        else:
            d_mult, f_mult = TENSION_WEIGHT_MID
        w *= d_mult if et in ("danger", "important") else f_mult

    return max(w, 0.01)  # never fully zero


# ── Priority hint classification ─────────────────────────────────────────

def _classify_priority_hint(event: dict) -> str:
    """Classify an event into a priority hint category for LLM reference.

    Returns a short Chinese hint string, or empty string if normal.
    The LLM uses this to decide whether to prioritize dramatic/rare events.
    """
    et = event.get("event_type", "normal")
    tags = set(event.get("tags", []))
    category = event.get("category", "")

    # 稀有特殊事件 (event_type=special)
    if et == "special":
        return "★稀有奇遇"

    # 情色/浪漫事件
    if "adult" in tags:
        if "romance" in tags:
            return "★缘分奇遇"
        return "★红尘奇事"

    # 生死危机
    if et == "danger" and tags & {"calamity", "combat"}:
        return "★生死大劫"

    # 重大转折点
    if et == "important":
        if "cultivation_start" in tags:
            return "★修仙契机"
        return "★命运转折"

    # 大机缘
    if et == "fortune" and category == "fortune":
        if any(t in tags for t in ("treasure", "secret_realm", "discovery")):
            return "★天大机缘"

    return ""


# ── Diversity decay constants ────────────────────────────────────────────
_DIVERSITY_DECAY_FACTOR = 0.6        # 同类别每出现一次，权重衰减40%
_DIVERSITY_LOOKBACK_BASE = 5         # 基础回看窗口（低境界）
_DIVERSITY_LOOKBACK_HIGH = 10        # 高境界(>=2)回看窗口
_CATEGORY_COOLDOWN_THRESHOLD = 2     # 连续出现>=N次触发冷却
_CATEGORY_COOLDOWN_PENALTY = 0.15    # 冷却期权重乘数

# ── NPC role keyword → relation_type mapping ──────────────────────────────
# 事件文本中的角色关键词，映射到NPC关系类型
# 用于 Layer 8: text-based NPC sentiment boost
_ROLE_KEYWORD_TO_RELATION: dict[str, str] = {
    # ── 师门关系 (师父/徒弟/同门)
    "师父": "师父",
    "师尊": "师父",
    "掌门": "师父",
    "长老": "师父",
    "宗主": "师父",
    "弟子": "同门",
    "师兄": "同门",
    "师姐": "同门",
    "师弟": "同门",
    "师妹": "同门",
    "同门": "同门",
    # ── 情感关系 (道侣)
    "道侣": "道侣",
    "情人": "道侣",
    "夫人": "道侣",
    "妻子": "道侣",
    "丈夫": "道侣",
    # ── 友谊关系 (挚友)
    "挚友": "挚友",
    "好友": "挚友",
    "朋友": "挚友",
    "道友": "挚友",
    "伙伴": "挚友",
    # ── 敌对关系 (宿敌/仇人)
    "宿敌": "宿敌",
    "仇人": "仇人",
    "仇家": "仇人",
    "敌人": "宿敌",
    "对手": "宿敌",
    "魔头": "宿敌",
    "魔修": "宿敌",
    # ── 泛社交 (恩人/泛泛之交)
    "散修": "泛泛之交",
    "仙人": "恩人",
    "前辈": "恩人",
    "真人": "恩人",
}

# ── Tag vocabulary (built at load time) ───────────────────────────────────
# 事件池中所有出现过的tags，供 Layer 9 做前缀匹配，也供 prompt 注入
EVENT_TAG_VOCABULARY: set[str] = set()

# 按频率排序的top tags，供 EventDirector prompt 参考
EVENT_TAG_TOP50: list[str] = []


def _build_tag_vocabulary() -> None:
    """Build tag vocabulary from loaded events."""
    global EVENT_TAG_VOCABULARY, EVENT_TAG_TOP50
    from collections import Counter
    tag_counter: Counter = Counter()
    for ev in ALL_EVENTS:
        for t in ev.get("tags", []):
            tag_counter[t] += 1
    EVENT_TAG_VOCABULARY = set(tag_counter.keys())
    EVENT_TAG_TOP50 = [tag for tag, _ in tag_counter.most_common(50)]


# Build after events are loaded
_build_tag_vocabulary()


# ── Event selection pipeline ─────────────────────────────────────────────

class EventSystem:
    """Three-layer event filtering pipeline."""

    def __init__(self) -> None:
        self.phase_manager = LifePhaseManager()

    # ── Candidate selection for LLM Director ─────────────────────────

    def select_candidates(
        self,
        state: GameState,
        count: int = 10,
        hook_adjustments: Optional[dict] = None,
        arc_keywords: Optional[list] = None,
        era_adjustments: Optional[dict] = None,
    ) -> list[dict]:
        """Return top-N weighted candidates for LLM director to choose from.

        Unlike select_events() which does final random pick, this returns
        the highest-weight candidates sorted by weight descending, with
        metadata for LLM consumption.

        Returns: [{"event": dict, "weight": float, "summary": str, "index": int}]
        """
        phase = LifePhase(state.life_phase)
        used_ids = state.used_event_ids  # already a set

        # Layer 1-3: Phase + Condition + Dedup
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
            fb = _fallback_event()
            return [{"event": fb, "weight": 1.0, "summary": fb["text"], "index": 0}]

        # Layer 4: Weight scoring
        weighted: list[tuple[dict, float]] = [
            (ev, _compute_weight(ev, state)) for ev in eligible
        ]

        # Layer 4.5: World Era category boost (纪元类别提权)
        if era_adjustments:
            weighted = [
                (ev, w * era_adjustments.get(ev.get("category", ""), 1.0))
                for ev, w in weighted
            ]

        # Layer 5: Hook weight adjustments
        if hook_adjustments:
            weighted = [
                (ev, w * hook_adjustments.get(ev.get("resolves_hook", ""), 1.0))
                for ev, w in weighted
            ]

        # Layer 6: Story arc keyword boost
        if arc_keywords:
            arc_kw_set = set(arc_keywords)
            boosted = []
            for ev, w in weighted:
                ev_keywords = set(ev.get("_keywords", []))
                ev_tags = set(ev.get("tags", []))
                ev_text = ev.get("text", "")

                kw_overlap = len(arc_kw_set & ev_keywords)
                text_hits = sum(1 for kw in arc_keywords if kw in ev_text and kw not in ev_keywords)
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
                    boosted.append((ev, w * 5.0))
                elif total_score == 2:
                    boosted.append((ev, w * 3.5))
                elif total_score == 1:
                    boosted.append((ev, w * 2.5))
                else:
                    boosted.append((ev, w))
            weighted = boosted

        # ── Layer 7: Diversity decay (近期重复类别衰减) ──────────────
        weighted = self._apply_diversity_decay(weighted, state)

        # ── Layer 8: NPC sentiment boost (好感度驱动) ────────────────
        weighted = self._apply_npc_sentiment_boost(weighted, state)

        # ── Layer 9: Consequence tag boost (选择后果提权) ─────────────
        weighted = self._apply_consequence_boost(weighted, state)

        # ── Global weight clamp ──────────────────────────────────────
        # 9 层叠乘可能产生极端权重 (理论最大 >100万)。
        # 使用硬上限 clamp，避免某个事件独占候选池。
        _WEIGHT_CAP = 5000.0
        weighted = [(ev, min(w, _WEIGHT_CAP)) for ev, w in weighted]

        # Sort by weight descending and take top-N
        weighted.sort(key=lambda x: x[1], reverse=True)
        top = weighted[:count]

        # Build candidate list with summaries
        candidates = []
        for i, (ev, w) in enumerate(top):
            effects = ev.get("effects", {})
            effects_brief = ""
            if effects:
                parts = []
                for k, v in effects.items():
                    if k in ("cultivation", "constitution", "comprehension",
                             "fortune", "charisma", "willpower") and v:
                        sign = "+" if v > 0 else ""
                        parts.append(f"{k}{sign}{v}")
                effects_brief = ", ".join(parts[:3])

            summary = f"{ev.get('text', '')[:60]} [{ev.get('event_type', 'normal')}]"
            if effects_brief:
                summary += f" ({effects_brief})"

            # ── Priority hint: 让LLM知道哪些是特殊事件，值得优先考虑
            priority_hint = _classify_priority_hint(ev)

            candidates.append({
                "event": ev,
                "weight": w,
                "summary": summary,
                "index": i,
                "priority_hint": priority_hint,
            })

        return candidates

    # ── Layer 7: Diversity decay ─────────────────────────────────────

    def _apply_diversity_decay(
        self, weighted: list[tuple[dict, float]], state: GameState
    ) -> list[tuple[dict, float]]:
        """Penalize events whose category appeared frequently in recent history.

        近期重复出现同类别事件时，对同类别的候选降权。
        Decay factor: 0.6^n where n = count of same category in recent events.
        Realm-adaptive lookback: base=5 for realm<2, 10 for realm>=2.
        Category cooldown: if same category appeared >= 2 times consecutively,
        apply a harsh 0.15x penalty.
        """
        # Realm-adaptive lookback window
        lookback = _DIVERSITY_LOOKBACK_HIGH if state.realm >= 2 else _DIVERSITY_LOOKBACK_BASE

        # Count recent categories from memory_working + memory_short_term (supplement)
        # memory_working is capped at 5, so for high-realm we pull from short_term too
        recent_memories = list(state.memory_working or [])
        if lookback > len(recent_memories) and state.memory_short_term:
            supplement_count = lookback - len(recent_memories)
            recent_memories = state.memory_short_term[-supplement_count:] + recent_memories
        recent_memories = recent_memories[-lookback:]
        recent_categories: dict[str, int] = {}
        for mem in recent_memories:
            cat = mem.get("category", "")
            if cat:
                recent_categories[cat] = recent_categories.get(cat, 0) + 1

        # Detect consecutive category streaks for cooldown
        cooldown_cats: set[str] = set()
        if len(recent_memories) >= _CATEGORY_COOLDOWN_THRESHOLD:
            tail = [m.get("category", "") for m in recent_memories[-_CATEGORY_COOLDOWN_THRESHOLD:]]
            if tail[0] and len(set(tail)) == 1:
                cooldown_cats.add(tail[0])

        if not recent_categories:
            return weighted

        result = []
        for ev, w in weighted:
            cat = ev.get("category", "")
            if cat in cooldown_cats:
                # Harsh cooldown penalty for consecutive same-category
                result.append((ev, w * _CATEGORY_COOLDOWN_PENALTY))
            elif cat in recent_categories:
                repeat_count = recent_categories[cat]
                decay = _DIVERSITY_DECAY_FACTOR ** repeat_count
                result.append((ev, w * decay))
            else:
                result.append((ev, w))
        return result

    # ── Layer 8: NPC sentiment boost ─────────────────────────────────

    def _apply_npc_sentiment_boost(
        self, weighted: list[tuple[dict, float]], state: GameState
    ) -> list[tuple[dict, float]]:
        """Boost events involving NPCs with high player affinity.

        两种匹配方式（OR关系）：
        1. 事件有明确的 involved_npc_id 字段
        2. 事件文本中含有角色关键词（师父/道侣/师兄/长老等），
           通过 _ROLE_KEYWORD_TO_RELATION 映射到玩家的实际NPC关系

        附加机制：道侣存在时，所有 adult 标签事件获得额外提权
        (好感度联动: mult = 1.0 + (sentiment/100) × 0.8 → [1.0, 1.8])

        Sentiment: -100~100 (0=中性), multiplier: 0.7 ~ 2.5
        """
        # Build relation_type → best sentiment
        relation_sentiment: dict[str, float] = {}
        npc_sentiment_by_id: dict[str, float] = {}
        for rel in (state.relationships or []):
            if isinstance(rel, dict):
                npc_id = rel.get("npc_id", "")
                sentiment = rel.get("sentiment", 0)
                rel_type = rel.get("relation_type", "")
            else:
                npc_id = getattr(rel, "npc_id", "")
                sentiment = getattr(rel, "sentiment", 0)
                rel_type = getattr(rel, "relation_type", "")
            if npc_id:
                npc_sentiment_by_id[npc_id] = sentiment
            if rel_type:
                # Keep highest sentiment per relation type
                old = relation_sentiment.get(rel_type, -1)
                if sentiment > old:
                    relation_sentiment[rel_type] = sentiment

        if not relation_sentiment and not npc_sentiment_by_id:
            return weighted

        # ── 道侣存在时，计算 adult 事件提权倍率 ──────────────────────
        # 仅对「道侣兼容」的情色事件提权，避免无关 adult 事件被误提
        lover_adult_mult = 1.0
        lover_sentiment = relation_sentiment.get("道侣")
        if lover_sentiment is not None:
            # mult = 1.0 + (sentiment/100) × 0.8 → [1.0, 1.8]
            lover_adult_mult = 1.0 + max(0.0, lover_sentiment / 100.0) * 0.8

        result = []
        for ev, w in weighted:
            # ── 道侣 adult 关联提权：仅道侣兼容的 adult 事件获得加成
            ev_tags = set(ev.get("tags", []))
            if lover_adult_mult > 1.0 and "adult" in ev_tags:
                if self._is_lover_compatible_adult(ev, ev_tags):
                    w = w * lover_adult_mult

            # Method 1: explicit involved_npc_id
            npc_id = ev.get("involved_npc_id", "")
            if npc_id and npc_id in npc_sentiment_by_id:
                mult = self._sentiment_to_multiplier(npc_sentiment_by_id[npc_id])
                result.append((ev, w * mult))
                continue

            # Method 2: pre-annotated npc_roles field (fast, covers text+expanded_text)
            best_sentiment = None
            npc_roles = ev.get("npc_roles")
            if npc_roles:
                for role in npc_roles:
                    if role in relation_sentiment:
                        s = relation_sentiment[role]
                        if best_sentiment is None or s > best_sentiment:
                            best_sentiment = s

            # Method 3: fallback text-based keyword inference (runtime scan)
            if best_sentiment is None:
                ev_text = ev.get("text", "")
                for keyword, rel_type in _ROLE_KEYWORD_TO_RELATION.items():
                    if keyword in ev_text and rel_type in relation_sentiment:
                        s = relation_sentiment[rel_type]
                        if best_sentiment is None or s > best_sentiment:
                            best_sentiment = s

            if best_sentiment is not None:
                mult = self._sentiment_to_multiplier(best_sentiment)
                result.append((ev, w * mult))
            else:
                result.append((ev, w))
        return result

    @staticmethod
    def _sentiment_to_multiplier(sentiment: float) -> float:
        """Convert sentiment (-100 ~ 100) to weight multiplier.

        0 = neutral (×1.0), 100 = max boost (×2.5), -100 = penalty (×0.7)
        """
        normalized = sentiment / 100.0  # [-1.0, 1.0]
        if normalized >= 0:
            return 1.0 + normalized * 1.5  # [1.0, 2.5]
        else:
            return max(0.7, 1.0 + normalized * 0.3)  # [0.7, 1.0]

    # ── 道侣兼容性判断 ─────────────────────────────────────

    # 少量兆底关键词：仅用于未预打 romance 标签但明确指向玩家道侣的事件
    _LOVER_FALLBACK_KEYWORDS = (
        "你的道侣", "与道侣", "你与道侣", "道侣双修",
    )

    @staticmethod
    def _is_lover_compatible_adult(ev: dict, ev_tags: set) -> bool:
        """Determine if an adult event is contextually compatible with 道侣.

        主要依据预打的 romance 标签，关键词仅作为少量兆底。

        Compatible conditions (OR):
        1. Event has 'romance' tag (primary, pre-annotated)
        2. Event text contains unambiguous 道侣 patterns (fallback)
        """
        # Condition 1: romance tag (主要判据)
        if "romance" in ev_tags:
            return True

        # Condition 2: 兆底关键词（仅匹配明确指向玩家道侣的模式）
        ev_text = ev.get("text", "")
        for kw in EventSystem._LOVER_FALLBACK_KEYWORDS:
            if kw in ev_text:
                return True

        return False

    # ── Layer 9: Consequence tag boost ───────────────────────────────

    def _apply_consequence_boost(
        self, weighted: list[tuple[dict, float]], state: GameState
    ) -> list[tuple[dict, float]]:
        """Boost events whose tags match recent player choice consequences.
    
        玩家之前的选择产生了consequence_tag，如果候选事件的tags中包含该tag，
        则提权（体现“选择有后果”的因果感）。
    
        匹配策略（按优先级）：
        1. 精确匹配: consequence_tag 完全等于事件tag (×2.0)
        2. 前缀匹配: consequence_tag 以事件tag开头 (×1.6)
           例如 consequence_tag='combat_injury' 匹配事件tag='combat'
        3. 含有匹配: 事件tag是 consequence_tag 的子串 (×1.3)
           例如 consequence_tag='betrayal' 匹配事件tag='npc_betrayal'
        """
        # Collect active consequence tags from recent choices (last 10)
        consequence_tags: set[str] = set()
        for choice in (state.choice_history or [])[-10:]:
            tag = choice.get("consequence_tag", "")
            if tag:
                consequence_tags.add(tag)
    
        if not consequence_tags:
            return weighted
    
        result = []
        for ev, w in weighted:
            ev_tags = set(ev.get("tags", []))
            if not ev_tags:
                result.append((ev, w))
                continue
    
            boost_score = 0.0
            for ctag in consequence_tags:
                # Priority 1: Exact match
                if ctag in ev_tags:
                    boost_score += 2.0
                    continue
                # Priority 2: Prefix match (ctag starts with an event tag + separator)
                prefix_hit = any(ctag.startswith(et + "_") for et in ev_tags if len(et) >= 3)
                if prefix_hit:
                    boost_score += 1.6
                    continue
                # Priority 3: Substring match (event tag contains ctag or vice versa)
                substr_hit = any(ctag in et or et in ctag for et in ev_tags if len(et) >= 4)
                if substr_hit:
                    boost_score += 1.3
    
            if boost_score > 0:
                mult = min(1.0 + boost_score, 6.0)  # Cap at ×6
                result.append((ev, w * mult))
            else:
                result.append((ev, w))
        return result

    # ── Effect application ───────────────────────────────────────────

    # Attribute value bounds (inclusive)
    _ATTR_MIN = 0
    _ATTR_MAX = 20
    # Cultivation has no upper-bound (threshold-driven), but must not go negative
    _CULTIVATION_MIN = 0

    @staticmethod
    def apply_effects(event: dict, state: GameState) -> None:
        """Apply an event's effects to game state."""
        effects = event.get("effects", {})

        if effects.get("cultivation"):
            state.cultivation = max(
                EventSystem._CULTIVATION_MIN,
                state.cultivation + effects["cultivation"],
            )

        # Attribute modifications (clamped to [0, 20])
        for attr in ("lifespan", "constitution", "comprehension",
                     "fortune", "charisma", "willpower"):
            if effects.get(attr):
                old = getattr(state.attributes, attr)
                clamped = max(EventSystem._ATTR_MIN,
                              min(EventSystem._ATTR_MAX, old + effects[attr]))
                setattr(state.attributes, attr, clamped)

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


def find_event_by_id(event_id: str) -> Optional[dict]:
    """Find an event by ID from the loaded event pool. Returns a copy."""
    for ev in ALL_EVENTS:
        if ev.get("id") == event_id:
            return dict(ev)  # Shallow copy to avoid mutation
    return None
