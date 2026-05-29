"""Data models for the cultivation life simulator."""
from pydantic import BaseModel
from typing import Optional
from enum import IntEnum


class Realm(IntEnum):
    """Cultivation realms - 修炼境界 (化神为修为顶峰; 飞升不是境界, 而是渡劫飞升的结局)"""
    MORTAL = 0        # 凡人
    QI_REFINING = 1   # 练气
    FOUNDATION = 2    # 筑基
    GOLDEN_CORE = 3   # 金丹
    NASCENT_SOUL = 4  # 元婴
    DEITY = 5         # 化神 (修为顶峰)


MAX_REALM = int(Realm.DEITY)  # 化神为修为顶峰; 之上需通过渡劫飞升离开此方天地


REALM_NAMES = {
    Realm.MORTAL: "凡人",
    Realm.QI_REFINING: "练气",
    Realm.FOUNDATION: "筑基",
    Realm.GOLDEN_CORE: "金丹",
    Realm.NASCENT_SOUL: "元婴",
    Realm.DEITY: "化神",
}

REALM_MAX_AGE = {
    Realm.MORTAL: 80,
    Realm.QI_REFINING: 150,
    Realm.FOUNDATION: 300,
    Realm.GOLDEN_CORE: 600,
    Realm.NASCENT_SOUL: 1200,
    Realm.DEITY: 1500,  # 化神顶峰寿元; 远超元婴但终有尽头, 若未渡劫飞升, 则困死于此方天地
}


class Attributes(BaseModel):
    """Player attributes - 六维属性"""
    lifespan: int = 3       # 寿元 - base max age modifier
    constitution: int = 3   # 根骨 - body talent
    comprehension: int = 3  # 悟性 - learning speed
    fortune: int = 3        # 福缘 - luck
    charisma: int = 3       # 魅力 - social
    willpower: int = 3      # 心性 - tribulation resist


class Talent(BaseModel):
    """A talent/trait the player can pick"""
    id: str
    name: str
    description: str
    rarity: int  # 1=common, 2=rare, 3=epic, 4=legendary
    effects: dict = {}
    tags: list[str] = []


class EventCondition(BaseModel):
    """Conditions for an event to trigger"""
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    min_realm: Optional[int] = None
    max_realm: Optional[int] = None
    min_cultivation: Optional[int] = None
    required_talents: list[str] = []
    required_tags: list[str] = []
    excluded_tags: list[str] = []
    min_attribute: Optional[dict] = None
    gender: Optional[str] = None  # 'male' / 'female' / None (any)


class EventEffect(BaseModel):
    """Effects when an event triggers"""
    cultivation: Optional[int] = None
    lifespan: Optional[int] = None
    constitution: Optional[int] = None
    comprehension: Optional[int] = None
    fortune: Optional[int] = None
    charisma: Optional[int] = None
    willpower: Optional[int] = None
    realm_up: Optional[bool] = None
    add_tag: Optional[str] = None
    remove_tag: Optional[str] = None
    death: Optional[bool] = None


class EventBranch(BaseModel):
    """A choice branch within an event"""
    text: str
    effects: EventEffect = EventEffect()
    result_text: str = ""


class GameEvent(BaseModel):
    """A single game event"""
    id: str
    text: str
    category: str
    conditions: EventCondition = EventCondition()
    weight: int = 50
    effects: EventEffect = EventEffect()
    branches: list[EventBranch] = []
    tags: list[str] = []
    event_type: str = "normal"  # normal, important, danger, fortune


class GameState(BaseModel):
    """Current game state"""
    game_id: str
    age: int = 0
    realm: int = 0
    cultivation: int = 0  # Progress to next realm (or post-化神 search progress)
    gender: str = "male"  # 'male' or 'female'
    attributes: Attributes = Attributes()
    talents: list[str] = []
    tags: list[str] = []
    events_log: list[dict] = []
    used_event_ids: list[str] = []  # Dedup: prevent same event firing twice
    mortal_max_age: int = 0  # Random mortal lifespan (50-80), set at game start
    is_dead: bool = False
    death_reason: str = ""
    is_ascended: bool = False
    tribulation_attempted: bool = False  # 是否已尝试渡劫飞升
    space_node_found: bool = False  # 是否已寻得空间节点


class StartGameRequest(BaseModel):
    """Request to start a new game"""
    attributes: Attributes
    talents: list[str]


class NextYearResponse(BaseModel):
    """Response for advancing one year"""
    age: int
    realm: int
    realm_name: str
    cultivation: int
    cultivation_max: int
    events: list[dict]
    attributes: Attributes
    is_dead: bool = False
    death_reason: str = ""
    is_ascended: bool = False
    has_choice: bool = False
    choice_event: Optional[dict] = None
    gender: str = "male"
    space_node_found: bool = False


class ChoiceRequest(BaseModel):
    """Request to make a choice"""
    game_id: str
    event_id: str
    choice_index: int


class LifeSummary(BaseModel):
    """Summary of a completed life"""
    total_age: int
    max_realm: int
    max_realm_name: str
    death_reason: str
    key_events: list[str]
    talents: list[str]
    final_attributes: Attributes
    score: int
    title: str  # Achievement title
    gender: str = "male"
