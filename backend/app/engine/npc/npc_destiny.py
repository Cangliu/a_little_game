"""NPC Destiny System — independent NPC storylines.

Gives key NPCs (master, lover, rival) an independent destiny arc
with variable narrative beats (master=7, lover/rival=9) that trigger
based on time, relationship, tension, and probability conditions.
"""
from __future__ import annotations

# Beat count configuration by relation type
BEAT_COUNT_BY_RELATION: dict[str, int] = {
    "师父": 7,
    "道侣": 9,
    "宿敌": 9,
}
DEFAULT_BEAT_COUNT = 5

# ── Master destiny (师父命运线 — 7拍) ──────────────────────────────────

MASTER_DESTINY = [
    {
        "description": "师父传授核心功法",
        "trigger": {"min_years_since_met": 3, "probability": 0.5},
        "effects": {"cultivation": 80, "comprehension": 2},
        "event_type": "fortune",
        "text_template": "{name}将你唤至密室，郑重取出一卷泛黄功法秘籍传授于你。",
        "expanded_template": (
            "师父{name}的表情前所未有的严肃。这卷功法上的字迹苍劲有力，"
            "每一笔都蕴含着浩然灵气。你接过秘籍，双手微微颤抖——你知道"
            "这意味着什么。师父将最珍贵的东西托付给了你。"
        ),
    },
    {
        "description": "师父放手历练",
        "trigger": {"min_years_since_met": 10, "probability": 0.4},
        "effects": {"willpower": 1, "comprehension": 1, "cultivation": 30},
        "event_type": "important",
        "text_template": "{name}将你逐出门墙，令你独自行走江湖历练心性。",
        "expanded_template": (
            "「修行到了你这一步，为师已无多少可教。」{name}递来一枚玉简，"
            "「去吧，红尘中走一遭。什么时候悟透了，再回来。」你背起行囊，"
            "踏上了独自行走的路。"
        ),
    },
    {
        "description": "师父闭死关",
        "trigger": {"min_years_since_met": 20, "probability": 0.3},
        "effects": {"willpower": 2, "cultivation": 30},
        "event_type": "important",
        "text_template": "{name}宣布闭死关，你从此失去了师父的指导。",
        "expanded_template": (
            "{name}在洞府门口对你说了最后一句话：「为师此去，不破不回。"
            "你要学会独立行走了。」沉重的石门缓缓关闭，你站在门外良久，"
            "终于转身离去。从此，修行之路上只有你自己。"
        ),
    },
    {
        "description": "师父旧敌找上门",
        "trigger": {"min_years_since_met": 30, "min_tension": 30, "probability": 0.4},
        "effects": {"constitution": -1, "willpower": 2, "cultivation": 50},
        "event_type": "danger",
        "text_template": "一位神秘强者声称是{name}的旧敌，找你清算恩怨。",
        "expanded_template": (
            "那人的气势如山岳般压来，你几乎无法呼吸。「你是{name}的弟子？"
            "很好，师父的债，徒弟来还。」你咬牙站稳，拔剑相向——不论师父"
            "在不在，你都不会丢他的脸。"
        ),
    },
    {
        "description": "师父突破或陨落",
        "trigger": {"min_years_since_met": 40, "probability": 0.35},
        "effects": {"willpower": 3, "cultivation": 100},
        "event_type": "important",
        "text_template": "{name}的死关终于有了结果——{outcome}。",
        "expanded_template": "",  # Generated dynamically based on outcome
    },
    {
        "description": "师父出关相见",
        "trigger": {"min_years_since_met": 55, "probability": 0.35},
        "effects": {"comprehension": 2, "cultivation": 60},
        "event_type": "fortune",
        "text_template": "{name}破关而出，师徒二人时隔数十年再次相见。",
        "expanded_template": (
            "洞府石门轰然洞开，一道苍老却挺拔的身影步出。{name}的气息"
            "比当年更加深邃浩瀚。师徒对视良久，{name}微微一笑："
            "「你已青出于蓝了。」"
        ),
    },
    {
        "description": "师恩了结",
        "trigger": {"min_years_since_met": 70, "probability": 0.4},
        "effects": {"comprehension": 2, "willpower": 2},
        "event_type": "important",
        "text_template": "你终于感觉到与{name}之间的师徒因果已经圆满。",
        "expanded_template": (
            "无论{name}是否还在世间，你已经走出了属于自己的道路。"
            "师父的功法在你手中已经面目全非，化为了你自己的东西。"
            "你向师父来时的方向深深一拜：「师恩永记。」"
        ),
    },
]

# ── Lover destiny (道侣命运线 — 9拍) ──────────────────────────────────

LOVER_DESTINY = [
    {
        "description": "互生情愛",
        "trigger": {"min_years_since_met": 5, "min_sentiment": 60, "probability": 0.45},
        "effects": {"charisma": 1, "cultivation": 20},
        "event_type": "fortune",
        "text_template": "你与{name}在月下对坐，心中某种微妙的情愛惄然滔生。",
        "expanded_template": (
            "月光如水，{name}的侧脸在银辉中显得格外柔和。你不知何时起，"
            "目光开始追逐那道身影。两人相视一笑，一切尽在不言中。"
        ),
    },
    {
        "description": "共修初成",
        "trigger": {"min_years_since_met": 12, "min_sentiment": 70, "probability": 0.5},
        "effects": {"cultivation": 60, "constitution": 1},
        "event_type": "fortune",
        "text_template": "你与{name}首次尝试双修，灵气交融，修为互补。",
        "expanded_template": (
            "你与{name}对坐于灵脉之上，灵气在你们之间形成了奇妙的循环。"
            "一阴一阳，相互补益。当灵光散去，你们相视一笑——从此修行不再"
            "是一个人的事。"
        ),
    },
    {
        "description": "道侣面临劫难",
        "trigger": {"min_years_since_met": 20, "min_tension": 20, "probability": 0.35},
        "effects": {"constitution": -2, "willpower": 3, "cultivation": 40},
        "event_type": "danger",
        "text_template": "{name}在外历练时遭遇强敌，你毅然前往救援。",
        "expanded_template": (
            "收到{name}的求救飞剑时，你正在闭关的关键时刻。你没有犹豫，"
            "散去即将凝聚的灵力，提剑便走。「修为可以重来，人不行。」"
        ),
    },
    {
        "description": "道侣离别远行",
        "trigger": {"min_years_since_met": 28, "probability": 0.3},
        "effects": {"willpower": 2, "cultivation": 20},
        "event_type": "important",
        "text_template": "{name}为寻找突破契机，不得不远行，你们暂时分别。",
        "expanded_template": (
            "{name}站在山门前，回头看了你一眼。「等我回来。」你点头，"
            "看着那道身影渐渐消失在云端。从此夜深人静时，你总会不自觉"
            "地望向远方。"
        ),
    },
    {
        "description": "暗线纠葛",
        "trigger": {"min_years_since_met": 38, "probability": 0.35},
        "effects": {"willpower": 2, "charisma": -1},
        "event_type": "important",
        "text_template": "有人传言{name}在外已另结道侣，又或是有人欲对你们事下毒手。",
        "expanded_template": (
            "流言如毒，不断有人向你传递不利于{name}的消息。你心中明白，"
            "这或许是有人蓄意离间。但夜深人静时，疑虑的种子仍在心底生根。"
        ),
    },
    {
        "description": "重逢",
        "trigger": {"min_years_since_met": 48, "probability": 0.4},
        "effects": {"willpower": 3, "cultivation": 80},
        "event_type": "fortune",
        "text_template": "多年后，{name}终于归来，你们重逢于山门之前。",
        "expanded_template": (
            "当那个熟悉的身影出现在山门时，你几乎不敢相信自己的眼睛。"
            "{name}瘦了许多，但眼神更加明亮。你们相对无言，千言万语尽在"
            "不言中。"
        ),
    },
    {
        "description": "生死与共",
        "trigger": {"min_years_since_met": 58, "min_tension": 50, "probability": 0.35},
        "effects": {"constitution": -1, "willpower": 3, "cultivation": 60},
        "event_type": "danger",
        "text_template": "大劫降临，你与{name}并肩面对生死危局。",
        "expanded_template": (
            "天劫雷云压顶，{name}紧紧握住你的手。「在一起，生死不惧。」"
            "你点头，两人并肩迎向那道天地之威。此刻，比任何时候都更确信——"
            "这一路，幸而有彼此。"
        ),
    },
    {
        "description": "道心互证",
        "trigger": {"min_years_since_met": 70, "probability": 0.4},
        "effects": {"comprehension": 2, "cultivation": 50},
        "event_type": "important",
        "text_template": "你与{name}坐而论道，互证彼此的大道感悟。",
        "expanded_template": (
            "岁月磨去了很多东西，但你们之间的默契越发深厚。一言不发，"
            "却能感知彼此道心的走向。{name}轻声说道：「有你同行，修道不孤。」"
        ),
    },
    {
        "description": "并肩飞升或天人永隔",
        "trigger": {"min_years_since_met": 85, "probability": 0.4},
        "effects": {"willpower": 3, "fortune": 2},
        "event_type": "important",
        "text_template": "你与{name}的道侣之缘，迎来了最终的结局。",
        "expanded_template": (
            "无论未来如何，你和{name}之间的缘分已经刻入了天道的法则之中。"
            "这段感情，是你修行路上最珍贵的收获。"
        ),
    },
]

# ── Rival destiny (宿敌命运线 — 9拍) ──────────────────────────────────

RIVAL_DESTINY = [
    {
        "description": "初次交锋",
        "trigger": {"min_years_since_met": 3, "probability": 0.5},
        "effects": {"cultivation": 40, "willpower": 1},
        "event_type": "danger",
        "text_template": "你与{name}第一次正面交手，火花四溅。",
        "expanded_template": (
            "{name}的实力比你预想的更强。你们在断崖之上大战三百回合，"
            "不分胜负。临别时，{name}冷笑道：「下次见面，你不会这么幸运。」"
            "你攥紧了手中的剑。"
        ),
    },
    {
        "description": "宿敌暗中成长",
        "trigger": {"min_years_since_met": 10, "probability": 0.35},
        "effects": {"willpower": 2, "cultivation": 60},
        "event_type": "important",
        "text_template": "你收到消息，{name}的修为突飞猛进，隐隐有超越你的趋势。",
        "expanded_template": (
            "来自各处的消息都指向同一个事实——{name}正在以惊人的速度变强。"
            "有人说对方得到了某位大能的真传，也有人说对方走了邪道。"
            "不管怎样，你感受到了一股无形的压力。你必须更加努力。"
        ),
    },
    {
        "description": "暗中角力",
        "trigger": {"min_years_since_met": 18, "probability": 0.35},
        "effects": {"comprehension": 1, "cultivation": 40},
        "event_type": "important",
        "text_template": "你与{name}在同一处秘境中争夺机缘，未直接交手却暗中争锅。",
        "expanded_template": (
            "秘境之中，你感应到了{name}的气息。两人心照不宣，"
            "各自加快了探索的步伐。最终你抢先一步得到了机缘——但你知道，"
            "下一次未必这么幸运。"
        ),
    },
    {
        "description": "宿敌突袭",
        "trigger": {"min_years_since_met": 26, "min_tension": 40, "probability": 0.4},
        "effects": {"constitution": -3, "willpower": 2, "cultivation": 30},
        "event_type": "danger",
        "text_template": "{name}趁你闭关之际发动突袭，你猝不及防。",
        "expanded_template": (
            "午夜三更，禁制突然被人从外部强行破开。{name}的声音从黑暗中传来："
            "「等这一天，我等了太久了。」你来不及运功到巅峰，只能仓促应战。"
            "这是你修行以来最凶险的一夜。"
        ),
    },
    {
        "description": "反转联手",
        "trigger": {"min_years_since_met": 35, "min_tension": 60, "probability": 0.3},
        "effects": {"charisma": 1, "willpower": 2, "cultivation": 50},
        "event_type": "important",
        "text_template": "大敌当前，你与{name}不得不暂时联手对抗外敌。",
        "expanded_template": (
            "这是你从未想过的局面——与{name}背对背站在一起。"
            "「别误会，这次斗完，我们的账另算。」{name}冷冷说道。"
            "你点头，两人齐心协力迎向共同的敌人。"
        ),
    },
    {
        "description": "第二次正面对决",
        "trigger": {"min_years_since_met": 45, "probability": 0.4},
        "effects": {"constitution": -2, "willpower": 3, "cultivation": 80},
        "event_type": "danger",
        "text_template": "你与{name}约在绝峰之巅，进行断恩怨的生死决战。",
        "expanded_template": (
            "绝峰之上，风云变色。你与{name}相对而立，两人之间的因果今天"
            "必须做个了断。这一战，你们都拿出了全部底牌。天地为之变色，"
            "方圆百里的修士都感应到了这场决战的气息。"
        ),
    },
    {
        "description": "恩怨了结",
        "trigger": {"min_years_since_met": 55, "probability": 0.4},
        "effects": {"willpower": 3, "comprehension": 2},
        "event_type": "important",
        "text_template": "你与{name}的恩怨，终于画上了句号。",
        "expanded_template": (
            "多年的纠葛在这一刻烟消云散。不管是你胜还是对方败，这段宿命般"
            "的对抗都让你变得更强。没有{name}，就没有今天的你。"
        ),
    },
    {
        "description": "惺惺相惜",
        "trigger": {"min_years_since_met": 68, "probability": 0.35},
        "effects": {"comprehension": 1, "willpower": 1},
        "event_type": "fortune",
        "text_template": "多年后，你与{name}偶然重逢，昔日宿敌已无杀意。",
        "expanded_template": (
            "在某处云海之巅，你与{name}不期而遇。对方的眼中已无昔日杀意，"
            "只剩一种同道之间的淡然。「这些年，没你逼着，我倒进步慢了。」"
            "{name}轻笑一声，转身飘然而去。"
        ),
    },
    {
        "description": "彼此成就",
        "trigger": {"min_years_since_met": 80, "probability": 0.4},
        "effects": {"comprehension": 2, "willpower": 2},
        "event_type": "important",
        "text_template": "回首往事，你明白{name}是你道路上不可或缺的磨刀石。",
        "expanded_template": (
            "时光流转，当年的生死相搏已成云烟。你心中清楚，没有{name}"
            "的鼓舞与刺激，你不可能走到今天。这段宿命般的缘分，"
            "是天道给你最好的砺石。"
        ),
    },
]


def get_destiny_template(relation_type: str) -> list[dict]:
    """Return a copy of the destiny template for a given relation type.

    Only 师父/道侣/宿敌 have destiny lines. Others return empty list.
    """
    mapping = {
        "师父": MASTER_DESTINY,
        "道侣": LOVER_DESTINY,
        "宿敌": RIVAL_DESTINY,
    }
    template = mapping.get(relation_type, [])
    # Deep copy to avoid shared mutation
    return [
        {k: (v.copy() if isinstance(v, dict) else v) for k, v in beat.items()}
        for beat in template
    ]


# ── NPC Destiny Generator (LLM动态生成) ──────────────────────────────

import json
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..ai import LLMClient
    from ...models import GameState

logger = logging.getLogger(__name__)

# Dramatic keywords that may trigger a destiny pivot (30 keywords, 6 categories)
# Note: "道侣" excluded — it appears in too many normal events, causing false pivots
DRAMATIC_KEYWORDS = {
    # 生死类
    "陨落", "生死", "重伤", "濒死", "牺牲", "死别",
    # 重大转折
    "走火入魔", "大机缘", "背叛", "决裂", "反目", "绝交",
    # 命运节点
    "传承", "拜师", "诀别", "结仇", "结义", "定情", "立誓",
    # 境界突破
    "突破", "灵根", "飞升", "渡劫",
    # 宗门变故
    "灭门", "叛出", "逆伐", "放逐",
    # 其他戏剧性
    "失踪", "囚禁", "解封", "复仇", "和解", "归隐",
}

# Cooldown: minimum years between two pivots for the same NPC
_PIVOT_COOLDOWN_YEARS = 30


class NpcDestinyGenerator:
    """LLM-powered NPC destiny line generator with template fallback.

    Generates personalized destiny arcs (7 beats for master, 9 for lover/rival,
    5 for others) based on NPC personality, and can pivot (rewrite) remaining
    beats when dramatic events occur.
    """

    # Rhythm guidance per beat count
    RHYTHM_BY_COUNT = {
        5: "相识→深入→危机→高潮→结局",
        7: "收徒→传授→放手→危机→转折→回归→了结",
        9: "相识→情感萌生→深入→危机→离别→暗线→重逢→高潮→终局",
    }
    YEARS_BY_COUNT = {
        5: "3→15→25→40→55",
        7: "3→10→20→30→40→55→70",
        9: "5→12→20→28→38→48→58→70→85",
    }

    def __init__(self, llm_client: "LLMClient"):
        self.llm_client = llm_client

    def generate_destiny(
        self,
        npc_dict: dict,
        relation_type: str,
        state: "GameState",
    ) -> list[dict]:
        """Generate destiny line via LLM. Falls back to template on failure.

        Beat count is determined by relation type:
        - 师父: 7 beats
        - 道侣/宿敌: 9 beats
        - Others: 5 beats (default)
        """
        from ..ai.prompt_templates import (
            NPC_DESTINY_GENERATION_SYSTEM,
            NPC_DESTINY_GENERATION_USER,
        )
        from ...models import REALM_NAMES, Realm

        beat_count = BEAT_COUNT_BY_RELATION.get(relation_type, DEFAULT_BEAT_COUNT)

        if not self.llm_client.available:
            logger.debug("LLM unavailable, falling back to destiny template")
            return get_destiny_template(relation_type)

        # Build user prompt
        player_realm_name = REALM_NAMES.get(Realm(state.realm), "凡人")
        npc_realm_name = REALM_NAMES.get(Realm(npc_dict.get("realm", 0)), "凡人")
        storyline = state.main_storyline or {}
        archetype = storyline.get("archetype", "未定")

        rhythm = self.RHYTHM_BY_COUNT.get(beat_count, self.RHYTHM_BY_COUNT[5])
        years_sug = self.YEARS_BY_COUNT.get(beat_count, self.YEARS_BY_COUNT[5])

        system_prompt = NPC_DESTINY_GENERATION_SYSTEM.format(
            beat_count=beat_count,
            rhythm_guidance=f"- {beat_count}个节拍应体现：{rhythm} 的叙事弧线",
            years_suggestion=f"{years_sug}（可微调）",
        )

        user_prompt = NPC_DESTINY_GENERATION_USER.format(
            beat_count=beat_count,
            relation_type=relation_type,
            personality=npc_dict.get("personality", "温和"),
            motivation=npc_dict.get("motivation", "未知"),
            secret=npc_dict.get("secret", "无"),
            growth_arc=npc_dict.get("growth_arc", "未定"),
            npc_realm=npc_realm_name,
            player_realm=player_realm_name,
            player_age=state.age,
            gender="男" if state.gender == "male" else "女",
            storyline_archetype=archetype,
        )

        # Scale max_tokens with beat count
        max_tokens = 600 + (beat_count - 5) * 150

        result = self.llm_client.generate_sync(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=0.85,
        )

        if not result:
            logger.warning("LLM destiny generation returned None, using template")
            return get_destiny_template(relation_type)

        beats = self._parse_beats(result, expected_count=beat_count)
        if not beats:
            logger.warning("Failed to parse LLM destiny beats, using template")
            return get_destiny_template(relation_type)

        logger.info(
            "Generated LLM destiny for %s (%s): %d beats",
            npc_dict.get("name", "?"), relation_type, len(beats),
        )
        return beats

    def pivot_destiny(
        self,
        npc_dict: dict,
        rel_dict: dict,
        trigger_event: dict,
        state: "GameState",
    ) -> bool:
        """Rewrite remaining destiny beats after a dramatic event.

        Returns True if pivot succeeded, False otherwise (keeps original beats).
        """
        from ..ai.prompt_templates import (
            NPC_DESTINY_PIVOT_SYSTEM,
            NPC_DESTINY_PIVOT_USER,
        )
        from ...models import REALM_NAMES, Realm

        if not self.llm_client.available:
            return False

        destiny_beats = npc_dict.get("destiny_beats", [])
        idx = npc_dict.get("current_destiny_index", 0)
        remaining_count = len(destiny_beats) - idx

        if remaining_count <= 0:
            return False

        # Build completed beats text
        completed = destiny_beats[:idx]
        completed_text = "\n".join(
            f"{i+1}. {b.get('description', '')}"
            for i, b in enumerate(completed)
        ) or "无（尚未触发任何节拍）"

        player_realm_name = REALM_NAMES.get(Realm(state.realm), "凡人")
        first_met = npc_dict.get("first_met_age", 0)
        years_since_met = state.age - first_met

        user_prompt = NPC_DESTINY_PIVOT_USER.format(
            trigger_event_text=trigger_event.get("text", "") or trigger_event.get("expanded_text", ""),
            npc_name=npc_dict.get("name", "某人"),
            relation_type=rel_dict.get("relation_type", "未知"),
            personality=npc_dict.get("personality", "温和"),
            motivation=npc_dict.get("motivation", "未知"),
            sentiment=rel_dict.get("sentiment", 0),
            completed_beats_text=completed_text,
            player_realm=player_realm_name,
            player_age=state.age,
            years_since_met=years_since_met,
            remaining_count=remaining_count,
        )

        result = self.llm_client.generate_sync(
            system_prompt=NPC_DESTINY_PIVOT_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=800,
            temperature=0.85,
        )

        if not result:
            logger.warning("LLM destiny pivot returned None, keeping original")
            return False

        new_beats = self._parse_beats(result, expected_count=remaining_count)
        if not new_beats:
            logger.warning("Failed to parse pivot beats, keeping original")
            return False

        # Replace remaining beats
        npc_dict["destiny_beats"] = completed + new_beats
        logger.info(
            "Pivoted destiny for %s: replaced %d remaining beats",
            npc_dict.get("name", "?"), remaining_count,
        )
        return True

    def should_pivot(
        self,
        npc_dict: dict,
        rel_dict: dict,
        event: dict,
        prev_sentiment: Optional[int] = None,
        current_age: int = 0,
    ) -> bool:
        """Determine if a dramatic event should trigger a destiny pivot.

        Trigger conditions (ALL must pass cooldown first):
        - Sentiment change >= 30 in a single turn
        - Event text contains dramatic keywords and involves this NPC
        """
        # Already completed destiny
        if npc_dict.get("destiny_completed", False):
            return False

        # Cooldown: prevent frequent pivots for same NPC
        last_pivot_age = npc_dict.get("_last_pivot_age", -999)
        if current_age - last_pivot_age < _PIVOT_COOLDOWN_YEARS:
            return False

        npc_name = npc_dict.get("name", "")
        # Only check primary text for keywords (not expanded_text to avoid false positives)
        event_text = event.get("text", "")

        # Check if event involves this NPC
        involved_npc = event.get("involved_npc", "")
        if involved_npc != npc_name and npc_name not in event_text:
            return False

        # Condition 1: Large sentiment swing
        if prev_sentiment is not None:
            current = rel_dict.get("sentiment", 0)
            if abs(current - prev_sentiment) >= 30:
                return True

        # Condition 2: Dramatic keywords in event (require >= 2 keyword hits)
        hits = sum(1 for kw in DRAMATIC_KEYWORDS if kw in event_text)
        if hits >= 2:
            return True

        return False

    @staticmethod
    def _parse_beats(raw: str, expected_count: int) -> Optional[list[dict]]:
        """Parse LLM response into list of beat dicts. Returns None on failure."""
        # Strip potential markdown code fences
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            text = text.strip()

        try:
            beats = json.loads(text)
        except json.JSONDecodeError:
            logger.debug("JSON parse failed for destiny beats: %s...", text[:100])
            return None

        if not isinstance(beats, list):
            return None

        # Validate each beat has required fields
        required_fields = {"description", "trigger", "effects", "event_type", "text_template"}
        validated = []
        for beat in beats:
            if not isinstance(beat, dict):
                continue
            if not required_fields.issubset(beat.keys()):
                continue
            # Ensure trigger has min_years_since_met
            trigger = beat.get("trigger", {})
            if "min_years_since_met" not in trigger:
                trigger["min_years_since_met"] = 5 * (len(validated) + 1)
            if "probability" not in trigger:
                trigger["probability"] = 0.4
            # Ensure keywords is a list
            if "keywords" not in beat or not isinstance(beat.get("keywords"), list):
                beat["keywords"] = []
            # Ensure expanded_template exists
            if "expanded_template" not in beat:
                beat["expanded_template"] = beat.get("text_template", "")
            validated.append(beat)

        if len(validated) < max(1, expected_count - 1):
            # Too few valid beats
            return None

        return validated[:expected_count]
