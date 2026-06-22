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
    1: (1, 3),      # 练气: 1-3年/回合
    2: (3, 8),      # 筑基: 3-8年/回合 (开始有闭关)
    3: (5, 15),     # 金丹: 5-15年/回合 (闭关渐长)
    4: (10, 30),    # 元婴: 10-30年/回合 (一闭关就是数十年)
    5: (20, 50),    # 化神: 20-50年/回合 (百年弹指一挥间)
}

# ---------------------------------------------------------------------------
# Breakthrough foreshadow threshold (% of cultivation needed)
# ---------------------------------------------------------------------------
FORESHADOW_THRESHOLD: float = 0.80  # Show foreshadow at 80% of required cultivation

# ---------------------------------------------------------------------------
# Realm max ages (from models, re-exported for convenience)
# ---------------------------------------------------------------------------
from ..models import REALM_MAX_AGE, REALM_NAMES  # noqa: E402
