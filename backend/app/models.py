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
    trigger_event_id: Optional[str] = None  # 事件链: 下一阶段事件ID


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
    used_event_ids: set[str] = set()  # Dedup: prevent same event firing twice (set for O(1) lookup)
    mortal_max_age: int = 0  # Random mortal lifespan (50-80), set at game start
    is_dead: bool = False
    death_reason: str = ""
    is_ascended: bool = False
    tribulation_attempted: bool = False  # 是否已尝试渡劫飞升
    space_node_found: bool = False  # 是否已寻得空间节点
    life_phase: int = 0  # 当前人生阶段 (LifePhase enum value)
    breakthrough_failures: dict = {}  # 每个境界的突破失败次数 {realm_int: count}
    # NPC 系统
    npc_registry: dict = {}           # {npc_id: NPC 实体 dict}
    relationships: list = []          # [Relationship dict]
    # 记忆系统
    memory_working: list = []         # 最近5条完整事件
    memory_short_term: list = []      # 近50年摘要
    memory_long_term: list = []       # 远期压缩记忆
    biography_summary: str = ""       # 压缩传记 (供AI使用)
    # 因果链系统
    plot_hooks: list = []              # 当前未解决的剧情钩子
    resolved_hooks: list = []          # 已解决的钩子 (供LLM回顾)
    # 剧情线系统
    active_arcs: list = []             # 当前活跃的剧情线 (StoryArc dicts)
    # 命运主线系统 (骨骼)
    main_storyline: dict = {}          # MainStoryline dict (开局生成的命运骨架)
    # 张力曲线系统
    tension: float = 0.0               # 叙事张力值 (0-100)，驱动事件节奏张弛有度
    # 玩家选择系统
    pending_choice: Optional[dict] = None  # 等待玩家选择的事件
    choice_history: list[dict] = []        # 选择历史记录 [{age, event_text, choice_text, consequence_tag}]
    # 事件链系统
    pending_chain_events: list[str] = []   # 等待触发的链式事件ID列表
    # 宗门系统
    sect_membership: Optional[dict] = None  # SectMembership dict (None=散修)
    sect_world: dict = {}                   # {sects: {id: Sect}, relations: [SectRelation]}
    # 动态因果链系统
    causal_chains: list[dict] = []           # 活跃的因果链 (CausalChain dicts)
    # 情感道具台账
    emotional_tokens: list[dict] = []        # 随身信物/遗物 [{name, description, source_npc, source_age, keywords}]
    # 修行积累台账 (斗法系统)
    combat_repertoire: list[dict] = []       # 功法/法宝 [{name, type, desc, power, source_age, category}]
    combat_wounded: bool = False              # 战伤状态（提高下次斗法致死率）
    combat_wound_age: int = 0                # 受伤时年龄（2回合后自动痊愈）
    # 因果驱动危险系数系统
    peril_sources: list[dict] = []           # [{type, intensity, reason, source_age}]
    peril_index: float = 0.0                 # 聚合危险系数 (0-100)
    peril_dominant: str = ""                 # 当前最强因果线类型 (用于事件主题匹配)
    # Saga 涌现系统
    sagas: list[dict] = []                   # 活跃的 Saga
    saga_omens: list[dict] = []              # Saga预兆记录 (未达到涌现阈值但有迹象)
    completed_arcs_history: list[dict] = []  # 已完成 Arc 的摘要 (用于 Saga 检测)
    # 世界纪元系统
    world_eras: list[dict] = []              # 历史纪元记录
    active_era: Optional[dict] = None        # 当前活跃纪元
    next_era_check_age: int = 0              # 下次检查纪元触发的年龄
    # 上下文追踪
    last_significant_event: Optional[dict] = None  # 最近一次重大事件摘要 (AI上下文用)


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
    years_passed: int = 1  # 本回合经过的总年数
    # 新增: 前端可视化数据
    tension: float = 0.0                    # 张力值
    sect_info: Optional[dict] = None        # 宗门简要 {name, rank, contribution, sect_type}
    npc_relationships: list[dict] = []      # NPC关系列表 [{name, relation_type, sentiment, is_alive}]
    ai_enhanced: bool = False                # LLM是否参与本轮叙事（前端灵玉指示器）


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
