"""Life phase management — the core solution for realm-inappropriate events.

Divides a character's life into distinct phases.  Each phase defines which
event categories / tags are permitted, preventing absurdities like a Golden
Core cultivator being mugged by village thugs.
"""
from enum import IntEnum
from ..models import GameState


class LifePhase(IntEnum):
    """Distinct stages of a character's life."""
    INFANCY = 0           # 婴幼期 (0-3岁)
    CHILDHOOD = 1         # 童年期 (4-11岁)
    MORTAL_YOUTH = 2      # 凡人青年 (12-30岁, realm==0)
    MORTAL_OLD = 3        # 凡人暮年 (31+岁, realm==0)
    EARLY_CULTIVATOR = 4  # 初入仙途 (练气 realm==1)
    MID_CULTIVATOR = 5    # 修行渐深 (筑基/金丹 realm==2-3)
    HIGH_CULTIVATOR = 6   # 大能之境 (元婴 realm==4)
    PEAK_CULTIVATOR = 7   # 顶峰之上 (化神 realm==5)


# ── Phase configuration ──────────────────────────────────────────────────
# allowed_categories: hard whitelist — events outside these are rejected
# blocked_tags:       events carrying any of these tags are rejected
# narrative_tone:     hint for future AI narrative generation
PHASE_CONFIG: dict[LifePhase, dict] = {
    LifePhase.INFANCY: {
        "allowed_categories": {"common"},
        "blocked_tags": {"mortal_life", "aging", "adult", "sect", "master",
                         "romance", "rival", "combat", "alchemy", "artifact"},
        "narrative_tone": "懵懂天真，尚在襁褓",
    },
    LifePhase.CHILDHOOD: {
        "allowed_categories": {"common", "world"},
        "blocked_tags": {"mortal_life", "aging", "adult", "sect", "master",
                         "romance", "rival", "combat", "alchemy", "artifact"},
        "narrative_tone": "童年记忆，朦胧初现",
    },
    LifePhase.MORTAL_YOUTH: {
        "allowed_categories": {"common", "social", "fortune", "calamity",
                               "world", "death"},
        "blocked_tags": {"qi_refining", "foundation", "golden_core",
                         "nascent_soul", "high_realm", "sect", "breakthrough",
                         "tribulation", "practice", "alchemy", "artifact",
                         "formation", "body_refining", "technique",
                         "gathering", "meditation", "crafting", "garden"},
        "narrative_tone": "红尘烟火，凡人悲欢",
    },
    LifePhase.MORTAL_OLD: {
        "allowed_categories": {"common", "social", "world", "death"},
        "blocked_tags": {"qi_refining", "foundation", "golden_core",
                         "nascent_soul", "high_realm", "sect", "breakthrough",
                         "childhood", "birth", "practice", "alchemy",
                         "artifact", "formation", "body_refining",
                         "technique", "gathering", "meditation", "crafting",
                         "garden"},
        "narrative_tone": "夕阳余晖，人事已非",
    },
    LifePhase.EARLY_CULTIVATOR: {
        "allowed_categories": {"cultivation", "social", "fortune", "calamity",
                               "world", "death", "common"},
        "blocked_tags": {"birth", "childhood", "mortal_life", "aging",
                         "high_realm", "endgame"},
        "narrative_tone": "仙路初启，意气风发",
    },
    LifePhase.MID_CULTIVATOR: {
        "allowed_categories": {"cultivation", "social", "fortune", "calamity",
                               "world", "death", "common"},
        "blocked_tags": {"birth", "childhood", "mortal_life", "aging",
                         "high_realm", "endgame"},
        "narrative_tone": "道途渐深，历劫成长",
    },
    LifePhase.HIGH_CULTIVATOR: {
        "allowed_categories": {"cultivation", "social", "fortune", "calamity",
                               "world", "death", "common"},
        "blocked_tags": {"birth", "childhood", "mortal_life", "aging",
                         "endgame"},
        "narrative_tone": "俯瞰天下，纵横无敌",
    },
    LifePhase.PEAK_CULTIVATOR: {
        "allowed_categories": {"cultivation", "social", "fortune", "calamity",
                               "world", "death", "common"},
        "blocked_tags": {"birth", "childhood", "mortal_life", "aging"},
        "narrative_tone": "天地之巅，求索飞升",
    },
}


class LifePhaseManager:
    """Determines and manages the current life phase of a character."""

    @staticmethod
    def determine_phase(state: GameState) -> LifePhase:
        """Compute the correct life phase from age + realm."""
        realm = state.realm
        age = state.age

        if realm >= 5:
            return LifePhase.PEAK_CULTIVATOR
        if realm == 4:
            return LifePhase.HIGH_CULTIVATOR
        if realm in (2, 3):
            return LifePhase.MID_CULTIVATOR
        if realm == 1:
            return LifePhase.EARLY_CULTIVATOR

        # realm == 0 (mortal)
        if age <= 3:
            return LifePhase.INFANCY
        if age <= 11:
            return LifePhase.CHILDHOOD
        if age <= 30:
            return LifePhase.MORTAL_YOUTH
        return LifePhase.MORTAL_OLD

    @staticmethod
    def update_phase(state: GameState) -> None:
        """Recompute and store the life phase on the state object."""
        state.life_phase = int(LifePhaseManager.determine_phase(state))

    @staticmethod
    def is_event_allowed(event: dict, phase: LifePhase) -> bool:
        """Return True if *event* is compatible with *phase*.

        Uses a combination of category whitelist and tag blacklist.
        Events whose category is not in the whitelist are rejected, unless
        the event has no category (treated as 'common').
        Events carrying any blocked tag are rejected.
        """
        cfg = PHASE_CONFIG.get(phase)
        if cfg is None:
            return True  # unknown phase — allow everything

        # ── Category check ────────────────────────────────────────────
        category = event.get("category", "common")
        if category not in cfg["allowed_categories"]:
            return False

        # ── Tag blacklist ─────────────────────────────────────────────
        event_tags = set(event.get("tags", []))
        if event_tags & cfg["blocked_tags"]:
            return False

        # ── Mortal cultivator content guard ────────────────────────────
        # If we are in a cultivator phase (>=4), reject events explicitly
        # capped at realm 0 (pure-mortal content).
        if phase >= LifePhase.EARLY_CULTIVATOR:
            cond = event.get("conditions", {})
            max_realm = cond.get("max_realm")
            if max_realm is not None and max_realm == 0:
                return False

        # ── Mortal phase: reject events requiring cultivation ─────────
        if phase <= LifePhase.MORTAL_OLD:
            effects = event.get("effects", {})
            if effects.get("cultivation", 0) > 0:
                return False
            cond = event.get("conditions", {})
            min_realm = cond.get("min_realm")
            if min_realm is not None and min_realm > 0:
                return False

        return True

    @staticmethod
    def get_narrative_tone(phase: LifePhase) -> str:
        """Return the narrative tone hint for the given phase."""
        cfg = PHASE_CONFIG.get(phase)
        return cfg["narrative_tone"] if cfg else ""
