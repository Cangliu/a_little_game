"""NPC data models — entity and relationship definitions.

Provides structured types for NPCs, their personalities, and
their relationships with the player character.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class NPCPersonality(str, Enum):
    """NPC personality archetypes affecting dialogue and behavior."""
    WARM = "温和"
    COLD = "冷漠"
    CUNNING = "狡诈"
    RIGHTEOUS = "正直"
    MYSTERIOUS = "神秘"
    FIERCE = "暴烈"


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
    sentiment: int = 50  # 0-100, 50 = neutral
    last_interaction_age: int = 0
    interaction_count: int = 0
    key_memory: str = ""  # Most important interaction summary
    interactions: list = []             # Full interaction history (list of NPCInteraction dicts)
    unresolved_hooks: list = []         # Unresolved plot hook IDs tied to this NPC
