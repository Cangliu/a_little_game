"""Sect data models — independent sect strategy system.

Defines core data structures for the cultivation sect system:
- Sect types (sword, alchemy, formation, body, spirit, demon)
- Player rank within a sect
- Inter-sect relations
- Resource management
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class SectType(str, Enum):
    """Types of cultivation sects."""
    SWORD = "剑宗"
    ALCHEMY = "丹宗"
    FORMATION = "阵宗"
    BODY = "体修宗"
    SPIRIT = "灵宗"
    DEMON = "魔宗"


class SectRank(str, Enum):
    """Player rank within a sect (ascending order)."""
    OUTER_DISCIPLE = "外门弟子"
    INNER_DISCIPLE = "内门弟子"
    CORE_DISCIPLE = "核心弟子"
    ELDER = "长老"
    GRAND_ELDER = "大长老"
    SECT_MASTER = "掌门"


# Rank ordering for promotion checks
RANK_ORDER = [
    SectRank.OUTER_DISCIPLE,
    SectRank.INNER_DISCIPLE,
    SectRank.CORE_DISCIPLE,
    SectRank.ELDER,
    SectRank.GRAND_ELDER,
    SectRank.SECT_MASTER,
]

# Promotion requirements: {rank: (min_contribution, min_reputation, min_realm)}
RANK_PROMOTION_REQS = {
    SectRank.INNER_DISCIPLE: (50, 40, 1),    # 练气+贡献50+声望40
    SectRank.CORE_DISCIPLE: (200, 60, 2),    # 筑基+贡献200+声望60
    SectRank.ELDER: (500, 75, 3),            # 金丹+贡献500+声望75
    SectRank.GRAND_ELDER: (1200, 85, 4),     # 元婴+贡献1200+声望85
    SectRank.SECT_MASTER: (3000, 95, 5),     # 化神+贡献3000+声望95
}


class SectRelationType(str, Enum):
    """Inter-sect relation types."""
    ALLY = "联盟"
    NEUTRAL = "中立"
    RIVAL = "竞争"
    HOSTILE = "敌对"


class SectResources(BaseModel):
    """Resource pool for a sect."""
    spirit_stones: int = 500          # 灵石储备
    spirit_veins: int = 1             # 灵脉数量 (affects cultivation speed)
    artifacts: list[str] = []         # 宗门宝物名称列表
    formations: list[str] = []        # 护山大阵列表
    monthly_income: int = 50          # 每回合灵石收入


class Sect(BaseModel):
    """A cultivation sect in the game world."""
    sect_id: str
    name: str
    sect_type: str                    # SectType value
    tier: int = 3                     # 1-5 (1=小门派, 5=仙门)
    reputation: int = 500             # 0-1000 宗门声望
    disciples_count: int = 100        # 弟子总数
    territory: str = ""               # 地盘描述
    specialization: str = ""          # 特色 (独门功法/独家丹方等)
    founding_story: str = ""          # 宗门典故
    resources: SectResources = SectResources()
    sect_master_name: str = ""        # 掌门名字
    is_destroyed: bool = False        # 是否已灭门


class SectMembership(BaseModel):
    """Player's membership within a sect."""
    sect_id: str
    rank: str = SectRank.OUTER_DISCIPLE.value
    contribution: int = 0             # 累计贡献值
    reputation_in_sect: int = 50      # 宗门内声望 (0-100)
    join_age: int = 0                 # 加入时年龄
    missions_completed: int = 0       # 完成任务数
    last_mission_age: int = 0         # 上次任务时年龄


class SectRelation(BaseModel):
    """Relationship between two sects."""
    sect_a_id: str
    sect_b_id: str
    relation_type: str = SectRelationType.NEUTRAL.value
    tension: int = 50                 # 0-100, higher = more strained
