"""All game configuration constants, extracted from the old monolithic engine."""
from ..models import Realm

# ---------------------------------------------------------------------------
# Realm constants
# ---------------------------------------------------------------------------
MAX_REALM = int(Realm.DEITY)  # 化神为修为顶峰

# Cultivation thresholds per realm
# 化神为修为顶峰; realm==5 后 cultivation 用于衡量寻找空间节点的准备程度
REALM_THRESHOLDS: dict[int, int] = {
    0: 0,       # Mortal -> Qi Refining (handled by awakening)
    1: 400,     # Qi Refining -> Foundation
    2: 1000,    # Foundation -> Golden Core
    3: 2500,    # Golden Core -> Nascent Soul
    4: 6000,    # Nascent Soul -> Deity
    5: 22000,   # Deity -> 空间节点累积阈值
}

# Per-realm breakthrough base chance (decreases with realm)
BREAKTHROUGH_BASE_CHANCE: dict[int, float] = {
    1: 0.15,   # Qi Refining -> Foundation
    2: 0.14,   # Foundation -> Golden Core
    3: 0.14,   # Golden Core -> Nascent Soul
    4: 0.13,   # Nascent Soul -> Deity
}

# Once at 化神 and cultivation >= REALM_THRESHOLDS[5],
# yearly chance to discover 空间节点
SPACE_NODE_BASE_CHANCE: float = 0.015

# ---------------------------------------------------------------------------
# Mortal awakening probabilities (tiered by age)
# ---------------------------------------------------------------------------
AWAKENING_CHANCE_BY_AGE: list[tuple[int, float]] = [
    (10,  0.01),   # 1% per year   (ages 1-10)
    (15,  0.10),   # 10% per year  (ages 11-15)
    (20,  0.20),   # 20% per year  (ages 16-20)
    (30,  0.15),   # 15% per year  (ages 21-30)
    (999, 0.05),   # 5% per year   (ages 31+)
]

# ---------------------------------------------------------------------------
# Death probabilities for mortals (tiered by age)
# ---------------------------------------------------------------------------
MORTAL_DEATH_TIERS: list[tuple[int, float]] = [
    (5,   0.0),     # infants protected
    (12,  0.002),   # ~0.2% childhood
    (20,  0.003),   # ~0.3% teenage
    (35,  0.005),   # ~0.5% young adult
    (50,  0.01),    # ~1% middle age
    (999, None),    # escalating — computed dynamically
]

# ---------------------------------------------------------------------------
# Time step per realm (min_years, max_years per turn)
# Higher realms advance more years per story beat
# ---------------------------------------------------------------------------
TIME_STEP_BY_REALM: dict = {
    0: (1, 1),      # 凡人: 1年/回合 (人生短暂，每年都有故事)
    1: (1, 2),      # 练气: 1-2年/回合 (初入仙途，事多)
    2: (2, 5),      # 筑基: 2-5年/回合 (开始有闭关)
    3: (4, 12),     # 金丹: 4-12年/回合 (闭关渐长)
    4: (8, 25),     # 元婴: 8-25年/回合 (一闭关就是数十年)
    5: (15, 40),    # 化神: 15-40年/回合 (百年弹指一挥间)
}

# ---------------------------------------------------------------------------
# Breakthrough foreshadow threshold (% of cultivation needed)
# ---------------------------------------------------------------------------
FORESHADOW_THRESHOLD: float = 0.80  # Show foreshadow at 80% of required cultivation

# ---------------------------------------------------------------------------
# Tension curve — narrative pacing system
# ---------------------------------------------------------------------------
TENSION_DECAY_PER_TURN: float = 10.0  # 每回合自然衰减

TENSION_BY_EVENT_TYPE: dict[str, float] = {
    "danger": 25.0,     # 危险事件大幅提升张力
    "important": 15.0,  # 重要事件中等提升
    "fortune": -10.0,   # 机缘事件降低张力
    "normal": -5.0,     # 普通事件微降
}

# tension值 -> (danger_multiplier, fortune_multiplier)
# 高张力时降低danger权重（给玩家喘息），提升fortune
# 低张力时提升danger权重（制造冲突）
TENSION_HIGH_THRESHOLD: float = 70.0
TENSION_LOW_THRESHOLD: float = 30.0
TENSION_WEIGHT_HIGH = (0.3, 2.0)    # (danger_mult, fortune_mult) when tension >= 70
TENSION_WEIGHT_MID  = (1.0, 1.0)    # when 30 <= tension < 70
TENSION_WEIGHT_LOW  = (2.0, 0.5)    # when tension < 30

# ---------------------------------------------------------------------------
# Peril系统配置（因果驱动动态危险系数）
# ---------------------------------------------------------------------------
PERIL_DECAY_PER_TURN: float = 5.0          # 每回合自然衰减（降低以允许积累）
PERIL_SECT_PROTECTION: float = 2.0         # 有宗门时额外衰减
PERIL_LOW_PROFILE_BONUS: float = 8.0       # 连续3回合无combat/fortune时额外衰减

# 各因果类型的初始贡献值
PERIL_CONTRIB: dict[str, int] = {
    "treasure_envy": 8,        # 每点power贡献8
    "sect_destroyed": 50,      # 宗门覆灭一次性+50
    "blood_feud": 60,          # 道侣/师父被杀+60
    "fame": 30,                # 突破/大比获胜+30
    "consequence": 25,         # 选择后果+25
    "fortune_streak": 18,      # fortune事件触发+18
    "danger_exposure": 15,     # danger+combat事件+15（树大招风）
}

# danger_level阈值
PERIL_LEVEL_THRESHOLDS: tuple = (30, 70)   # <30=偏Level1, 30-70=均匀, >70=偏Level3
# danger_level对致死率的乘数
DANGER_LEVEL_DEATH_MULT: dict[int, float] = {1: 0.5, 2: 1.0, 3: 2.5}

# ---------------------------------------------------------------------------
# Realm max ages (from models, re-exported for convenience)
# ---------------------------------------------------------------------------
from ..models import REALM_MAX_AGE, REALM_NAMES  # noqa: E402
