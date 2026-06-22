"""Event generator for high-realm events (筑基 through 化神).

Generates approximately 6,500 new events using template x variable
cartesian products. Events are brief outlines meant to be expanded
by LLM at runtime.

Usage:
    python3 -m app.event_generator_realms
"""
import json
import os
import random
import itertools
from typing import List, Dict

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "events")

# ─── Shared Variables ─────────────────────────────────────────────────

TECHNIQUES = ["剑意", "丹道", "阵法", "神通", "禁术", "炼体", "御器", "符箓", "音攻", "隐匿"]
ELEMENTS = ["金", "木", "水", "火", "土", "雷", "风", "冰", "暗", "光"]
LOCATIONS = [
    "洞府", "灵脉", "秘境", "深渊", "古战场", "仙府遗迹",
    "海底宫殿", "火山深处", "万年冰原", "九天之上",
    "混沌空间", "时间裂缝", "星辰大阵", "虚空通道",
]
TREASURES = [
    "千年灵芝", "九转还魂草", "天火精华", "龙血晶", "凤凰涅槃果",
    "混沌灵液", "太古精血", "星辰之核", "造化神泥", "鸿蒙紫气",
    "万年寒铁", "九天玄玉", "天外陨铁", "地心神火", "归墟之水",
]
DANGERS = [
    "心魔侵袭", "天劫余波", "走火入魔", "灵气暴动", "经脉逆转",
    "魔修偷袭", "妖兽围攻", "禁制反噬", "毒瘴侵体", "时空乱流",
]
INSIGHTS = [
    "天地法则", "因果轮回", "阴阳之道", "五行相生", "生死大道",
    "时间法则", "空间之力", "命运之理", "万物归一", "道法自然",
]
SECT_EVENTS = [
    "宗门大比", "长老议事", "弟子选拔", "宗门迁址", "外敌来犯",
    "宗门联盟", "资源分配", "传承争夺", "门规修改", "宗门庆典",
]
WORLD_EVENTS_TEMPLATES = [
    "修真界发生了一场大变故，{event}",
    "天地异象频现，{event}",
    "各大宗门纷纷关注，{event}",
]


def _id(prefix: str, idx: int) -> str:
    return f"{prefix}_{idx:05d}"


# ─── Mortal Events (realm 0) ─────────────────────────────────────────

def generate_mortal_events() -> List[Dict]:
    """Generate ~200 additional mortal events."""
    events = []
    idx = 5000

    mortal_daily = [
        "你在田间劳作，收成颇丰", "你与邻里发生口角，心情郁闷",
        "你在集市上遇到一位算命先生，对方说你命中有贵人",
        "你帮助了一位落难老者", "你在河边钓鱼时看到异象",
        "一位路过的道士在你家借宿", "你做了一个奇怪的梦",
        "村里来了一群江湖人", "你在山上采药时迷了路",
        "你救了一只受伤的灵禽", "天降流星，你许了个愿",
        "你听老人讲述修仙者的传说", "你在古井中发现一块奇石",
        "你无意间看到天空中有人御剑飞行", "村中瘟疫蔓延，你安然无恙",
        "你在雷雨天感到体内有异样的悸动", "你被一位神秘人盯上了",
        "你偶得一本残破古书", "你在梦中看到了一座仙山",
        "一道流光坠入你家后院",
    ]

    seasons = ["春", "夏", "秋", "冬"]
    feelings = ["平静", "不安", "期待", "困惑", "喜悦"]

    for tmpl in mortal_daily:
        events.append({
            "id": _id("mortal_new", idx),
            "text": tmpl,
            "expanded_text": tmpl,
            "category": "common",
            "conditions": {"min_realm": 0, "max_realm": 0},
            "weight": 50,
            "effects": {},
            "tags": ["mortal_life"],
            "event_type": "normal",
        })
        idx += 1

    # Seasonal events
    for season in seasons:
        for tmpl in [
            f"{season}日里你感受到自然的力量", f"{season}天的第一场雨让你心生感悟",
            f"{season}末你在山间游历", f"一个寻常的{season}日，你的生活发生了变化",
            f"{season}风吹过，你感到一丝与往日不同的气息",
        ]:
            events.append({
                "id": _id("mortal_season", idx),
                "text": tmpl, "expanded_text": tmpl,
                "category": "common",
                "conditions": {"min_realm": 0, "max_realm": 0},
                "weight": 40, "effects": {}, "tags": ["mortal_life"],
                "event_type": "normal",
            })
            idx += 1

    # Fortune/calamity for mortals
    mortal_fortune = [
        "你在路边捡到一枚铜钱，当日诸事顺遂",
        "你无意中帮助了一位仙人的后裔",
        "你在梦中得到一位仙人的指点",
        "家中祖坟冒出紫气", "你的体质突然变好了",
    ]
    mortal_calamity = [
        "你遭遇山贼", "你生了一场重病", "洪水冲毁了家园",
        "你被野兽追赶", "一场大火烧了村子",
    ]
    for tmpl in mortal_fortune:
        events.append({
            "id": _id("mortal_fort", idx), "text": tmpl, "expanded_text": tmpl,
            "category": "fortune", "conditions": {"min_realm": 0, "max_realm": 0},
            "weight": 30, "effects": {"fortune": 1}, "tags": ["mortal_life"],
            "event_type": "fortune",
        })
        idx += 1
    for tmpl in mortal_calamity:
        events.append({
            "id": _id("mortal_cala", idx), "text": tmpl, "expanded_text": tmpl,
            "category": "calamity", "conditions": {"min_realm": 0, "max_realm": 0},
            "weight": 25, "effects": {"constitution": -1}, "tags": ["mortal_life"],
            "event_type": "danger",
        })
        idx += 1

    return events


# ─── Qi Refining Events (realm 1) ────────────────────────────────────

def generate_qi_refining_events() -> List[Dict]:
    """Generate ~300 additional Qi Refining events."""
    events = []
    idx = 6000

    bases = [
        "你打坐吐纳，感受灵气入体的过程",
        "你尝试引导{element}属性灵气入体",
        "你在{location}修炼，灵气充沛",
        "你研读一本{technique}入门典籍",
        "你向师兄请教{technique}修炼心得",
        "你在修炼中遇到小瓶颈，静心调息后突破",
        "你尝试凝聚灵气于掌心，初见成效",
        "你练习基础剑法，剑气初显",
        "你第一次成功炼制出一枚低阶丹药",
        "你在晨间吐纳时感受到一缕异样灵气",
        "你的灵根与天地灵气产生了短暂共鸣",
        "你尝试布置一个简单的聚灵阵",
    ]

    for base in bases:
        for elem in ELEMENTS[:5]:
            text = base.format(element=elem, location=random.choice(LOCATIONS[:4]),
                              technique=random.choice(TECHNIQUES[:5]))
            events.append({
                "id": _id("qi_ref", idx), "text": text, "expanded_text": text,
                "category": "cultivation",
                "conditions": {"min_realm": 1, "max_realm": 1},
                "weight": 50, "effects": {"cultivation": random.randint(3, 8)},
                "tags": ["practice", "qi_refining"], "event_type": "normal",
            })
            idx += 1

    # Social events for qi refining
    qi_social = [
        "你在坊市中与一位同期弟子切磋", "你参加了宗门的月末考核",
        "你与同门结伴外出历练", "一位师姐赠你一瓶聚气丹",
        "你在宗门任务中结识了新朋友", "你帮助一位低阶弟子解答疑惑",
    ]
    for tmpl in qi_social:
        events.append({
            "id": _id("qi_social", idx), "text": tmpl, "expanded_text": tmpl,
            "category": "social", "conditions": {"min_realm": 1, "max_realm": 2},
            "weight": 40, "effects": {"cultivation": random.randint(1, 3)},
            "tags": ["social", "qi_refining"], "event_type": "normal",
        })
        idx += 1

    return events


# ─── Foundation Events (realm 2) ─────────────────────────────────────

def generate_foundation_events() -> List[Dict]:
    """Generate ~1500 Foundation Building events."""
    events = []
    idx = 7000

    # Cultivation daily (40%)
    cult_templates = [
        "你闭关修炼，感受筑基后灵力的质变",
        "你尝试以{technique}之道领悟更高层次的法则",
        "你在{location}闭关，灵气浓郁修为精进",
        "你参悟{element}属性功法，有所收获",
        "你凝练真元，根基愈发稳固",
        "你在闭关中感悟到{technique}的一丝真意",
        "你尝试将两种属性灵力融合",
        "你的神识范围扩大了一些",
        "你苦修{technique}，终于小有所成",
        "你在灵脉上盘坐修炼，效率倍增",
        "你研习一门新的{technique}功法",
        "你打磨根基，为将来冲击金丹做准备",
        "你尝试催动一件中品法器",
        "你修炼神识之术，精神力增长显著",
        "你参悟师父留下的功法残卷",
    ]

    for tmpl in cult_templates:
        for tech in TECHNIQUES:
            for elem in ELEMENTS[:5]:
                for loc in LOCATIONS[:5]:
                    text = tmpl.format(technique=tech, element=elem, location=loc)
                    events.append({
                        "id": _id("found_cult", idx), "text": text, "expanded_text": text,
                        "category": "cultivation",
                        "conditions": {"min_realm": 2, "max_realm": 3},
                        "weight": 50,
                        "effects": {"cultivation": random.randint(8, 20)},
                        "tags": ["practice", "foundation"],
                        "event_type": "normal",
                        "duration": random.choice([0, 0, 0, 1, 2]),
                    })
                    idx += 1
                    if idx - 7000 >= 600:
                        break
                if idx - 7000 >= 600:
                    break
            if idx - 7000 >= 600:
                break
        if idx - 7000 >= 600:
            break

    # Fortune events (15%)
    fortune_templates = [
        "你在{location}中发现了{treasure}",
        "你意外获得一位前辈的{technique}传承",
        "一位路过的高人指点你{technique}修炼",
        "你在坊市以低价购得{treasure}",
        "你在探索古洞时找到一枚筑基丹",
        "你领悟了{element}属性的法则碎片",
        "你救了一只灵兽，它以灵果报恩",
        "你在天材地宝产出之地守了数月终于等到",
    ]
    for tmpl in fortune_templates:
        for i in range(28):
            text = tmpl.format(
                location=random.choice(LOCATIONS),
                treasure=random.choice(TREASURES),
                technique=random.choice(TECHNIQUES),
                element=random.choice(ELEMENTS),
            )
            events.append({
                "id": _id("found_fort", idx), "text": text, "expanded_text": text,
                "category": "fortune",
                "conditions": {"min_realm": 2, "max_realm": 3},
                "weight": 30,
                "effects": {"cultivation": random.randint(15, 40), "fortune": random.choice([0, 0, 1])},
                "tags": ["fortune", "foundation"], "event_type": "fortune",
            })
            idx += 1

    # Calamity events (15%)
    calamity_templates = [
        "你遭遇{danger}，险些丧命",
        "修炼{technique}时失误，{danger}",
        "你在{location}探索时遇险",
        "一位同门暗中陷害你",
        "你在渡小劫时受了重伤",
        "你被卷入修士间的争斗",
        "你体内灵力失控，走火入魔的边缘",
        "一头变异妖兽向你发起攻击",
    ]
    for tmpl in calamity_templates:
        for i in range(28):
            text = tmpl.format(
                danger=random.choice(DANGERS),
                technique=random.choice(TECHNIQUES),
                location=random.choice(LOCATIONS),
            )
            events.append({
                "id": _id("found_cala", idx), "text": text, "expanded_text": text,
                "category": "calamity",
                "conditions": {"min_realm": 2, "max_realm": 3},
                "weight": 30,
                "effects": {"constitution": random.choice([-1, -1, 0]), "cultivation": random.randint(-5, 5)},
                "tags": ["calamity", "foundation"], "event_type": "danger",
            })
            idx += 1

    # Social events (15%)
    social_templates = [
        "你参加修士聚会，与同辈交流{technique}心得",
        "你接受宗门任务前往外地",
        "你与一位筑基同修切磋法术",
        "你在坊市出售自己炼制的丹药",
        "你加入一支探险队伍前往{location}",
        "你收了一个练气期弟子",
        "你代表宗门参加{event}",
        "你与同门一起执行危险任务",
    ]
    for tmpl in social_templates:
        for i in range(28):
            text = tmpl.format(
                technique=random.choice(TECHNIQUES),
                location=random.choice(LOCATIONS),
                event=random.choice(SECT_EVENTS),
            )
            events.append({
                "id": _id("found_soc", idx), "text": text, "expanded_text": text,
                "category": "social",
                "conditions": {"min_realm": 2, "max_realm": 3},
                "weight": 35,
                "effects": {"cultivation": random.randint(2, 8), "charisma": random.choice([0, 0, 1])},
                "tags": ["social", "foundation"], "event_type": "normal",
            })
            idx += 1

    # World events (10%)
    world_templates = [
        "修真界传出{location}中现世了{treasure}的消息",
        "附近的宗门爆发了一场冲突",
        "天降异象，各宗门纷纷派人查探",
        "一位化神大能陨落，天地为之变色",
        "坊市物价暴涨，灵石贬值",
        "一处新的灵脉被发现，引发争夺",
    ]
    for tmpl in world_templates:
        for i in range(20):
            text = tmpl.format(
                location=random.choice(LOCATIONS),
                treasure=random.choice(TREASURES),
            )
            events.append({
                "id": _id("found_world", idx), "text": text, "expanded_text": text,
                "category": "world",
                "conditions": {"min_realm": 2, "max_realm": 4},
                "weight": 25, "effects": {},
                "tags": ["world", "foundation"], "event_type": "normal",
            })
            idx += 1

    # Philosophy (5%)
    phil_templates = [
        "你感悟{insight}，心境有所提升",
        "你在枯坐中思考{insight}",
        "一花一叶间你看到了{insight}的影子",
        "你突然对{insight}有了新的理解",
    ]
    for tmpl in phil_templates:
        for ins in INSIGHTS[:5]:
            text = tmpl.format(insight=ins)
            events.append({
                "id": _id("found_phil", idx), "text": text, "expanded_text": text,
                "category": "cultivation",
                "conditions": {"min_realm": 2, "max_realm": 4},
                "weight": 30,
                "effects": {"willpower": random.choice([0, 1]), "comprehension": random.choice([0, 0, 1])},
                "tags": ["philosophy", "foundation"], "event_type": "normal",
            })
            idx += 1

    return events


# ─── Golden Core Events (realm 3) ────────────────────────────────────

def generate_golden_core_events() -> List[Dict]:
    """Generate ~1800 Golden Core events."""
    events = []
    idx = 10000

    # Cultivation (40%) - longer durations
    cult_templates = [
        "你闭关炼化{treasure}，金丹愈发圆润",
        "你以金丹之力感悟{element}属性法则",
        "你在{location}闭关数载，修为大进",
        "你参悟{technique}奥义，神通初成",
        "你凝练金丹，为元婴做准备",
        "你尝试以金丹之力催动一件上品法器",
        "你修炼分身术，初步掌握神识分离",
        "你苦修{technique}，小神通已成",
        "你吞服{treasure}辅助修炼",
        "你在灵气最浓处闭关感悟天地",
        "你打磨金丹，使其更加凝实",
        "你尝试在金丹中刻录{element}法则",
        "你的金丹表面浮现{element}符文",
        "你修炼护体神通以备不时之需",
        "你将全部精力投入{technique}大成之路",
    ]

    durations_gc = [0, 0, 2, 3, 5, 5, 8]
    for tmpl in cult_templates:
        for tech in TECHNIQUES:
            for elem in ELEMENTS[:6]:
                text = tmpl.format(
                    technique=tech, element=elem,
                    location=random.choice(LOCATIONS),
                    treasure=random.choice(TREASURES),
                )
                dur = random.choice(durations_gc)
                events.append({
                    "id": _id("gc_cult", idx), "text": text, "expanded_text": text,
                    "category": "cultivation",
                    "conditions": {"min_realm": 3, "max_realm": 4},
                    "weight": 50,
                    "effects": {"cultivation": random.randint(20, 50)},
                    "tags": ["practice", "golden_core"],
                    "event_type": "normal",
                    "duration": dur,
                })
                idx += 1
                if idx - 10000 >= 720:
                    break
            if idx - 10000 >= 720:
                break
        if idx - 10000 >= 720:
            break

    # Fortune (15%)
    fortune_gc = [
        "你在{location}深处发现了{treasure}",
        "一位元婴前辈赐你{technique}秘法",
        "你在古修洞府中得到一枚金丹期辅助丹药",
        "你在秘境中偶得上古{technique}残篇",
        "你体内金丹突然产生异变，凝实了三分",
        "你在交易会上以奇物换得{treasure}",
        "天降机缘，一缕{element}精纯灵气涌入体内",
        "你解开了一处远古禁制，内有惊天造化",
    ]
    for tmpl in fortune_gc:
        for i in range(34):
            text = tmpl.format(
                location=random.choice(LOCATIONS),
                treasure=random.choice(TREASURES),
                technique=random.choice(TECHNIQUES),
                element=random.choice(ELEMENTS),
            )
            events.append({
                "id": _id("gc_fort", idx), "text": text, "expanded_text": text,
                "category": "fortune",
                "conditions": {"min_realm": 3, "max_realm": 4},
                "weight": 25,
                "effects": {"cultivation": random.randint(30, 80), "fortune": random.choice([0, 0, 1])},
                "tags": ["fortune", "golden_core"], "event_type": "fortune",
                "duration": random.choice([0, 0, 1, 2]),
            })
            idx += 1

    # Calamity (15%)
    calamity_gc = [
        "你遭遇金丹期{danger}",
        "一位金丹同辈向你发起生死挑战",
        "你在闭关时遭遇心魔侵扰",
        "修炼{technique}时反噬严重",
        "你在{location}被困于上古禁制中",
        "你的金丹出现裂纹，需要紧急修复",
        "魔修趁你闭关之际偷袭",
        "你中了一种罕见灵毒",
    ]
    for tmpl in calamity_gc:
        for i in range(34):
            text = tmpl.format(
                danger=random.choice(DANGERS),
                technique=random.choice(TECHNIQUES),
                location=random.choice(LOCATIONS),
            )
            events.append({
                "id": _id("gc_cala", idx), "text": text, "expanded_text": text,
                "category": "calamity",
                "conditions": {"min_realm": 3, "max_realm": 4},
                "weight": 25,
                "effects": {"constitution": random.choice([-1, -1, 0]), "cultivation": random.randint(-10, 5)},
                "tags": ["calamity", "golden_core"], "event_type": "danger",
            })
            idx += 1

    # Social (15%)
    social_gc = [
        "你受邀参加金丹修士的论道会",
        "你代表宗门出席{event}",
        "你与一位金丹道友结为挚友",
        "你在修士聚会上展示{technique}造诣",
        "你被推举为宗门长老候选",
        "一位后辈向你求教{technique}",
        "你与其他金丹修士组队探索{location}",
        "你在宗门中的地位提升了",
    ]
    for tmpl in social_gc:
        for i in range(34):
            text = tmpl.format(
                technique=random.choice(TECHNIQUES),
                event=random.choice(SECT_EVENTS),
                location=random.choice(LOCATIONS),
            )
            events.append({
                "id": _id("gc_soc", idx), "text": text, "expanded_text": text,
                "category": "social",
                "conditions": {"min_realm": 3, "max_realm": 4},
                "weight": 30,
                "effects": {"cultivation": random.randint(5, 15), "charisma": random.choice([0, 0, 1])},
                "tags": ["social", "golden_core"], "event_type": "normal",
            })
            idx += 1

    # World (10%)
    world_gc = [
        "修真界爆发了一场金丹级别的大战",
        "一处上古遗迹开启，各方势力云集",
        "天降{element}劫雷异象，修真界震动",
        "魔道大举入侵，各宗门联手抵御",
        "一位金丹大修陨落引发势力洗牌",
        "修真界新发现了一处金丹级秘境",
    ]
    for tmpl in world_gc:
        for i in range(15):
            text = tmpl.format(element=random.choice(ELEMENTS))
            events.append({
                "id": _id("gc_world", idx), "text": text, "expanded_text": text,
                "category": "world",
                "conditions": {"min_realm": 3, "max_realm": 5},
                "weight": 20, "effects": {},
                "tags": ["world", "golden_core"], "event_type": "normal",
            })
            idx += 1

    # Philosophy (5%)
    for ins in INSIGHTS:
        for prefix in ["你在金丹运转中感悟", "你突然对", "闭关枯坐中你领悟了"]:
            text = f"{prefix}{ins}的一丝真意"
            events.append({
                "id": _id("gc_phil", idx), "text": text, "expanded_text": text,
                "category": "cultivation",
                "conditions": {"min_realm": 3, "max_realm": 5},
                "weight": 25,
                "effects": {"willpower": random.choice([0, 1]), "comprehension": random.choice([0, 0, 1])},
                "tags": ["philosophy", "golden_core"], "event_type": "normal",
            })
            idx += 1

    return events


# ─── Nascent Soul Events (realm 4) ───────────────────────────────────

def generate_nascent_soul_events() -> List[Dict]:
    """Generate ~1500 Nascent Soul events."""
    events = []
    idx = 14000

    # Cultivation (40%) - very long durations
    cult_templates = [
        "你元婴出窍游历虚空，感悟天地之力",
        "你闭关百年凝练元婴，修为愈发深厚",
        "你以元婴之力炼化{treasure}",
        "你参悟{element}大道真意",
        "你修炼{technique}大神通，威力惊人",
        "你在{location}中以元婴感应天地法则",
        "你尝试凝聚{element}领域",
        "你的元婴蜕变了一次，实力倍增",
        "你以神念探索{location}深处的奥秘",
        "你修炼天级{technique}功法",
        "你吞服{treasure}壮大元婴",
        "你领悟了{element}法则的一丝本源",
        "你的元婴凝实了三分，距化神更近一步",
    ]

    durations_ns = [0, 3, 5, 8, 10, 15, 20]
    for tmpl in cult_templates:
        for tech in TECHNIQUES:
            for elem in ELEMENTS[:5]:
                text = tmpl.format(
                    technique=tech, element=elem,
                    location=random.choice(LOCATIONS),
                    treasure=random.choice(TREASURES),
                )
                dur = random.choice(durations_ns)
                events.append({
                    "id": _id("ns_cult", idx), "text": text, "expanded_text": text,
                    "category": "cultivation",
                    "conditions": {"min_realm": 4, "max_realm": 5},
                    "weight": 50,
                    "effects": {"cultivation": random.randint(50, 150)},
                    "tags": ["practice", "nascent_soul"],
                    "event_type": "normal",
                    "duration": dur,
                })
                idx += 1
                if idx - 14000 >= 600:
                    break
            if idx - 14000 >= 600:
                break
        if idx - 14000 >= 600:
            break

    # Fortune (15%)
    fortune_ns = [
        "你在{location}深处找到了{treasure}",
        "一位化神前辈传你{technique}不传之秘",
        "你的元婴突然顿悟，修为暴涨",
        "你在虚空中偶遇一缕鸿蒙之气",
        "你解开了一处太古禁制，内有逆天造化",
        "你在混沌深处找到了{treasure}",
        "天地赐福，{element}法则主动向你靠近",
    ]
    for tmpl in fortune_ns:
        for i in range(32):
            text = tmpl.format(
                location=random.choice(LOCATIONS[4:]),
                treasure=random.choice(TREASURES[5:]),
                technique=random.choice(TECHNIQUES),
                element=random.choice(ELEMENTS),
            )
            events.append({
                "id": _id("ns_fort", idx), "text": text, "expanded_text": text,
                "category": "fortune",
                "conditions": {"min_realm": 4, "max_realm": 5},
                "weight": 20,
                "effects": {"cultivation": random.randint(80, 200), "fortune": random.choice([0, 1])},
                "tags": ["fortune", "nascent_soul"], "event_type": "fortune",
                "duration": random.choice([0, 0, 3, 5]),
            })
            idx += 1

    # Calamity (15%)
    calamity_ns = [
        "你渡小天劫时受了重伤",
        "你遭遇元婴期大敌的追杀",
        "你的元婴被一股神秘力量侵蚀",
        "修炼{technique}大神通时走火入魔",
        "你在{location}陷入时空乱流",
        "心魔化形与你在识海中大战",
        "你被一位化神修士盯上",
        "你触犯了某处远古禁忌",
    ]
    for tmpl in calamity_ns:
        for i in range(28):
            text = tmpl.format(
                technique=random.choice(TECHNIQUES),
                location=random.choice(LOCATIONS[4:]),
            )
            events.append({
                "id": _id("ns_cala", idx), "text": text, "expanded_text": text,
                "category": "calamity",
                "conditions": {"min_realm": 4, "max_realm": 5},
                "weight": 20,
                "effects": {"constitution": random.choice([-1, -2, 0]), "willpower": random.choice([0, 0, 1])},
                "tags": ["calamity", "nascent_soul"], "event_type": "danger",
            })
            idx += 1

    # Social (15%)
    social_ns = [
        "你参加元婴级别的修士大会",
        "你被多个宗门争相邀请为客卿",
        "你与一位元婴老怪论道三日",
        "你以元婴修为主持宗门大事",
        "你收了一位金丹弟子传授衣钵",
        "你被推举为宗门护法长老",
        "你与同辈修士探讨化神之路",
        "修真界各方势力拉拢于你",
    ]
    for tmpl in social_ns:
        for i in range(28):
            events.append({
                "id": _id("ns_soc", idx), "text": tmpl, "expanded_text": tmpl,
                "category": "social",
                "conditions": {"min_realm": 4, "max_realm": 5},
                "weight": 25,
                "effects": {"cultivation": random.randint(10, 30), "charisma": random.choice([0, 1])},
                "tags": ["social", "nascent_soul"], "event_type": "normal",
            })
            idx += 1

    # World + Philosophy
    for i in range(50):
        world_text = random.choice([
            "修真界发生了一件惊天大事",
            f"一位元婴大修在{random.choice(LOCATIONS)}陨落",
            "天地法则波动，预示大变将至",
            f"{random.choice(ELEMENTS)}属天劫异象频现",
            "上古大能留下的预言开始应验",
        ])
        events.append({
            "id": _id("ns_world", idx), "text": world_text, "expanded_text": world_text,
            "category": "world",
            "conditions": {"min_realm": 4, "max_realm": 5},
            "weight": 15, "effects": {},
            "tags": ["world", "nascent_soul"], "event_type": "normal",
        })
        idx += 1

    for ins in INSIGHTS:
        for suffix in ["有了深刻感悟", "似乎近在咫尺", "的门槛若隐若现"]:
            text = f"你对{ins}{suffix}"
            events.append({
                "id": _id("ns_phil", idx), "text": text, "expanded_text": text,
                "category": "cultivation",
                "conditions": {"min_realm": 4, "max_realm": 5},
                "weight": 20,
                "effects": {"willpower": 1, "comprehension": random.choice([0, 1])},
                "tags": ["philosophy", "nascent_soul"], "event_type": "normal",
            })
            idx += 1

    return events


# ─── Deity Events (realm 5) ──────────────────────────────────────────

def generate_deity_events() -> List[Dict]:
    """Generate ~1200 Deity (化神) events."""
    events = []
    idx = 18000

    # Cultivation (40%) - extremely long durations
    cult_templates = [
        "你闭关感悟天地本源，化神之力愈发精纯",
        "你以化神之力炼化{treasure}，实力暴涨",
        "你参悟{element}大道本源",
        "你修炼{technique}至巅峰境界",
        "你在{location}中与天地共鸣",
        "你凝练化神之力，探索飞升之路",
        "你以化神神念笼罩千里，感悟天地运转",
        "你尝试触碰仙界法则",
        "你修炼逆天{technique}神通",
        "你体悟{element}本源，法则之力为你所用",
        "你在闭关中隐约感应到仙界的气息",
        "你凝聚{element}领域至大成",
    ]

    durations_deity = [5, 10, 15, 20, 30, 50]
    for tmpl in cult_templates:
        for tech in TECHNIQUES:
            for elem in ELEMENTS[:5]:
                text = tmpl.format(
                    technique=tech, element=elem,
                    location=random.choice(LOCATIONS[6:]),
                    treasure=random.choice(TREASURES[6:]),
                )
                dur = random.choice(durations_deity)
                events.append({
                    "id": _id("deity_cult", idx), "text": text, "expanded_text": text,
                    "category": "cultivation",
                    "conditions": {"min_realm": 5},
                    "weight": 50,
                    "effects": {"cultivation": random.randint(100, 400)},
                    "tags": ["practice", "high_realm"],
                    "event_type": "normal",
                    "duration": dur,
                })
                idx += 1
                if idx - 18000 >= 480:
                    break
            if idx - 18000 >= 480:
                break
        if idx - 18000 >= 480:
            break

    # Fortune (15%)
    fortune_deity = [
        "你在虚空中发现了通往仙界的线索",
        "你获得了{treasure}，这是渡劫飞升的关键材料",
        "一位飞升前辈托梦传你渡劫心法",
        "你在{location}中感应到空间节点的气息",
        "天地法则向你示好，修为暴涨",
        "你参悟了{element}大道至理",
        "一缕仙界灵气降临于你",
    ]
    for tmpl in fortune_deity:
        for i in range(26):
            text = tmpl.format(
                treasure=random.choice(TREASURES[8:]),
                location=random.choice(LOCATIONS[8:]),
                element=random.choice(ELEMENTS),
            )
            events.append({
                "id": _id("deity_fort", idx), "text": text, "expanded_text": text,
                "category": "fortune",
                "conditions": {"min_realm": 5},
                "weight": 15,
                "effects": {"cultivation": random.randint(200, 600)},
                "tags": ["fortune", "high_realm"], "event_type": "fortune",
                "duration": random.choice([0, 5, 10]),
            })
            idx += 1

    # Calamity (15%)
    calamity_deity = [
        "天劫提前降临的预兆让你心惊",
        "你遭遇化神级大敌的偷袭",
        "修炼逆天功法引来天罚",
        "你的化神之体出现了裂痕",
        "一位老对头趁你闭关时设下杀阵",
        "你在参悟法则时触动了天道禁忌",
        "魔道化神修士向你发起挑战",
        "你在{location}遭遇空间坍塌",
    ]
    for tmpl in calamity_deity:
        for i in range(22):
            text = tmpl.format(location=random.choice(LOCATIONS[6:]))
            events.append({
                "id": _id("deity_cala", idx), "text": text, "expanded_text": text,
                "category": "calamity",
                "conditions": {"min_realm": 5},
                "weight": 20,
                "effects": {"constitution": random.choice([-1, -2, 0]), "willpower": random.choice([0, 1, 1])},
                "tags": ["calamity", "high_realm"], "event_type": "danger",
            })
            idx += 1

    # Social (15%)
    social_deity = [
        "你参加化神级别的绝顶强者会议",
        "多个宗门恳请你出任太上长老",
        "你与另一位化神大能论道百年",
        "你被整个修真界视为传奇",
        "你指点后辈修炼，留下一段佳话",
        "你以化神之威平息了一场宗门大战",
        "一位远古化神苏醒，邀你共探飞升之路",
        "你主持修真界百年一度的大会",
    ]
    for tmpl in social_deity:
        for i in range(22):
            events.append({
                "id": _id("deity_soc", idx), "text": tmpl, "expanded_text": tmpl,
                "category": "social",
                "conditions": {"min_realm": 5},
                "weight": 20,
                "effects": {"cultivation": random.randint(30, 80)},
                "tags": ["social", "high_realm"], "event_type": "normal",
                "duration": random.choice([0, 5, 10]),
            })
            idx += 1

    # World + Philosophy for deity
    deity_world = [
        "天地法则剧变，大劫将至的预兆",
        "修真界格局因你而改变",
        "仙界有人传信至凡间",
        "一处远古仙人遗迹浮出水面",
        "天地灵气浓度在你周围急剧攀升",
    ]
    for tmpl in deity_world:
        for i in range(12):
            events.append({
                "id": _id("deity_world", idx), "text": tmpl, "expanded_text": tmpl,
                "category": "world", "conditions": {"min_realm": 5},
                "weight": 15, "effects": {},
                "tags": ["world", "high_realm"], "event_type": "normal",
            })
            idx += 1

    for ins in INSIGHTS:
        for prefix in ["你参透了", "你与天道共鸣感悟", "化神巅峰的你领悟了"]:
            text = f"{prefix}{ins}的终极奥义"
            events.append({
                "id": _id("deity_phil", idx), "text": text, "expanded_text": text,
                "category": "cultivation",
                "conditions": {"min_realm": 5},
                "weight": 20,
                "effects": {"willpower": 1, "comprehension": 1, "cultivation": random.randint(50, 100)},
                "tags": ["philosophy", "high_realm"], "event_type": "normal",
            })
            idx += 1

    return events


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    """Generate all events and merge with existing all_events.json."""
    print("Generating events...")

    all_new = []
    all_new.extend(generate_mortal_events())
    print(f"  Mortal: {len(all_new)} events")

    qi_events = generate_qi_refining_events()
    all_new.extend(qi_events)
    print(f"  Qi Refining: {len(qi_events)} events (total: {len(all_new)})")

    found_events = generate_foundation_events()
    all_new.extend(found_events)
    print(f"  Foundation: {len(found_events)} events (total: {len(all_new)})")

    gc_events = generate_golden_core_events()
    all_new.extend(gc_events)
    print(f"  Golden Core: {len(gc_events)} events (total: {len(all_new)})")

    ns_events = generate_nascent_soul_events()
    all_new.extend(ns_events)
    print(f"  Nascent Soul: {len(ns_events)} events (total: {len(all_new)})")

    deity_events = generate_deity_events()
    all_new.extend(deity_events)
    print(f"  Deity: {len(deity_events)} events (total: {len(all_new)})")

    # Load existing events
    existing_path = os.path.join(OUTPUT_DIR, "all_events.json")
    existing = []
    if os.path.exists(existing_path):
        with open(existing_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        print(f"\nExisting events: {len(existing)}")

    # Merge
    merged = existing + all_new
    print(f"Total after merge: {len(merged)}")

    # Write
    with open(existing_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Written to {existing_path}")

    # Stats
    realm_counts = {}
    for e in merged:
        mr = e.get("conditions", {}).get("min_realm", 0)
        realm_counts[mr] = realm_counts.get(mr, 0) + 1
    print("\nFinal distribution by min_realm:")
    for r in sorted(realm_counts.keys()):
        print(f"  Realm {r}: {realm_counts[r]}")


if __name__ == "__main__":
    main()
