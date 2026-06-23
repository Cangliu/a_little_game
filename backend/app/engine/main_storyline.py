"""Main Storyline System — skeleton + flesh narrative architecture.

At game start (first realm breakthrough), generates a main storyline
("destiny skeleton") that spans the entire game. Random events ("flesh")
enrich the details, and significant events can feed back to modify
the storyline ("flesh nourishes skeleton").

Three-layer interaction:
1. Skeleton → Flesh: main storyline keywords boost event selection (×3)
2. Flesh → Skeleton (advance): matching events complete destiny beats
3. Flesh → Skeleton (pivot): dramatic events rewrite future beats

Key generation trick — "Keyword Palette":
Instead of dumping all 9185 events into LLM context, we pre-scan the
event pool to extract high-frequency meaningful keywords, then provide
a random subset as a "palette" to LLM. This ensures:
- Generated keywords actually match events in the pool
- Output stays compact (<1000 chars total)
- Each beat has ≥2 keywords, total ≥10
- Randomness through palette sampling + narrative seeds
"""
from __future__ import annotations

import json
import random
import logging
import uuid
from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from ..models import GameState
    from .ai.llm_client import LLMClient
    from .ai.prompt_builder import PromptBuilder
    from .npc.npc_manager import NPCManager

logger = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────────────────

class DestinyBeat(BaseModel):
    """A single major narrative beat in the destiny storyline."""
    description: str                    # "灵根觉醒，踏入仙途"
    target_realm: int = 0               # Expected realm when this triggers
    keywords: list = []                 # Keywords for matching events
    is_completed: bool = False
    completion_age: int = 0             # Age when completed
    completion_summary: str = ""        # What event completed this
    is_modified: bool = False           # Whether flesh feedback modified this
    original_description: str = ""      # Pre-modification description


class MainStoryline(BaseModel):
    """The overarching destiny arc for a character's entire journey."""
    storyline_id: str = ""
    archetype: str = ""                 # "天命修仙" / "红尘历劫" etc.
    archetype_description: str = ""     # Brief archetype description
    destiny_beats: list = []            # [DestinyBeat dicts]
    current_beat_index: int = 0         # Progress tracker
    momentum: float = 0.0              # 0-100, how well events align
    pivots: list = []                   # Records of flesh→skeleton modifications
    created_at_age: int = 0
    is_completed: bool = False


# ── Keyword Palette ──────────────────────────────────────────────────────
# Curated keywords verified to exist in the event pool (each maps to real events).
# Organized by narrative theme for structured random sampling.

KEYWORD_PALETTE = {
    "修行": ["修炼", "闭关", "入定", "参悟", "功法", "心法", "炼化", "顿悟", "悟道"],
    "感悟": ["领悟", "感悟", "境界", "蜕变", "真谛", "大道", "道心", "天道"],
    "战斗": ["遭遇", "击败", "重伤", "逃脱", "围攻", "追杀", "切磋", "比试"],
    "社交": ["传承", "宗门", "同门", "弟子", "散修", "魔修", "守护"],
    "机缘": ["机缘", "宝物", "秘境", "遗迹", "丹药", "灵石", "探索", "法宝"],
    "劫难": ["走火", "心魔", "陨落", "生死", "天劫", "背叛", "情劫"],
    "境界": ["灵根", "觉醒", "筑基", "金丹", "元婴", "化神", "突破", "飞升", "渡劫"],
    "天地": ["天地", "法则", "本源", "灵气", "神通", "灵力", "修为"],
    "生物": ["妖兽"],
}

# Random narrative seeds — injected into LLM prompt for variety
_NARRATIVE_SEEDS = [
    "你的灵根似乎蕴含着不为人知的秘密",
    "一位神秘前辈曾在你幼年时暗中注视过你",
    "你的命运与某处远古遗迹有着千丝万缕的联系",
    "你注定要在修行路上遭遇一场改变一切的变故",
    "有一股来自上古的力量正在暗中寻找你",
    "你的道途与一位挚友的命运紧紧纠缠",
    "你终将面临一个关乎万千修士的抉择",
    "你修炼的功法中藏着一个前人未曾发现的隐秘",
    "一场席卷修仙界的浩劫将与你的命运交汇",
    "你将在一次生死危机中彻底领悟道的真谛",
    "你和某位大能之间存在着一段跨越千年的因果",
    "你的丹田内隐藏着一缕异于常人的力量",
]


# ── Archetype Templates (with beat variants for randomization) ───────────

_BEAT_VARIANTS = {
    # ── realm 1 (练气) ────────────────────────────────────────
    # 觉醒
    "awakening": [
        {"d": "灵根觉醒，踏入仙途", "kw": ["觉醒", "灵根", "修炼", "灵气"]},
        {"d": "偶感天地灵气，修行之路初启", "kw": ["灵气", "天地", "觉醒", "修炼"]},
        {"d": "一朝顿悟，从此踏上逆天之路", "kw": ["顿悟", "觉醒", "灵根", "修炼"]},
    ],
    # 初修
    "early_path": [
        {"d": "拜入宗门，习得根基功法", "kw": ["宗门", "功法", "传承", "弟子"]},
        {"d": "偶得前辈传承，修为初成", "kw": ["传承", "修为", "功法", "秘境"]},
        {"d": "闭关苦修，练气有成", "kw": ["闭关", "修炼", "入定", "灵力"]},
    ],
    # 练气历练
    "qi_trial": [
        {"d": "初次外出历练，见识修仙百态", "kw": ["遭遇", "探索", "修炼", "切磋"]},
        {"d": "独闯险地，在生死间磨砺修为", "kw": ["生死", "修为", "遭遇", "灵力"]},
        {"d": "执行宗门任务，崭露头角", "kw": ["宗门", "弟子", "修为", "比试"]},
    ],

    # ── realm 2 (筑基) ────────────────────────────────────────
    # 宗门/江湖
    "sect_life": [
        {"d": "宗门中修行日久，渐有所成", "kw": ["宗门", "修炼", "同门", "功法"]},
        {"d": "游历四方，结识各路修士", "kw": ["散修", "遭遇", "探索", "传承"]},
        {"d": "与同门切磋论道，互有胜负", "kw": ["同门", "切磋", "比试", "修为"]},
    ],
    # 筑基之路
    "foundation": [
        {"d": "筑基途中遭遇大劫，道心经受考验", "kw": ["筑基", "遭遇", "道心", "生死"]},
        {"d": "闭关感悟天地法则，筑基圆满", "kw": ["闭关", "感悟", "法则", "筑基"]},
        {"d": "探索秘境获得机缘，根基更加稳固", "kw": ["探索", "秘境", "机缘", "筑基"]},
        {"d": "历经磨难后领悟真谛，修为突飞猛进", "kw": ["领悟", "真谛", "突破", "修为"]},
    ],
    # 筑基试炼
    "foundation_test": [
        {"d": "入秘境试炼，险象环生", "kw": ["秘境", "遭遇", "生死", "突破"]},
        {"d": "宗门大比中脱颖而出", "kw": ["宗门", "比试", "击败", "修为"]},
        {"d": "遭遇瓶颈，闭关苦思终突破", "kw": ["闭关", "突破", "领悟", "修炼"]},
    ],

    # ── realm 3 (金丹) ────────────────────────────────────────
    # 机缘/秘境
    "treasure_hunt": [
        {"d": "深入遗迹，寻觅上古机缘", "kw": ["遗迹", "机缘", "探索", "宝物"]},
        {"d": "偶入秘境，获得天材地宝", "kw": ["秘境", "机缘", "宝物", "法宝"]},
        {"d": "炼制丹药以助突破", "kw": ["丹药", "炼化", "突破", "灵石"]},
    ],
    # 金丹凝结
    "golden_core": [
        {"d": "炼化天材地宝，金丹初成", "kw": ["炼化", "金丹", "丹药", "突破"]},
        {"d": "遗迹中发现上古传承，修为大进", "kw": ["遗迹", "传承", "金丹", "修为"]},
        {"d": "与强敌激战后顿悟，金丹圆满", "kw": ["遭遇", "顿悟", "金丹", "击败"]},
        {"d": "参悟大道之理，金丹之力凝实", "kw": ["参悟", "大道", "金丹", "修炼"]},
    ],
    # 劫难危机 (可插入任意境界)
    "crisis": [
        {"d": "走火入魔，在心魔中挣扎求生", "kw": ["走火", "心魔", "生死", "道心"]},
        {"d": "遭遇追杀，在绝境中寻找生机", "kw": ["追杀", "遭遇", "逃脱", "生死"]},
        {"d": "重伤之下入定参悟，化险为夷", "kw": ["重伤", "入定", "参悟", "蜕变"]},
        {"d": "至亲陨落，化悲愤为修行之力", "kw": ["陨落", "修炼", "蜕变", "道心"]},
    ],

    # ── realm 4 (元婴) ────────────────────────────────────────
    # 实力飞跃
    "power_surge": [
        {"d": "功法大成，实力今非昔比", "kw": ["功法", "修为", "突破", "神通"]},
        {"d": "击败强敌，名震一方", "kw": ["击败", "遭遇", "修为", "比试"]},
        {"d": "闭关悟道，修为精进", "kw": ["闭关", "悟道", "修炼", "境界"]},
    ],
    # 元婴显化
    "nascent_soul": [
        {"d": "元婴显化，窥得天地本源之力", "kw": ["元婴", "天地", "本源", "神通"]},
        {"d": "领悟天道法则，元婴之力浩瀚无边", "kw": ["领悟", "天道", "法则", "元婴"]},
        {"d": "悟道于天地之间，元婴大成", "kw": ["悟道", "天地", "元婴", "感悟"]},
    ],
    # 恩怨清算
    "reckoning": [
        {"d": "与宿敌终极一战，了结恩怨", "kw": ["遭遇", "击败", "生死", "修为"]},
        {"d": "旧日因果浮现，逐一清算", "kw": ["遭遇", "追杀", "道心", "蜕变"]},
        {"d": "守护至亲，不惜以命相搏", "kw": ["守护", "生死", "遭遇", "修炼"]},
    ],

    # ── realm 5 (化神/飞升) ───────────────────────────────────
    # 天劫临近
    "tribulation": [
        {"d": "天劫将至，闭关做最后准备", "kw": ["天劫", "闭关", "修炼", "渡劫"]},
        {"d": "化神之路，天地法则层层阻碍", "kw": ["化神", "法则", "天地", "突破"]},
        {"d": "感应天劫之力，心中无惧", "kw": ["天劫", "渡劫", "道心", "化神"]},
    ],
    # 飞升终局
    "ascension": [
        {"d": "渡天劫，一步登天问道飞升", "kw": ["天劫", "飞升", "渡劫", "化神"]},
        {"d": "化神圆满，万劫归一终得超脱", "kw": ["化神", "天劫", "飞升", "大道"]},
        {"d": "天地共鸣，飞升在即", "kw": ["天地", "飞升", "渡劫", "化神"]},
    ],
}

ARCHETYPE_STORYLINES = {
    "天命修仙": {
        "description": "你生来便注定了一条非凡的修仙之路，每一步都仿佛冥冥中自有天意",
        "beat_sequence": [
            "awakening", "early_path", "qi_trial",        # 练气 ×3
            "sect_life", "foundation", "foundation_test",  # 筑基 ×3
            "treasure_hunt", "golden_core",                # 金丹 ×2 (稳步上升，无危机)
            "power_surge", "nascent_soul", "reckoning",    # 元婴 ×3
            "tribulation", "ascension",                    # 化神 ×2
        ],
    },
    "红尘历劫": {
        "description": "你的修仙之路注定充满红尘纠葛，唯有历尽情劫方能证道",
        "beat_sequence": [
            "awakening", "early_path",                     # 练气 ×2
            "sect_life", "foundation", "foundation_test",  # 筑基 ×3
            "crisis", "golden_core", "treasure_hunt",      # 金丹 ×3 (危机打头)
            "nascent_soul", "reckoning", "power_surge",    # 元婴 ×3
            "tribulation", "ascension",                    # 化神 ×2
        ],
    },
    "逆天改命": {
        "description": "你本是一介废材，却偏要逆天改命走出一条前人未走之路",
        "beat_sequence": [
            "awakening", "early_path", "qi_trial",         # 练气 ×3
            "foundation", "foundation_test",               # 筑基 ×2 (仓促筑基)
            "crisis", "treasure_hunt", "golden_core",      # 金丹 ×3 (危机打头)
            "power_surge", "nascent_soul", "reckoning",    # 元婴 ×3
            "tribulation", "ascension",                    # 化神 ×2
        ],
    },
    "剑道孤峰": {
        "description": "你以剑入道，一生只求剑道极致，孤高而纯粹",
        "beat_sequence": [
            "awakening", "early_path", "qi_trial",         # 练气 ×3
            "foundation", "foundation_test",               # 筑基 ×2
            "golden_core", "treasure_hunt", "crisis",      # 金丹 ×3 (磨难收尾)
            "power_surge", "nascent_soul", "reckoning",    # 元婴 ×3
            "tribulation", "ascension",                    # 化神 ×2
        ],
    },
    "问道长生": {
        "description": "你追求的不是力量而是长生之道的真谛，修行即是求知",
        "beat_sequence": [
            "awakening", "early_path",                     # 练气 ×2
            "sect_life", "foundation", "foundation_test",  # 筑基 ×3
            "treasure_hunt", "golden_core", "crisis",      # 金丹 ×3 (晚期危机)
            "power_surge", "nascent_soul", "reckoning",    # 元婴 ×3
            "tribulation", "ascension",                    # 化神 ×2
        ],
    },
}

# Realm mapping for beat sequences
_BEAT_REALM = {
    "awakening": 1, "early_path": 1, "qi_trial": 1,
    "sect_life": 2, "foundation": 2, "foundation_test": 2,
    "treasure_hunt": 3, "golden_core": 3, "crisis": 3,
    "power_surge": 4, "nascent_soul": 4, "reckoning": 4,
    "tribulation": 5, "ascension": 5,
}

# Significant event keywords that can trigger storyline pivots
PIVOT_TRIGGER_KEYWORDS = [
    # 生死类
    "陨落", "生死", "重伤", "濒死", "牺牲", "死别",
    # 重大转折类
    "走火入魔", "大机缘", "背叛", "决裂", "反目", "绝交",
    # 命运节点类
    "传承", "拜师", "道侣", "结仇", "结义",
    # 境界突破类
    "突破", "灵根", "飞升", "渡劫",
    # 宗门变故类
    "灭门", "叛出", "逆伐", "放逐",
    # 其他戴剧性事件
    "失踪", "囚禁", "解封", "复仇", "和解", "归隐",
]


class MainStorylinePlanner:
    """Plans and manages the main destiny storyline throughout the game."""

    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        prompt_builder: Optional["PromptBuilder"] = None,
        npc_manager: Optional["NPCManager"] = None,
    ):
        self._llm = llm_client
        self._prompt_builder = prompt_builder
        self._npc_manager = npc_manager

    def generate_storyline(self, state: "GameState", realm: int = 1) -> dict:
        """Generate the main storyline at first realm breakthrough.

        Called once when the player first enters 练气 (realm 1).
        Tries LLM first, falls back to archetype templates.

        Returns: MainStoryline dict (stored in state.main_storyline)
        """
        if state.main_storyline and state.main_storyline.get("storyline_id"):
            return state.main_storyline  # Already has a storyline

        # Try LLM generation
        if self._llm and self._llm.available and self._prompt_builder:
            storyline = self._generate_with_llm(state)
            if storyline:
                state.main_storyline = storyline
                # Auto-complete beat 0 (awakening) since character already broke through
                self._auto_complete_first_beat(state)
                logger.info("Generated LLM main storyline: %s", storyline.get("archetype", "custom"))
                return storyline

        # Fallback: pick archetype based on character attributes
        storyline = self._generate_from_archetype(state)
        state.main_storyline = storyline
        # Auto-complete beat 0 (awakening) since character already broke through
        self._auto_complete_first_beat(state)
        logger.info("Generated archetype main storyline: %s", storyline.get("archetype", "?"))
        return storyline

    @staticmethod
    def _auto_complete_first_beat(state: "GameState") -> None:
        """Auto-complete beat 0 (awakening) since storyline is generated after awakening."""
        storyline = state.main_storyline
        beats = storyline.get("destiny_beats", [])
        if beats and not beats[0].get("is_completed"):
            beats[0]["is_completed"] = True
            beats[0]["completion_age"] = state.age
            beats[0]["completion_summary"] = "灵根觉醒，踏入修仙之路"
            storyline["current_beat_index"] = 1
            storyline["momentum"] = 10
            logger.debug("Auto-completed beat 0 (awakening) at age %d", state.age)

    def get_destiny_keywords(self, state: "GameState") -> list:
        """Get keywords from the current destiny beat for event selection boost.

        Returns keywords with ×3 priority (handled by caller in event_system).
        """
        storyline = state.main_storyline
        if not storyline or storyline.get("is_completed"):
            return []

        beats = storyline.get("destiny_beats", [])
        idx = storyline.get("current_beat_index", 0)

        if idx >= len(beats):
            return []

        current_beat = beats[idx]
        keywords = list(current_beat.get("keywords", []))  # COPY to avoid mutating beat

        # Also add next beat's keywords at lower priority
        if idx + 1 < len(beats):
            next_beat = beats[idx + 1]
            keywords.extend(next_beat.get("keywords", [])[:3])

        return keywords[:12]  # Limit total keywords

    def advance_destiny(self, state: "GameState", events: list) -> None:
        """Check if any events advance the main storyline beats.

        Called in _post_year_update after all events are processed.
        Handles both beat advancement and flesh→skeleton feedback.
        """
        storyline = state.main_storyline
        if not storyline or storyline.get("is_completed"):
            return

        beats = storyline.get("destiny_beats", [])
        idx = storyline.get("current_beat_index", 0)

        if idx >= len(beats):
            storyline["is_completed"] = True
            return

        current_beat = beats[idx]

        # Check each event for beat advancement
        for ev in events:
            if current_beat.get("is_completed"):
                # Move to next beat
                idx += 1
                storyline["current_beat_index"] = idx
                if idx >= len(beats):
                    storyline["is_completed"] = True
                    return
                current_beat = beats[idx]

            event_text = ev.get("text", "")
            event_tags = set(ev.get("tags", []))

            # Check keyword match
            match_score = self._calc_beat_match(event_text, event_tags, current_beat)

            if match_score >= 2:
                # Beat completed!
                current_beat["is_completed"] = True
                current_beat["completion_age"] = state.age
                current_beat["completion_summary"] = event_text[:60]
                storyline["momentum"] = min(100, storyline.get("momentum", 0) + 10)

                logger.info(
                    "Destiny beat %d completed: %s (momentum: %.0f)",
                    idx, current_beat.get("description", "?"),
                    storyline["momentum"]
                )

            # Check for flesh→skeleton pivot (regardless of beat match)
            self._check_pivot(state, ev, storyline)

    def _check_pivot(self, state: "GameState", event: dict, storyline: dict) -> None:
        """Check if a dramatic event should modify future storyline beats.

        Pivot triggers:
        - NPC death (master/lover/rival death)
        - Major status change (走火入魔, 大机缘)
        - Hook creation (creates_hook field)
        """
        event_text = event.get("text", "")
        event_tags = set(event.get("tags", []))
        involved_npc = event.get("involved_npc", "")
        creates_hook = event.get("creates_hook")

        # Detect if this is a pivot-worthy event
        is_pivot = False
        pivot_reason = ""

        # Only trigger pivots on truly dramatic events — reuse module-level PIVOT_TRIGGER_KEYWORDS
        for kw in PIVOT_TRIGGER_KEYWORDS:
            if kw in event_text:
                is_pivot = True
                pivot_reason = f"关键事件: {kw}"
                break

        # Check for hook creation
        if creates_hook:
            is_pivot = True
            hook_desc = creates_hook.get("description", "")
            pivot_reason = f"因果伏笔: {hook_desc[:20]}"

        # Check for NPC-related dramatic events
        if involved_npc and any(kw in event_text for kw in ["陨落", "离世", "永别", "背叛", "决裂"]):
            is_pivot = True
            pivot_reason = f"NPC变故: {involved_npc}"

        if not is_pivot:
            return

        # Perform pivot: modify an unfinished future beat
        beats = storyline.get("destiny_beats", [])
        idx = storyline.get("current_beat_index", 0)

        # Collect existing descriptions to prevent duplicates
        existing_descs = {b.get("description", "") for b in beats}

        # Find next unfinished beat to modify
        for i in range(idx + 1, len(beats)):
            beat = beats[i]
            if beat.get("is_completed") or beat.get("is_modified"):
                continue

            # Generate new description + keywords based on pivot
            result = self._generate_pivot_beat(beat, event_text, involved_npc, pivot_reason)
            if not result:
                continue

            new_desc, new_keywords = result

            # Skip if this description already exists (prevent duplicate beats)
            if new_desc in existing_descs:
                logger.debug("Skipping duplicate pivot desc: %s", new_desc[:20])
                continue

            # Store original and modify
            beat["original_description"] = beat.get("description", "")
            beat["is_modified"] = True
            beat["description"] = new_desc
            beat["keywords"] = new_keywords  # From KEYWORD_PALETTE, not bigrams

            # Record pivot
            pivot_record = f"{state.age}岁: {pivot_reason} → 改写命运'{beat.get('description', '')[:20]}'"
            storyline.setdefault("pivots", []).append(pivot_record)

            logger.info("Storyline pivot at age %d: %s", state.age, pivot_record)
            break  # Only modify one beat per event

    def get_storyline_context_for_ai(self, state: "GameState") -> str:
        """Build context string about main storyline for AI prompts."""
        storyline = state.main_storyline
        if not storyline or not storyline.get("storyline_id"):
            return ""

        archetype = storyline.get("archetype", "")
        desc = storyline.get("archetype_description", "")
        beats = storyline.get("destiny_beats", [])
        idx = storyline.get("current_beat_index", 0)
        momentum = storyline.get("momentum", 0)

        lines = [f"命运主线 [{archetype}]: {desc}"]
        lines.append(f"命运契合度: {momentum:.0f}/100")

        for i, beat in enumerate(beats):
            status = "✓" if beat.get("is_completed") else ("▶" if i == idx else "○")
            modified = " [已改写]" if beat.get("is_modified") else ""
            lines.append(f"  {status} {beat.get('description', '')}{modified}")

        pivots = storyline.get("pivots", [])
        if pivots:
            lines.append(f"命运转折 ({len(pivots)}次):")
            for p in pivots[-3:]:  # Show last 3 pivots
                lines.append(f"  - {p}")

        return "\n".join(lines)

    # ── Private helpers ───────────────────────────────────────────────

    @staticmethod
    def _build_keyword_palette(n: int = 30) -> list[str]:
        """Randomly sample keywords from the curated palette.

        The trick: instead of giving LLM all 9185 events, we give it
        ~30 verified keywords guaranteed to match real events.
        LLM picks from these to compose beats.
        """
        pool: list[str] = []
        for theme_words in KEYWORD_PALETTE.values():
            pool.extend(theme_words)
        pool = list(dict.fromkeys(pool))  # Deduplicate
        return random.sample(pool, min(n, len(pool)))

    def _generate_with_llm(self, state: "GameState") -> Optional[dict]:
        """Use LLM to generate a custom main storyline.

        Key trick: provide a "keyword palette" sampled from the event pool,
        so LLM generates keywords that actually match real events.
        Total output constrained to <1000 chars with ≥10 keywords.
        """
        from .ai import prompt_templates as T
        from ..models import REALM_NAMES, Realm

        realm_name = REALM_NAMES.get(Realm(state.realm), "凡人")

        # Build character context
        talents_str = ", ".join(state.talents[:5]) if state.talents else "无特殊天赋"
        attrs = state.attributes
        attr_highlights = []
        if attrs.constitution >= 5:
            attr_highlights.append("根骨出众")
        if attrs.comprehension >= 5:
            attr_highlights.append("悟性过人")
        if attrs.fortune >= 5:
            attr_highlights.append("福缘深厚")
        if attrs.willpower >= 5:
            attr_highlights.append("心性坚定")
        attr_str = "、".join(attr_highlights) if attr_highlights else "资质平平"

        npc_context = ""
        if self._npc_manager:
            npc_context = self._npc_manager.get_npc_context_string(state)

        # Build keyword palette (the core trick)
        palette = self._build_keyword_palette(30)
        palette_str = "、".join(palette)

        # Pick a random narrative seed for variety
        seed = random.choice(_NARRATIVE_SEEDS)

        system_prompt = T.MAIN_STORYLINE_SYSTEM
        user_prompt = T.MAIN_STORYLINE_USER.format(
            realm_name=realm_name,
            age=state.age,
            gender="男" if state.gender == "male" else "女",
            talents=talents_str,
            attributes=attr_str,
            biography=state.biography_summary or "初入仙途，尚无往事",
            npc_relationships=npc_context or "暂无已知人际关系",
            keyword_palette=palette_str,
            narrative_seed=seed,
        )

        response = self._llm.generate_sync(
            system_prompt, user_prompt,
            max_tokens=1200, temperature=0.85,
        )

        if not response:
            return None

        return self._parse_llm_storyline(response, state, set(palette))

    def _parse_llm_storyline(
        self, response: str, state: "GameState", palette: set[str] | None = None,
    ) -> Optional[dict]:
        """Parse LLM response into MainStoryline dict.

        Validates keywords against palette and supplements if too few.
        Enforces total description length ≤1000 chars.
        """
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start < 0 or end <= start:
                return None

            data = json.loads(response[start:end])

            archetype = data.get("archetype", "天命之路")[:8]
            description = data.get("description", "")[:80]
            raw_beats = data.get("beats", [])

            if not raw_beats or len(raw_beats) < 8:
                return None

            all_keywords: list[str] = []
            total_desc_len = len(description)
            destiny_beats = []

            for i, rb in enumerate(raw_beats[:16]):
                desc = rb.get("description", rb) if isinstance(rb, dict) else str(rb)
                desc = desc[:50]
                total_desc_len += len(desc)

                kws = rb.get("keywords", []) if isinstance(rb, dict) else []

                # Validate keywords against palette
                if palette:
                    valid_kws = [k for k in kws if k in palette]
                else:
                    valid_kws = list(kws)

                # Supplement if too few keywords
                if len(valid_kws) < 2:
                    extracted = self._extract_keywords_from_desc(desc)
                    if palette:
                        extracted = [k for k in extracted if k in palette]
                    valid_kws.extend(extracted)
                    valid_kws = list(dict.fromkeys(valid_kws))[:5]

                all_keywords.extend(valid_kws)

                beat = DestinyBeat(
                    description=desc,
                    target_realm=rb.get("target_realm", min(i + 1, 5)) if isinstance(rb, dict) else min(i + 1, 5),
                    keywords=valid_kws,
                ).model_dump()
                destiny_beats.append(beat)

            # Truncate if total description >1800 chars
            if total_desc_len > 1800:
                logger.warning("LLM storyline too long (%d chars), truncating", total_desc_len)
                destiny_beats = destiny_beats[:13]

            # Ensure ≥25 unique keywords total
            unique_keywords = list(dict.fromkeys(all_keywords))
            if len(unique_keywords) < 25 and palette:
                supplement = [k for k in palette if k not in unique_keywords]
                random.shuffle(supplement)
                for k in supplement[:25 - len(unique_keywords)]:
                    min_beat = min(destiny_beats, key=lambda b: len(b.get("keywords", [])))
                    min_beat.setdefault("keywords", []).append(k)

            storyline = MainStoryline(
                storyline_id=f"destiny_{uuid.uuid4().hex[:6]}",
                archetype=archetype,
                archetype_description=description,
                destiny_beats=destiny_beats,
                created_at_age=state.age,
            ).model_dump()

            final_kw_count = sum(len(b.get("keywords", [])) for b in destiny_beats)
            logger.info(
                "Parsed LLM storyline: %s, %d beats, %d keywords, %d chars",
                archetype, len(destiny_beats), final_kw_count, total_desc_len,
            )
            return storyline

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning("Failed to parse LLM storyline: %s", e)
            return None

    def _generate_from_archetype(self, state: "GameState") -> dict:
        """Generate storyline from archetypes with randomized beat variants.

        Uses beat_sequence + _BEAT_VARIANTS to pick random beat variants,
        ensuring every playthrough has a different flavor.
        """
        attrs = state.attributes

        weights = {
            "天命修仙": 30 + attrs.fortune * 3,
            "红尘历劫": 20 + attrs.charisma * 4,
            "逆天改命": 25 + attrs.willpower * 3,
            "剑道孤峰": 15 + attrs.constitution * 3,
            "问道长生": 20 + attrs.comprehension * 4,
        }

        archetype_name = random.choices(
            list(weights.keys()),
            weights=list(weights.values()),
            k=1
        )[0]

        template = ARCHETYPE_STORYLINES[archetype_name]

        # Use new beat_sequence format with random variants
        if "beat_sequence" in template:
            destiny_beats = []
            for seq_key in template["beat_sequence"]:
                variants = _BEAT_VARIANTS.get(seq_key, [])
                if not variants:
                    continue
                chosen = random.choice(variants)
                beat = DestinyBeat(
                    description=chosen["d"],
                    target_realm=_BEAT_REALM.get(seq_key, 1),
                    keywords=chosen["kw"],
                ).model_dump()
                destiny_beats.append(beat)
        else:
            # Legacy format fallback
            destiny_beats = []
            for beat_tmpl in template["beats"]:
                beat = DestinyBeat(
                    description=beat_tmpl["description"],
                    target_realm=beat_tmpl["target_realm"],
                    keywords=beat_tmpl["keywords"],
                ).model_dump()
                destiny_beats.append(beat)

        storyline = MainStoryline(
            storyline_id=f"destiny_{uuid.uuid4().hex[:6]}",
            archetype=archetype_name,
            archetype_description=template["description"],
            destiny_beats=destiny_beats,
            created_at_age=state.age,
        ).model_dump()

        total_kw = sum(len(b.get("keywords", [])) for b in destiny_beats)
        logger.info(
            "Generated archetype storyline [%s]: %d beats, %d keywords",
            archetype_name, len(destiny_beats), total_kw,
        )
        return storyline

    @staticmethod
    def _calc_beat_match(event_text: str, event_tags: set, beat: dict) -> int:
        """Calculate match score between an event and a destiny beat."""
        keywords = beat.get("keywords", [])
        score = 0

        for kw in keywords:
            if kw in event_text:
                score += 1

        # Tag-based bonus
        beat_desc = beat.get("description", "")
        tag_map = {
            "师父": {"master_event"}, "道侣": {"lover_event"},
            "宿敌": {"rival_event"}, "同门": {"fellow_event"},
            "突破": {"breakthrough"}, "飞升": {"ascension", "tribulation"},
            "觉醒": {"awakening"}, "劫难": {"danger"},
            "机缘": {"fortune"}, "闭关": {"meditation", "practice"},
        }
        for keyword, related_tags in tag_map.items():
            if keyword in beat_desc and (event_tags & related_tags):
                score += 1

        return score

    @staticmethod
    def _generate_pivot_beat(beat: dict, event_text: str, npc_name: str, reason: str) -> Optional[tuple[str, list[str]]]:
        """Generate a modified beat description + keywords based on a pivot event.
    
        Returns (new_description, palette_keywords) or None.
        Keywords are drawn from KEYWORD_PALETTE for guaranteed event matching.
        """
        # Pivot templates with associated palette keywords
        if "陨落" in event_text or "离世" in event_text:
            if npc_name:
                return (f"为{npc_name}了结未竟之缘，化悲痛为力量", ["陨落", "修炼", "道心", "蜕变"])
            return ("化丧亲之痛为修道之志", ["陨落", "修炼", "道心"])
    
        if "背叛" in event_text or "决裂" in event_text:
            if npc_name:
                return (f"与{npc_name}的恩怨将迎来最终清算", ["背叛", "遭遇", "生死", "追杀"])
            return ("在背叛的阴影中找到新的道路", ["背叛", "遭遇", "道心"])
    
        if "走火入魔" in event_text:
            return ("克服走火入魔后遗症，重塑道心", ["走火", "心魔", "道心", "领悟"])
    
        if "大机缘" in event_text:
            return ("凭借天降机缘，冲击更高境界", ["机缘", "突破", "修为", "境界"])
    
        if "传承" in event_text:
            if npc_name:
                return (f"继承{npc_name}的衣钵，发扬其道统", ["传承", "功法", "修炼", "领悟"])
            return ("得到传承后，走上崭新的修炼之路", ["传承", "功法", "修炼"])
    
        if "结仇" in event_text:
            if npc_name:
                return (f"与{npc_name}的仇怨日深，终将交锋", ["遭遇", "追杀", "生死", "击败"])
            return ("恩怨缠身，在冲突中砂砺前行", ["遭遇", "生死", "追杀"])
    
        if "生死" in event_text:
            return ("经历生死考验后，对修行有了更深的领悟", ["生死", "领悟", "感悟", "道心"])
    
        return None

    @staticmethod
    def _extract_keywords_from_desc(description: str) -> list:
        """Extract meaningful Chinese keywords from a beat description using jieba."""
        from .event_system import extract_keywords
        return extract_keywords(description, max_keywords=8)
