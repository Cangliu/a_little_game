"""Sect templates — pre-defined sect archetypes for world generation.

Provides 12 sect templates covering 6 SectTypes (剑/丹/阵/体/灵/魔), each with:
- name, sect_type, tier, specialization
- founding_story (one-line lore)
- territory description
- starting resources

The world generator selects 6-8 templates randomly to populate each game.
"""
from __future__ import annotations

import random
from typing import List

from .models import Sect, SectType, SectResources


# ── Sect templates ────────────────────────────────────────────────────────
# Each template: (name, type, tier, territory, specialization, founding_story)
SECT_TEMPLATES: List[dict] = [
    # 剑宗 (Sword)
    {
        "name": "青云剑宗",
        "sect_type": SectType.SWORD.value,
        "tier": 4,
        "territory": "东海青云山",
        "specialization": "御剑术与剑意修行",
        "founding_story": "上古剑仙青云子斩妖于此，留下御剑传承，弟子皆以剑为伴。",
    },
    {
        "name": "万剑山庄",
        "sect_type": SectType.SWORD.value,
        "tier": 3,
        "territory": "西陲万剑岭",
        "specialization": "百炼剑器与剑阵",
        "founding_story": "山庄主人遍访名山，铸万剑封印魔头，立庄镇守。",
    },

    # 丹宗 (Alchemy)
    {
        "name": "太乙丹宗",
        "sect_type": SectType.ALCHEMY.value,
        "tier": 4,
        "territory": "南岭灵药谷",
        "specialization": "炼丹与药理",
        "founding_story": "太乙真人于此谷中炼出九转还魂丹，从此弟子满堂。",
    },
    {
        "name": "百草堂",
        "sect_type": SectType.ALCHEMY.value,
        "tier": 2,
        "territory": "北原药王峰",
        "specialization": "灵草培育与丹方研究",
        "founding_story": "前朝御医谪隐于此，建堂传医道丹法，惠及四方。",
    },

    # 阵宗 (Formation)
    {
        "name": "天机阵宗",
        "sect_type": SectType.FORMATION.value,
        "tier": 4,
        "territory": "北漠天机城",
        "specialization": "大阵布设与机关之道",
        "founding_story": "天机老人参悟周天星辰，立宗传授阵道机关，自此阵法甲于天下。",
    },
    {
        "name": "玄机门",
        "sect_type": SectType.FORMATION.value,
        "tier": 3,
        "territory": "中州玄机岛",
        "specialization": "幻阵与禁制",
        "founding_story": "玄机门主善于以幻阵藏匿宝藏，门派出入皆需破阵方可寻得。",
    },

    # 体修宗 (Body)
    {
        "name": "金刚体修门",
        "sect_type": SectType.BODY.value,
        "tier": 3,
        "territory": "西域金刚山",
        "specialization": "肉身锤炼与不灭体魄",
        "founding_story": "金刚祖师以血肉之躯硬撼天劫，立门传体修，号称万法不侵。",
    },
    {
        "name": "巨灵宗",
        "sect_type": SectType.BODY.value,
        "tier": 3,
        "territory": "南荒巨灵谷",
        "specialization": "蛮力与巨灵血脉",
        "founding_story": "上古巨灵神族遗脉，弟子血脉雄浑，一拳碎山。",
    },

    # 灵宗 (Spirit)
    {
        "name": "灵虚宫",
        "sect_type": SectType.SPIRIT.value,
        "tier": 5,
        "territory": "中州灵虚峰",
        "specialization": "神识修行与心法奥妙",
        "founding_story": "灵虚仙子以一念证道，于灵虚峰立宫，专修神识与道心。",
    },
    {
        "name": "云霄阁",
        "sect_type": SectType.SPIRIT.value,
        "tier": 3,
        "territory": "东岭云霄之巅",
        "specialization": "御风之术与轻灵身法",
        "founding_story": "云霄阁主一袭青衫，乘风而行，以身法之妙立阁授徒。",
    },

    # 魔宗 (Demon)
    {
        "name": "幽冥魔宗",
        "sect_type": SectType.DEMON.value,
        "tier": 4,
        "territory": "幽冥之地",
        "specialization": "魔功与噬魂之术",
        "founding_story": "古魔陨落前以残魂立宗，弟子皆食人精气，正道视为大敌。",
    },
    {
        "name": "血煞门",
        "sect_type": SectType.DEMON.value,
        "tier": 2,
        "territory": "血煞荒原",
        "specialization": "血祭与魔兵铸造",
        "founding_story": "门主以万人血祭炼成魔兵，立门于荒原，行事狠辣。",
    },
]


# Sect master name pool (kept simple, gendered hints)
_SECT_MASTER_NAMES = [
    "玄真子", "云无涯", "凌寒霜", "墨白衣", "司徒清玄",
    "上官无极", "百里千寻", "南宫煊", "苏离", "秦九霄",
    "诸葛玄机", "欧阳追日", "公孙明月", "左丘尘", "西门吹影",
]


def generate_world_sects(num_sects: int = 7) -> list[dict]:
    """Generate a random world population of sects.

    Args:
        num_sects: How many sects to populate (default 7, range 6-9 reasonable)

    Returns:
        List of Sect dicts (model_dump format) ready to inject into state.
    """
    num_sects = max(4, min(num_sects, len(SECT_TEMPLATES)))
    selected = random.sample(SECT_TEMPLATES, num_sects)

    sects: list[dict] = []
    for i, tpl in enumerate(selected):
        sect_id = f"sect_{i:02d}_{tpl['sect_type'][:2]}"
        # Tier influences resources
        tier = tpl["tier"]
        resources = SectResources(
            spirit_stones=500 * tier + random.randint(-100, 100),
            spirit_veins=max(1, tier - 1),
            artifacts=[],  # Could be populated later
            formations=[],
            monthly_income=30 * tier + random.randint(-10, 10),
        )
        sect = Sect(
            sect_id=sect_id,
            name=tpl["name"],
            sect_type=tpl["sect_type"],
            tier=tier,
            reputation=200 + tier * 100 + random.randint(-50, 50),
            disciples_count=50 * tier + random.randint(-20, 30),
            territory=tpl["territory"],
            specialization=tpl["specialization"],
            founding_story=tpl["founding_story"],
            resources=resources,
            sect_master_name=random.choice(_SECT_MASTER_NAMES),
        )
        sects.append(sect.model_dump())

    return sects


def generate_initial_relations(sects: list[dict]) -> list[dict]:
    """Generate inter-sect relations matrix at world creation.

    For each pair, randomly assign a relation type based on sect type compatibility:
    - Demon vs non-demon: tend to hostile/rival
    - Same type: tend to rival
    - Different non-demon types: tend to neutral, may be ally
    """
    from .models import SectRelation, SectRelationType

    relations: list[dict] = []
    sect_ids = [s["sect_id"] for s in sects]
    sect_types = {s["sect_id"]: s["sect_type"] for s in sects}

    for i, sa in enumerate(sect_ids):
        for sb in sect_ids[i + 1:]:
            ta = sect_types[sa]
            tb = sect_types[sb]
            is_demon_a = ta == SectType.DEMON.value
            is_demon_b = tb == SectType.DEMON.value

            if is_demon_a != is_demon_b:
                # 正魔对立
                rel = random.choices(
                    [SectRelationType.HOSTILE.value, SectRelationType.RIVAL.value],
                    weights=[70, 30],
                )[0]
                tension = random.randint(70, 95)
            elif ta == tb:
                # 同类型: 多为竞争关系
                rel = random.choices(
                    [SectRelationType.RIVAL.value, SectRelationType.NEUTRAL.value],
                    weights=[60, 40],
                )[0]
                tension = random.randint(50, 75)
            else:
                # 不同正派
                rel = random.choices(
                    [SectRelationType.NEUTRAL.value, SectRelationType.ALLY.value, SectRelationType.RIVAL.value],
                    weights=[55, 25, 20],
                )[0]
                tension = random.randint(20, 60)

            relations.append(SectRelation(
                sect_a_id=sa,
                sect_b_id=sb,
                relation_type=rel,
                tension=tension,
            ).model_dump())

    return relations
