"""NPC data models — entity and relationship definitions.

Provides structured types for NPCs, their personalities, and
their relationships with the player character.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class NPCPersonality(str, Enum):
    """NPC personality archetypes affecting dialogue and behavior (18 types)."""
    WARM = "温和"
    COLD = "冷漠"
    CUNNING = "狡诈"
    RIGHTEOUS = "正直"
    MYSTERIOUS = "神秘"
    FIERCE = "暴烈"
    CAREFREE = "洒脱"
    GLOOMY = "阴沉"
    ARROGANT = "傲慢"
    LOYAL = "忠厚"
    PARANOID = "多疑"
    COMPASSIONATE = "慈悲"
    OBSESSIVE = "执着"
    ELEGANT = "风雅"
    RUTHLESS = "狠辣"
    NAIVE = "天真"
    DEFIANT = "桀骜"
    DEEP = "深沉"


class RelationType(str, Enum):
    """Types of relationships between NPC and player."""
    MASTER = "师父"
    DISCIPLE = "徒弟"
    FELLOW = "同门"
    FRIEND = "挚友"
    RIVAL = "宿敌"
    LOVER = "道侣"
    BENEFACTOR = "恩人"
    ENEMY = "仇人"
    ACQUAINTANCE = "泛泛之交"


# Relationship types that imply positive sentiment
POSITIVE_RELATIONS = {
    RelationType.MASTER, RelationType.DISCIPLE, RelationType.FELLOW,
    RelationType.FRIEND, RelationType.LOVER, RelationType.BENEFACTOR,
}

# Relationship types that imply negative sentiment
NEGATIVE_RELATIONS = {
    RelationType.RIVAL, RelationType.ENEMY,
}


class NPC(BaseModel):
    """A persistent NPC entity in the game world."""
    npc_id: str
    name: str
    gender: str  # "male" / "female"
    realm: int = 0  # NPC's cultivation realm
    personality: str = NPCPersonality.WARM.value
    role_tags: list = []  # e.g. ["sword_master", "alchemy_elder"]
    first_met_age: int = 0
    last_seen_age: int = 0
    appearance_count: int = 0
    is_alive: bool = True
    backstory: str = ""  # One-line backstory for AI reference
    max_age: int = 80  # NPC lifespan (based on realm)
    # Destiny system (独立命运线)
    destiny_beats: list = []         # NPC命运节拍 (from npc_destiny templates)
    current_destiny_index: int = 0   # 当前节拍索引
    destiny_completed: bool = False  # 命运线是否已完成
    # 人格深度字段 (Task 8)
    motivation: str = ""             # 核心动机 ("追求剑道极致" / "守护宗门安宁")
    secret: str = ""                 # 隐藏秘密 ("实为魔修后裔" / "暗恋主角多年")
    growth_arc: str = ""             # 成长方向 ("从冷漠到温情" / "从正直到堕落")
    betrayal_threshold: int = -1     # 背叛触发条件 (好感度降至此值以下可能背叛, -1=不会背叛)
    age_offset: int = 30             # 初次相遇时NPC比玩家大的估算年数 (生成时固定)


class NPCInteraction(BaseModel):
    """A single recorded interaction between NPC and player."""
    age: int                            # Player age when interaction happened
    event_text: str = ""                # Brief event description (<60 chars)
    sentiment_delta: int = 0            # Sentiment change from this interaction
    consequence: str = ""               # Unresolved consequence, if any
    resolved: bool = True               # Whether consequence was resolved


class Relationship(BaseModel):
    """Tracks the relationship between an NPC and the player."""
    npc_id: str
    relation_type: str = RelationType.ACQUAINTANCE.value
    sentiment: int = 0  # -100~100, 0 = neutral, positive=友好, negative=敌对
    last_interaction_age: int = 0
    interaction_count: int = 0
    key_memory: str = ""  # Most important interaction summary
    interactions: list = []             # Full interaction history (list of NPCInteraction dicts)
    unresolved_hooks: list = []         # Unresolved plot hook IDs tied to this NPC
