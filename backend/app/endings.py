"""Endings definitions for the cultivation life simulator.

修为体系顶峰为化神 (realm == 5)。化神之上不再有境界, 三种结局:
  1. 飞升成仙   (is_ascended = True)
  2. 渡劫陨落   (is_dead = True, death_reason = "渡劫陨落")
  3. 困死人间   (is_dead = True, death_reason = "困死人间") — 化神顶峰却终生未寻得空间节点
"""

# 凡俗到化神的常规境界称号 (realm 0-5)
REALM_TITLES = [
    {"min_age": 0, "max_age": 1, "max_realm": 0, "title": "夭折婴儿", "score": 1},
    {"min_age": 2, "max_age": 12, "max_realm": 0, "title": "懵懂幼童", "score": 5},
    {"min_age": 13, "max_age": 30, "max_realm": 0, "title": "平凡少年", "score": 10},
    {"min_age": 31, "max_age": 50, "max_realm": 0, "title": "碌碌凡人", "score": 15},
    {"min_age": 51, "max_age": 70, "max_realm": 0, "title": "白发老翁", "score": 20},
    {"min_age": 71, "max_age": 999, "max_realm": 0, "title": "寿终正寝", "score": 25},
    {"min_age": 0, "max_age": 999, "min_realm": 1, "max_realm": 1, "title": "练气散修", "score": 40},
    {"min_age": 0, "max_age": 999, "min_realm": 2, "max_realm": 2, "title": "筑基修士", "score": 80},
    {"min_age": 0, "max_age": 999, "min_realm": 3, "max_realm": 3, "title": "金丹真人", "score": 150},
    {"min_age": 0, "max_age": 999, "min_realm": 4, "max_realm": 4, "title": "元婴老祖", "score": 250},
    {"min_age": 0, "max_age": 999, "min_realm": 5, "max_realm": 5, "title": "化神尊者", "score": 400},
]

# 三种最终结局的特别称号 (覆盖普通境界称号)
ENDING_TITLES = {
    "ascended":      {"title": "飞升仙人", "score": 999},
    "tribulation":   {"title": "渡劫陨仙", "score": 600},  # 渡劫陨落 — 距仙一步之遥
    "trapped":       {"title": "困世化神", "score": 500},  # 困死人间 — 化神顶峰却未得节点
}

DEATH_MESSAGES = {
    "default": "你的一生就此结束。",
    "ascension": "你寻得空间节点，逆渡九重雷劫，飞升而去。从此长生不老，与天地同寿。",
    "tribulation": "九重雷劫过于狂暴，你终究未能踏过那最后一步。空间节点闭合如初，你的修仙之路就此画上句点。",
    "trapped": "你修至化神之巅，却终其一世也未能寻得空间节点。寿元耗尽之时，你只能困死于这一方天地之间。",
    "mortal": "你安详地闭上了眼睛，了无遗憾。",
    "cultivation_death": "你的修仙之路在此终结，但你的传说将被后人铭记。",
}


def _get_realm_title(age: int, realm: int) -> dict:
    """匹配常规境界称号 (用作非特殊结局的 fallback)。"""
    best_title = REALM_TITLES[0]
    best_score = 0

    for t in REALM_TITLES:
        if age < t.get("min_age", 0) or age > t.get("max_age", 99999):
            continue
        if realm < t.get("min_realm", 0) or realm > t.get("max_realm", 99):
            continue
        if t["score"] > best_score:
            best_score = t["score"]
            best_title = t

    return best_title


def get_title(age: int, realm: int, is_ascended: bool = False,
              death_reason: str = "") -> dict:
    """根据年龄、境界、结局类型返回最终称号。

    三种特殊结局会覆盖普通境界称号:
    - 飞升成仙: ENDING_TITLES["ascended"]
    - 渡劫陨落: ENDING_TITLES["tribulation"]
    - 困死人间: ENDING_TITLES["trapped"]
    """
    if is_ascended:
        return ENDING_TITLES["ascended"]
    if death_reason == "渡劫陨落":
        return ENDING_TITLES["tribulation"]
    if death_reason == "困死人间":
        return ENDING_TITLES["trapped"]
    return _get_realm_title(age, realm)


def calculate_score(age: int, realm: int, attributes: dict,
                    is_ascended: bool = False, death_reason: str = "") -> int:
    """根据结局算最终评分。"""
    title = get_title(age, realm, is_ascended=is_ascended, death_reason=death_reason)
    base_score = title["score"]

    attr_bonus = sum(attributes.values()) * 2
    age_bonus = min(age // 10, 50)

    return base_score + attr_bonus + age_bonus
