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
            # Cultivator accidental death: very low baseline, cubic age scaling
            death_chance = 0.0005 * (age_ratio ** 3)

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

    # ── Combat death (斗法致死通路) ────────────────────────────────────────────

    def check_combat_death(self, state: GameState, event: dict) -> Optional[dict]:
        """After a danger+combat event, check for combat death.

        Triggers:
        - Event must have event_type=danger AND tags contain 'combat' or 'calamity'
        - Base death chance: 2% (练气/筑基), 1.5% (金丹/元婴), 1% (化神)
        - Modifiers:
          - constitution: ×(1 - constitution×0.06)
          - combat_wounded: ×4
          - fortune: ×(1 - fortune×0.03)
          - repertoire power: 每持有power>=3的修行积累，-5%相对风险
        """
        tags = set(event.get("tags", []))
        if event.get("event_type") != "danger":
            return None
        if not (tags & {"combat", "calamity"}):
            return None
        # 凡人期不触发
        if state.realm < 1:
            return None

        # Base rate by realm
        base = 0.02 if state.realm <= 2 else 0.015 if state.realm <= 4 else 0.01

        # Constitution modifier
        rate = base * max(0.2, 1 - state.attributes.constitution * 0.06)

        # Fortune modifier
        rate *= max(0.3, 1 - state.attributes.fortune * 0.03)

        # Combat wounded amplifier
        if getattr(state, "combat_wounded", False):
            rate *= 4.0

        # Repertoire power bonus
        high_power_count = sum(
            1 for r in getattr(state, "combat_repertoire", [])
            if r.get("power", 0) >= 3
        )
        rate *= max(0.3, 1 - high_power_count * 0.05)

        if random.random() >= rate:
            return None

        # Trigger combat death
        state.is_dead = True
        state.death_reason = "斗法陨落"
        return self._get_combat_death_event(state)

    def _get_combat_death_event(self, state: GameState) -> dict:
        """Pick a combat-specific death event or use fallback."""
        combat_deaths = [
            e for e in ALL_EVENTS
            if e.get("category") == "death"
            and "斗" in e.get("death_reason", "")
            and check_conditions(e, state)
        ]
        if combat_deaths:
            return random.choice(combat_deaths)
        return {
            "id": "combat_death_generic",
            "text": "你在一场激烈的斗法中力竭而亡。",
            "expanded_text": (
                "灵力已竭，对手的最后一击如山岳压来。"
                "你拼尽全力运起护体灵光，却已无法抵挡。"
                "意识渐渐模糊，一切戛然而止。"
            ),
            "event_type": "danger",
            "category": "death",
            "death_reason": "斗法陨落",
        }

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
