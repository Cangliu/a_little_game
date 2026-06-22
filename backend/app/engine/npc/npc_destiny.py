"""NPC Destiny System — independent NPC storylines.

Gives key NPCs (master, lover, rival) an independent destiny arc
with 5 narrative beats that trigger based on time, relationship,
tension, and probability conditions.
"""
from __future__ import annotations

# ── Master destiny (师父命运线) ────────────────────────────────────────

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
        "description": "师父闭死关",
        "trigger": {"min_years_since_met": 15, "probability": 0.3},
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
        "trigger": {"min_years_since_met": 25, "min_tension": 30, "probability": 0.4},
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
        "description": "师恩了结",
        "trigger": {"min_years_since_met": 60, "probability": 0.4},
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

# ── Lover destiny (道侣命运线) ────────────────────────────────────────

LOVER_DESTINY = [
    {
        "description": "共修初成",
        "trigger": {"min_years_since_met": 5, "min_sentiment": 70, "probability": 0.5},
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
        "trigger": {"min_years_since_met": 15, "min_tension": 20, "probability": 0.35},
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
        "trigger": {"min_years_since_met": 25, "probability": 0.3},
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
        "description": "重逢",
        "trigger": {"min_years_since_met": 40, "probability": 0.4},
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
        "description": "并肩飞升或天人永隔",
        "trigger": {"min_years_since_met": 60, "probability": 0.4},
        "effects": {"willpower": 3, "fortune": 2},
        "event_type": "important",
        "text_template": "你与{name}的道侣之缘，迎来了最终的结局。",
        "expanded_template": (
            "无论未来如何，你和{name}之间的缘分已经刻入了天道的法则之中。"
            "这段感情，是你修行路上最珍贵的收获。"
        ),
    },
]

# ── Rival destiny (宿敌命运线) ────────────────────────────────────────

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
        "trigger": {"min_years_since_met": 15, "probability": 0.35},
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
        "description": "宿敌突袭",
        "trigger": {"min_years_since_met": 25, "min_tension": 40, "probability": 0.4},
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
        "description": "正面对决",
        "trigger": {"min_years_since_met": 40, "probability": 0.4},
        "effects": {"constitution": -2, "willpower": 3, "cultivation": 80},
        "event_type": "danger",
        "text_template": "你与{name}约在绝峰之巅，进行了断恩怨的生死决战。",
        "expanded_template": (
            "绝峰之上，风云变色。你与{name}相对而立，两人之间的因果今天"
            "必须做个了断。这一战，你们都拿出了全部底牌。天地为之变色，"
            "方圆百里的修士都感应到了这场决战的气息。"
        ),
    },
    {
        "description": "恩怨了结",
        "trigger": {"min_years_since_met": 55, "probability": 0.45},
        "effects": {"willpower": 3, "comprehension": 2},
        "event_type": "important",
        "text_template": "你与{name}的恩怨，终于画上了句号。",
        "expanded_template": (
            "多年的纠葛在这一刻烟消云散。不管是你胜还是对方败，这段宿命般"
            "的对抗都让你变得更强。没有{name}，就没有今天的你。你望着远方，"
            "第一次对这个宿敌生出了几分感激。"
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
