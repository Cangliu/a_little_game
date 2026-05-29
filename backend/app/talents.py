"""Talent definitions for the cultivation life simulator."""

TALENTS = [
    # === LEGENDARY (rarity 4) ===
    {"id": "chaos_body", "name": "混沌体", "description": "天生混沌之体，修炼速度倍增，百毒不侵", "rarity": 4, "effects": {"constitution": 5, "comprehension": 3}, "tags": ["special_body"]},
    {"id": "innate_dao", "name": "先天道体", "description": "与大道亲和，悟性超凡，修炼如饮水", "rarity": 4, "effects": {"comprehension": 6, "fortune": 2}, "tags": ["special_body"]},
    {"id": "immortal_root", "name": "仙灵根", "description": "五行俱全的天灵根，万中无一", "rarity": 4, "effects": {"constitution": 4, "comprehension": 4}, "tags": ["spirit_root", "heavenly_root"]},
    {"id": "destiny_star", "name": "命星护体", "description": "命中注定成就大道，死劫可化险为夷", "rarity": 4, "effects": {"fortune": 6, "willpower": 3}, "tags": ["destiny"]},
    {"id": "reincarnation", "name": "转世大能", "description": "前世为飞升大能，记忆封印于识海深处", "rarity": 4, "effects": {"comprehension": 5, "willpower": 4}, "tags": ["reincarnation"]},

    # === EPIC (rarity 3) ===
    {"id": "fire_root", "name": "火灵根", "description": "先天火灵根，修炼火系功法事半功倍", "rarity": 3, "effects": {"constitution": 3, "comprehension": 2}, "tags": ["spirit_root", "fire"]},
    {"id": "water_root", "name": "水灵根", "description": "先天水灵根，炼丹有天赋", "rarity": 3, "effects": {"constitution": 2, "comprehension": 3}, "tags": ["spirit_root", "water"]},
    {"id": "sword_bone", "name": "剑骨", "description": "天生剑修之骨，与飞剑天然亲和", "rarity": 3, "effects": {"constitution": 3, "willpower": 2}, "tags": ["sword"]},
    {"id": "pill_talent", "name": "丹道奇才", "description": "对丹药有超凡感悟，炼丹成功率极高", "rarity": 3, "effects": {"comprehension": 3, "fortune": 2}, "tags": ["alchemy"]},
    {"id": "beast_affinity", "name": "万兽亲和", "description": "天生亲近灵兽，可驯服凶兽", "rarity": 3, "effects": {"charisma": 3, "fortune": 2}, "tags": ["beast"]},
    {"id": "fortune_child", "name": "天命之子", "description": "气运之子，总能遇到机缘", "rarity": 3, "effects": {"fortune": 5}, "tags": ["destiny"]},
    {"id": "iron_will", "name": "金刚心", "description": "心如磐石，不受心魔侵扰", "rarity": 3, "effects": {"willpower": 5}, "tags": ["mental"]},
    {"id": "ancient_bloodline", "name": "远古血脉", "description": "体内沉睡着远古妖族血脉", "rarity": 3, "effects": {"constitution": 4, "lifespan": 2}, "tags": ["bloodline"]},
    {"id": "divination", "name": "天眼通", "description": "可窥天机一二，趋吉避凶", "rarity": 3, "effects": {"fortune": 3, "comprehension": 2}, "tags": ["divination"]},
    {"id": "charm_body", "name": "魅体", "description": "天生魅力非凡，众人倾慕", "rarity": 3, "effects": {"charisma": 5, "fortune": 1}, "tags": ["charm"]},

    # === RARE (rarity 2) ===
    {"id": "spirit_root", "name": "灵根", "description": "具有灵根，可踏入修仙之途", "rarity": 2, "effects": {"constitution": 2}, "tags": ["spirit_root"]},
    {"id": "strong_body", "name": "天生神力", "description": "力大无穷，体魄强健", "rarity": 2, "effects": {"constitution": 3}, "tags": ["body"]},
    {"id": "quick_learner", "name": "过目不忘", "description": "记忆力超群，过目成诵", "rarity": 2, "effects": {"comprehension": 3}, "tags": ["mental"]},
    {"id": "lucky_star", "name": "福星高照", "description": "运气不错，常有小惊喜", "rarity": 2, "effects": {"fortune": 3}, "tags": ["luck"]},
    {"id": "silver_tongue", "name": "舌灿莲花", "description": "口才极佳，善于交际", "rarity": 2, "effects": {"charisma": 3}, "tags": ["social"]},
    {"id": "meditation", "name": "静心", "description": "心境平和，不易动怒", "rarity": 2, "effects": {"willpower": 3}, "tags": ["mental"]},
    {"id": "longevity", "name": "长寿相", "description": "面相主贵，天生寿命较长", "rarity": 2, "effects": {"lifespan": 4}, "tags": ["lifespan"]},
    {"id": "merchant", "name": "商贾之才", "description": "善于经营，资源不缺", "rarity": 2, "effects": {"fortune": 2, "charisma": 1}, "tags": ["merchant"]},
    {"id": "noble_birth", "name": "世家子弟", "description": "出身修仙世家，资源丰厚", "rarity": 2, "effects": {"fortune": 2, "constitution": 1}, "tags": ["noble"]},
    {"id": "tough_life", "name": "命硬", "description": "大难不死，必有后福", "rarity": 2, "effects": {"lifespan": 2, "willpower": 2}, "tags": ["survival"]},
    {"id": "music_dao", "name": "琴心", "description": "精通音律，以琴入道", "rarity": 2, "effects": {"comprehension": 2, "charisma": 1}, "tags": ["music"]},
    {"id": "array_talent", "name": "阵法天赋", "description": "对阵法有独特理解", "rarity": 2, "effects": {"comprehension": 2, "willpower": 1}, "tags": ["array"]},

    # === COMMON (rarity 1) ===
    {"id": "healthy", "name": "体健", "description": "身体健康，少有疾病", "rarity": 1, "effects": {"constitution": 1, "lifespan": 1}, "tags": ["body"]},
    {"id": "diligent", "name": "勤奋", "description": "刻苦努力，笨鸟先飞", "rarity": 1, "effects": {"comprehension": 1, "willpower": 1}, "tags": ["mental"]},
    {"id": "kind_heart", "name": "善良", "description": "心地善良，有善缘", "rarity": 1, "effects": {"charisma": 1, "fortune": 1}, "tags": ["social"]},
    {"id": "curious", "name": "好奇心", "description": "对万物充满好奇", "rarity": 1, "effects": {"comprehension": 2}, "tags": ["mental"]},
    {"id": "cautious", "name": "谨慎", "description": "行事小心，少犯错误", "rarity": 1, "effects": {"willpower": 2}, "tags": ["mental"]},
    {"id": "brave", "name": "勇敢", "description": "胆大心细，敢于冒险", "rarity": 1, "effects": {"willpower": 1, "fortune": 1}, "tags": ["mental"]},
    {"id": "plain_look", "name": "相貌平平", "description": "长相普通，不引人注目", "rarity": 1, "effects": {"charisma": -1, "willpower": 1}, "tags": ["appearance"]},
    {"id": "stubborn", "name": "固执", "description": "性格固执，不易妥协", "rarity": 1, "effects": {"willpower": 2, "charisma": -1}, "tags": ["mental"]},
    {"id": "foodie", "name": "饕餮", "description": "嗜好美食，体质微增", "rarity": 1, "effects": {"constitution": 1}, "tags": ["food"]},
    {"id": "dreamer", "name": "白日梦", "description": "常做奇怪的梦，偶有灵感", "rarity": 1, "effects": {"comprehension": 1, "fortune": 1}, "tags": ["dream"]},
]


def get_random_talents(count: int = 10) -> list[dict]:
    """Get a random pool of talents weighted by rarity."""
    import random
    
    # Weight by rarity - rarer talents appear less
    weighted_pool = []
    for talent in TALENTS:
        if talent["rarity"] == 1:
            weighted_pool.extend([talent] * 4)
        elif talent["rarity"] == 2:
            weighted_pool.extend([talent] * 3)
        elif talent["rarity"] == 3:
            weighted_pool.extend([talent] * 2)
        elif talent["rarity"] == 4:
            weighted_pool.extend([talent] * 1)
    
    # Pick unique talents
    selected = []
    available = list(TALENTS)
    random.shuffle(available)
    
    # Ensure at least 1 rare+ talent in the pool
    rare_plus = [t for t in available if t["rarity"] >= 3]
    common = [t for t in available if t["rarity"] < 3]
    
    if rare_plus:
        selected.append(random.choice(rare_plus))
    
    remaining = [t for t in available if t not in selected]
    random.shuffle(remaining)
    selected.extend(remaining[:count - len(selected)])
    
    random.shuffle(selected)
    return selected[:count]
