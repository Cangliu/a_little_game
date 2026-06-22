"""Death system — natural death, accidental death, and 困死人间.

Handles all mortality checks that were previously in check_death() of
the old monolithic engine.
"""
import random
from typing import Optional

from ..models import GameState, Realm, REALM_MAX_AGE
from .config import MAX_REALM, MORTAL_DEATH_TIERS
from .event_system import ALL_EVENTS, check_conditions


class DeathSystem:
    """Mortality checks split into natural vs accidental."""

    @staticmethod
    def get_max_age(state: GameState) -> int:
        """Calculate max age based on realm and attributes."""
        if state.realm == 0:
            base_max = state.mortal_max_age if state.mortal_max_age > 0 else 70
            lifespan_bonus = state.attributes.lifespan * 3
            return base_max + lifespan_bonus
        else:
            base_max = REALM_MAX_AGE.get(Realm(state.realm), 80)
            return int(base_max * (1 + state.attributes.lifespan * 0.05))

    # ── Natural death (lifespan exhausted) ───────────────────────────

    def check_natural_death(self, state: GameState) -> Optional[dict]:
        """Check if the character has exceeded their max age.

        Special case: 化神 peak who never found a space node → 困死人间.
        """
        max_age = self.get_max_age(state)

        if state.age < max_age:
            return None

        # 化神顶峰 — never attempted tribulation → trapped in the mortal world
        if state.realm == MAX_REALM and not state.tribulation_attempted:
            state.is_dead = True
            state.death_reason = "困死人间"
            return {
                "id": "trapped_in_world",
                "text": (
                    "你修至化神之巅, 却终其一世也未能寻得那一道空间节点。"
                    "寿元耗尽之时, 你只能闭目长叹, 困死于这一方天地之间。"
                ),
                "expanded_text": (
                    "洞府之外的山色与你初成化神时并无两样, "
                    "可你已比那时苍老了千年。"
                    "你穷尽神识, 一寸寸搜过这方天地的每一处虚空裂罅, "
                    "却始终没能等到那一线传说中的空间节点显现。"
                    "寿元如沙漏, 终有尽头。这一日, 你盘膝端坐, "
                    "望向天外那似近实远的青光, 轻轻闭上了眼睛。"
                    "化神之巅, 终究困死人间——"
                    "这一方天地, 留不住你, 也送不出你。"
                ),
                "event_type": "danger",
                "category": "death",
            }

        # Normal lifespan exhaustion — pick a matching death event
        death_events = [
            e for e in ALL_EVENTS
            if e.get("category") == "death" and check_conditions(e, state)
        ]
        if death_events:
            event = random.choice(death_events)
            state.is_dead = True
            state.death_reason = event.get("death_reason", "寿元耗尽")
            return event

        # Ultimate fallback
        state.is_dead = True
        state.death_reason = "寿元耗尽"
        return {
            "id": "natural_death",
            "text": "你的寿元终于耗尽，安详地离开了这个世界。",
            "expanded_text": "",
            "event_type": "danger",
            "category": "death",
        }

    # ── Accidental death (random chance each year) ───────────────────

    def check_accidental_death(self, state: GameState) -> Optional[dict]:
        """Yearly random death chance based on age / realm / fortune."""
        max_age = self.get_max_age(state)
        age_ratio = state.age / max_age if max_age > 0 else 1.0

        if state.realm == 0:
            death_chance = self._mortal_death_chance(state)
        else:
            death_chance = 0.0005 * (age_ratio ** 3) * 5

        # Fortune reduces death chance
        death_chance *= max(0.1, 1 - state.attributes.fortune * 0.03)

        if state.age <= 5:
            return None  # Infants protected

        if random.random() >= death_chance:
            return None

        death_events = [
            e for e in ALL_EVENTS
            if e.get("category") == "death" and check_conditions(e, state)
        ]
        if death_events:
            event = random.choice(death_events)
            state.is_dead = True
            state.death_reason = event.get("death_reason", "意外身亡")
            return event

        return None  # Low-probability path: no matching death event → survive

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _mortal_death_chance(state: GameState) -> float:
        """Tiered death probability for mortals."""
        for max_age, chance in MORTAL_DEATH_TIERS:
            if chance is None:
                # Escalating tier for old age (51+)
                return 0.02 + 0.01 * (state.age - 50) / 20
            if state.age <= max_age:
                return chance
        return 0.02
