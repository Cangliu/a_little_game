"""NPC name pools and personality templates.

Provides cultivation-themed Chinese names and personality-specific
behavior descriptions for NPC generation.
"""
from __future__ import annotations

import random
from typing import Optional

# ─── Name Pools ───────────────────────────────────────────────────────

MALE_SURNAMES = [
    "陈", "林", "张", "李", "王", "赵", "刘", "杨", "周", "吴",
    "孙", "萧", "叶", "顾", "韩", "唐", "沈", "宋", "郑", "冯",
    "魏", "褚", "卫", "蒋", "许", "何", "吕", "施", "姜", "秦",
    "方", "石", "谢", "邹", "薛", "程", "任", "邓", "龙", "傅",
    # 复姓
    "慕容", "司马", "上官", "欧阳", "长孙", "独孤", "公孙", "端木",
    "轩辕", "南宫", "百里", "东方", "诸葛", "令狐", "宇文", "尉迟",
    "皇甫", "夏侯", "司徒", "纳兰",
]

MALE_GIVEN_NAMES = [
    # 单字名
    "逸", "玄", "辰", "渊", "墨", "尘", "风", "寒", "烨", "昊",
    "霖", "轩", "泽", "宇", "修", "凌", "峰", "云", "天", "明",
    "远", "道", "清", "澈", "玉", "瑾", "瑜", "煜", "旭", "阳",
    "衡", "策", "奕", "翊", "珩", "璟", "晏", "瀚", "岳", "铮",
    "焱", "曜", "麟", "鹤", "枫", "霆", "骁", "铭", "彦", "恒",
    # 双字名
    "无极", "长青", "九霄", "天行", "云深", "不器", "如是", "问道",
    "归元", "守一", "承志", "弘毅", "致远", "思源", "若虚", "怀真",
    "凌霄", "破军", "惊蛰", "望舒", "扶摇", "沧海", "横渠", "浮生",
    "千机", "流光", "玄霜", "镇岳", "御风", "逐日", "乘黄", "拂晓",
    "临渊", "踏雪", "惊鸿", "倾川", "长歌", "断云", "擎苍", "执明",
    "听潮", "看山", "栖霞", "知秋", "映川", "入尘", "渡风", "揽星",
]

FEMALE_SURNAMES = [
    "柳", "苏", "沈", "谢", "秦", "楚", "卫", "花", "慕", "凤",
    "陈", "林", "张", "李", "王", "赵", "萧", "叶", "顾", "唐",
    "韩", "宋", "白", "纪", "温", "容", "殷", "颜", "洛", "裴",
    "程", "薛", "方", "蓝", "姬", "姜", "云", "风", "莫", "夜",
    # 复姓
    "上官", "南宫", "百里", "东方", "公孙", "端木", "独孤", "长孙",
    "慕容", "欧阳", "令狐", "皇甫", "夏侯", "纳兰", "司徒", "轩辕",
]

FEMALE_GIVEN_NAMES = [
    "如烟", "若兰", "紫萱", "清雪", "月华", "灵犀", "婉清", "素心",
    "凝霜", "飞雪", "幽兰", "碧落", "芷若", "冰心", "瑶光", "锦书",
    "倾城", "无双", "霓裳", "云裳", "梦蝶", "惊鸿", "落霞", "朝露",
    "琉璃", "玲珑", "含烟", "映雪", "听雨", "望月", "怜星", "寻梅",
    "念卿", "思归", "忆仙", "怀瑾", "问琴", "抚剑", "弄影", "踏歌",
    "挽星", "揽月", "乘风", "凝香", "浣纱", "采薇", "折花", "拾翠",
    "明珠", "暗香", "疏影", "流萤", "浮光", "清辉", "漱玉", "衔烛",
    "九歌", "离骚", "湘灵", "洛神", "青鸾", "白凤", "丹鹤", "紫燕",
    "初雪", "晚晴", "长宁", "安歌", "知音", "解语", "画眉", "点绛",
    "栖迟", "徘徊", "缥缈", "逍遥", "扶风", "入梦", "枕霞", "卧云",
]

# ─── Personality Templates ────────────────────────────────────────────

PERSONALITY_DESCRIPTIONS = {
    "温和": {
        "speech_style": "语气平和，措辞温柔，常以微笑示人",
        "behavior": "乐于助人，遇事多为他人考虑",
        "conflict_style": "倾向于调和矛盾，避免正面冲突",
    },
    "冷漠": {
        "speech_style": "言简意赅，表情淡然，不喜寒暄",
        "behavior": "独来独往，不愿被打扰",
        "conflict_style": "冷眼旁观，除非触及底线否则不出手",
    },
    "狡诈": {
        "speech_style": "话中有话，善于引导对方暴露弱点",
        "behavior": "表面热情实则盘算利弊",
        "conflict_style": "避免正面交锋，擅长借刀杀人",
    },
    "正直": {
        "speech_style": "直言不讳，嫉恶如仇，言出必行",
        "behavior": "路见不平拔刀相助，重诺守信",
        "conflict_style": "堂堂正正，即便实力不济也不屑暗算",
    },
    "神秘": {
        "speech_style": "话语含糊，常用隐喻，令人捉摸不透",
        "behavior": "行踪不定，偶尔出现指点迷津",
        "conflict_style": "来去无踪，不与人正面为敌",
    },
    "暴烈": {
        "speech_style": "大嗓门，喜怒形于色，不耐繁文缛节",
        "behavior": "行事雷厉风行，遇到看不惯的直接动手",
        "conflict_style": "先打后问，拳头就是道理",
    },
}

# ─── Role-specific backstory templates ────────────────────────────────

ROLE_BACKSTORIES = {
    "sword_master": [
        "年少时为剑道天才，曾以一剑破万法",
        "出身剑阁，修习上古剑诀",
        "孤身仗剑行走天下三百年的散修",
    ],
    "alchemy_elder": [
        "精通丹道，炼制的筑基丹名满修真界",
        "出身丹鼎派，师承上古药王一脉",
        "曾因炼丹走火入魔，大彻大悟后丹道更精",
    ],
    "sect_leader": [
        "白手起家创建宗门，威震一方",
        "世家子弟继承宗主之位，肩负宗门兴衰",
        "废材逆袭成为宗门掌门的传奇人物",
    ],
    "wanderer": [
        "不愿受宗门束缚的自由散修",
        "曾是某宗内门弟子，因故离开独自修行",
        "天生野性，以天地为家的流浪修士",
    ],
    "merchant": [
        "行走于各修真城市的灵材商人",
        "坊市大掌柜，消息灵通人脉广博",
        "以商入道的奇人，修为深不可测",
    ],
    "mysterious_elder": [
        "真实身份不明，偶尔出没于各大秘境",
        "据说已活了上千年的老怪物",
        "面容永远不老的神秘前辈",
    ],
}

# Default backstories for roles without templates
DEFAULT_BACKSTORIES = [
    "修真界的普通修士，有着自己的故事",
    "在这方天地间寻找自己道路的修行者",
    "曾经历过生死劫难的修仙者",
]


# ─── Helper Functions ─────────────────────────────────────────────────

def generate_name(gender: str = "male") -> str:
    """Generate a random cultivation-style name."""
    if gender == "female":
        surname = random.choice(FEMALE_SURNAMES)
        given = random.choice(FEMALE_GIVEN_NAMES)
    else:
        surname = random.choice(MALE_SURNAMES)
        given = random.choice(MALE_GIVEN_NAMES)
    return f"{surname}{given}"


def get_backstory(role_tags: list, personality: str = "") -> str:
    """Generate a one-line backstory based on role tags."""
    for tag in role_tags:
        if tag in ROLE_BACKSTORIES:
            return random.choice(ROLE_BACKSTORIES[tag])
    return random.choice(DEFAULT_BACKSTORIES)


def get_personality_desc(personality: str) -> dict:
    """Get the description template for a personality type."""
    return PERSONALITY_DESCRIPTIONS.get(personality, PERSONALITY_DESCRIPTIONS["温和"])
