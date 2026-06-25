"""Realm system — cultivation gain, awakening, breakthrough, tribulation.

Handles all realm-related logic that was previously scattered across
check_mortal_awakening(), check_realm_breakthrough(), process_cultivation_gain(),
and check_space_node_tribulation() in the old engine.
"""
import json
import os
import random
from typing import Optional

from ..models import GameState, Realm, REALM_NAMES, MAX_REALM
from .config import (
    REALM_THRESHOLDS,
    BREAKTHROUGH_BASE_CHANCE,
    SPACE_NODE_BASE_CHANCE,
    AWAKENING_CHANCE_BY_AGE,
    FORESHADOW_THRESHOLD,
)
from .event_system import ALL_EVENTS


# ── Load breakthrough templates ──────────────────────────────────────────
_BT_DATA: dict = {}

def _load_breakthrough_data() -> None:
    global _BT_DATA
    bt_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "events", "breakthrough.json"
    )
    if os.path.exists(bt_path):
        with open(bt_path, "r", encoding="utf-8") as f:
            _BT_DATA = json.load(f)
        print(f"[RealmSystem] Loaded breakthrough templates")

_load_breakthrough_data()


class RealmSystem:
    """All realm-related calculations and state transitions."""

    # ── Cultivation gain ─────────────────────────────────────────────

    @staticmethod
    def process_cultivation(state: GameState, years: int = 1) -> int:
        """Add cultivation gain for *years* elapsed and return the total amount gained."""
        if state.realm == 0:
            return 0

        base = 2 + state.attributes.comprehension + int(state.attributes.constitution * 0.5)
        realm_mod = 1 + state.realm * 0.15
        gain_per_year = int(base * realm_mod)
        total_gain = gain_per_year * years
        state.cultivation += total_gain
        return total_gain

    # ── Mortal awakening ─────────────────────────────────────────────

    @staticmethod
    def check_awakening(state: GameState) -> Optional[dict]:
        """Check if a mortal awakens spiritual roots.

        Returns an awakening event dict, or None.
        """
        if state.realm != 0 or state.age < 12:
            return None

        # Tiered probability by age
        base_chance = 0.05  # fallback
        for max_age, chance in AWAKENING_CHANCE_BY_AGE:
            if state.age <= max_age:
                base_chance = chance
                break

        comp_bonus = state.attributes.comprehension * 0.005
        fort_bonus = state.attributes.fortune * 0.003
        chance = base_chance + comp_bonus + fort_bonus

        if random.random() >= chance:
            return None

        # Awaken!
        state.realm = 1
        state.cultivation = 0

        # Pick a random cult_entry event for narrative variety
        cult_entries = [e for e in ALL_EVENTS if e.get("id", "").startswith("cult_entry")]
        if cult_entries:
            chosen = random.choice(cult_entries)
            effects = chosen.get("effects", {})
            for attr in ("constitution", "comprehension", "fortune"):
                if effects.get(attr):
                    old = getattr(state.attributes, attr)
                    setattr(state.attributes, attr, old + effects[attr])
            if effects.get("add_tag"):
                tag = effects["add_tag"]
                if tag not in state.tags:
                    state.tags.append(tag)
            return {
                "id": chosen.get("id", "spiritual_awakening"),
                "text": chosen.get("text", "你踏入修仙之途！"),
                "expanded_text": chosen.get("expanded_text", ""),
                "event_type": "important",
                "category": "cultivation",
            }

        # Fallback text
        return {
            "id": "spiritual_awakening",
            "text": "你偶然间感应到天地灵气，灵根觉醒，踏入修仙之途！",
            "expanded_text": (
                "那是一个再平常不过的黄昏。天边的晚霞忽然比以往亮了三分，"
                "你抬头望向天空，只觉一股无名的温热从天灵盖涌入体内。"
                "周身的风仿佛停了一纵，草木不摇，虫鸣寂然。"
                "你感到一丝微弱却真实的力量在丹田中缓缓旋转——那是灵气。"
                "你不知这算不算缘分，但从这一刻起，你的人生已经不同了。"
            ),
            "event_type": "important",
            "category": "cultivation",
        }

    # ── Breakthrough foreshadow ──────────────────────────────────────

    @staticmethod
    def check_breakthrough_foreshadow(state: GameState) -> Optional[dict]:
        """Return a foreshadow event when cultivation is 80-99% of threshold."""
        if state.realm == 0 or state.realm >= MAX_REALM:
            return None

        threshold = REALM_THRESHOLDS.get(state.realm, 99999)
        ratio = state.cultivation / threshold if threshold > 0 else 0

        if ratio < FORESHADOW_THRESHOLD or ratio >= 1.0:
            return None

        next_name = REALM_NAMES.get(Realm(state.realm + 1), "未知")
        templates = [
            f"你感到体内灵力已至临界，{next_name}之机或许就在今朝。",
            f"经脉中的灵气如同即将决堤的洪水，你知道突破{next_name}的时刻不远了。",
            f"修炼时你隐约触摸到一层无形的壁障——{next_name}的门槛近在咫尺。",
        ]
        return {
            "id": f"foreshadow_{state.realm}_to_{state.realm + 1}",
            "text": random.choice(templates),
            "expanded_text": "",
            "event_type": "important",
            "category": "cultivation",
        }

    # ── Breakthrough ─────────────────────────────────────────────────

    @staticmethod
    def check_breakthrough(state: GameState) -> Optional[dict]:
        """Check if the player breaks through to the next realm.

        Uses data-driven templates from breakthrough.json when available.
        On failure, cultivation drops to 60% of threshold.
        """
        if state.realm >= MAX_REALM or state.realm == 0:
            return None

        threshold = REALM_THRESHOLDS.get(state.realm, 99999)
        if state.cultivation < threshold:
            return None

        # Chance calculation
        base_chance = BREAKTHROUGH_BASE_CHANCE.get(state.realm, 0.06)
        comp_bonus = state.attributes.comprehension * 0.008
        fort_bonus = state.attributes.fortune * 0.005
        chance = min(base_chance + comp_bonus + fort_bonus, 0.35)

        bt_key = f"{state.realm}_to_{state.realm + 1}"

        if random.random() < chance:
            # ── Success ──────────────────────────────────────────
            old_realm = state.realm
            state.realm += 1
            state.cultivation = 0

            # Try data-driven template
            event = _pick_breakthrough_template(bt_key, "success", state)
            if event:
                event["id"] = f"breakthrough_{bt_key}"
                event["event_type"] = "important"
                event["category"] = "cultivation"
                return event

            # Fallback
            new_name = REALM_NAMES.get(Realm(state.realm), "未知")
            if state.realm == MAX_REALM:
                return _deity_breakthrough_event(old_realm, state.realm)
            return {
                "id": f"breakthrough_{bt_key}",
                "text": f"经过漫长的修炼，你终于突破了瓶颈，成功进入{new_name}期！",
                "expanded_text": (
                    f"你盘膝于洞府之中，倾尽所能引动炼化多年的真元。"
                    f"灵力如江水一般在经脉中翻腾，不时撞击着关隘。"
                    f"那道无名的桎梏似乎异常坚固，你一度以为仍需再闭关多时，"
                    f"却忽然听见体内传来丝丝龟裂之声。"
                    f"关隘应声裂开，轰鸣震耳。天地灵气如百川归海般向你涌来。"
                    f"你知道，此生你已然踏入{new_name}之境了。"
                ),
                "event_type": "important",
                "category": "cultivation",
            }
        else:
            # ── Failure ──────────────────────────────────────────
            state.cultivation = int(threshold * 0.6)
            fail_count = state.breakthrough_failures.get(str(state.realm), 0) + 1
            state.breakthrough_failures[str(state.realm)] = fail_count

            event = _pick_breakthrough_template(bt_key, "failure", state)
            if event:
                # Inject failure count flavor
                if fail_count >= 3:
                    event["text"] = f"这已是你第{fail_count}次冲击突破了……" + event["text"]
                event["id"] = f"breakthrough_fail_{bt_key}_{fail_count}"
                event["event_type"] = "danger"
                event["category"] = "cultivation"
                return event

            # Fallback failure text
            next_name = REALM_NAMES.get(Realm(state.realm + 1), "未知")
            fail_text = f"突破{next_name}失败，你吐出一口逆血，修为跌落大半。"
            if fail_count >= 3:
                fail_text = f"这已是你第{fail_count}次冲击{next_name}了……" + fail_text
            return {
                "id": f"breakthrough_fail_{bt_key}_{fail_count}",
                "text": fail_text,
                "expanded_text": (
                    "你全力冲击那道无形的壁障，灵力在经脉中暴走。"
                    "壁障纹丝不动，反震之力却将你震得七窍溢血。"
                    "你勉力收功，丹田内的真元已损耗大半。"
                    "成败有命，你暗暗咬牙：下一次，一定要过。"
                ),
                "event_type": "danger",
                "category": "cultivation",
            }

    # ── Tribulation (post-化神) ───────────────────────────────────────

    @staticmethod
    def check_tribulation(state: GameState) -> Optional[dict]:
        """化神后寻找空间节点 → 渡劫飞升。

        Three outcomes: ascension, tribulation death, or None (keep searching).
        """
        if state.realm != MAX_REALM or state.tribulation_attempted:
            return None

        threshold = REALM_THRESHOLDS.get(MAX_REALM, 22000)
        if state.cultivation < threshold:
            return None

        # Discover space node chance
        discover_chance = SPACE_NODE_BASE_CHANCE
        discover_chance += state.attributes.fortune * 0.003
        discover_chance += state.attributes.comprehension * 0.002
        discover_chance = min(discover_chance, 0.06)

        if random.random() >= discover_chance:
            return None

        # Found the node — attempt tribulation
        state.space_node_found = True
        state.tribulation_attempted = True

        base = 0.30
        will_bonus = state.attributes.willpower * 0.05
        cons_bonus = state.attributes.constitution * 0.04
        fort_bonus = state.attributes.fortune * 0.03
        comp_bonus = state.attributes.comprehension * 0.02
        success_chance = min(base + will_bonus + cons_bonus + fort_bonus + comp_bonus, 0.92)

        if random.random() < success_chance:
            state.is_ascended = True
            return {
                "id": "ascension",
                "text": "天地共鸣，万道齐现！你寻得空间节点，逆渡九重雷劫，成功飞升！",
                "expanded_text": (
                    "那一道转瞬即逝的空间节点，你一等便是千载。"
                    "虚空裂罅之间，你踏剑而上，温热的玄黄云气在你脚下翻涌。"
                    "九重雷劫逐道落下——你以心性抵住火雷，以根骨抗住冰雷，"
                    "以福缘避过暗雷，以悟性看透君雷。"
                    "最后一道紫雷过后，天门在云端轰然裂开。"
                    "有仙人披霞衣推开仙门，与你目光相对时轻轻颔首。"
                    "此方天地在你身后逐渐缩成一点青色，再也与你无关。"
                    "仙路漫漫，自此启程。"
                ),
                "event_type": "important",
                "category": "cultivation",
            }
        else:
            state.is_dead = True
            state.death_reason = "渡劫陨落"
            return {
                "id": "tribulation_failure",
                "text": "你踏入空间节点，渡劫之雷过于狂暴，你终未能踏过这最后一步。",
                "expanded_text": (
                    "空间节点之上，九重霆雷狂作。"
                    "你以生平所学逆折君雷，可越打越觉体内真元耐不住那逆天之力。"
                    "第七道雷击破你护身法衣，第八道雷击碎你的本命法器。"
                    "那第九道雷落下时，你竟为这方天地留下一丝足迹都未能。"
                    "云开雾散，空间节点闭合如初。"
                    "下面代代以后的人，永远不会知道今夜云端曾站过一个多么接近仙道的人。"
                ),
                "event_type": "danger",
                "category": "death",
            }


# ── Helpers ──────────────────────────────────────────────────────────────

def _pick_breakthrough_template(
    bt_key: str, outcome: str, state: GameState
) -> Optional[dict]:
    """Pick a matching breakthrough template from breakthrough.json."""
    breakthroughs = _BT_DATA.get("breakthroughs", {})
    entry = breakthroughs.get(bt_key, {})
    templates = entry.get(outcome, [])
    if not templates:
        return None

    # Find templates whose conditions match
    matching = []
    for t in templates:
        conds = t.get("conditions", {})
        req_tags = conds.get("required_tags", [])
        if req_tags and not all(tag in state.tags for tag in req_tags):
            continue
        matching.append(t)

    if not matching:
        # Fallback to templates without conditions
        matching = [t for t in templates if not t.get("conditions")]

    if not matching:
        return None

    chosen = random.choice(matching)
    return {
        "text": chosen.get("text", ""),
        "expanded_text": chosen.get("expanded_text", ""),
    }


def _deity_breakthrough_event(old_realm: int, new_realm: int) -> dict:
    """Hardcoded event for reaching 化神 (the peak)."""
    return {
        "id": f"breakthrough_{old_realm}_to_{new_realm}",
        "text": (
            "你冲破元婴之桎梏，踏入化神之境！"
            "自此修为已至此方天地之巅，等待你的唯有寻得空间节点、渡劫飞升一途。"
        ),
        "expanded_text": (
            "元婴之上是化神——这是仙道与凡俗的最后一道鸿沟。"
            "你盘膝于洞府之中，元婴与肉身、神识与道心同时发生那不可逆转的汇纳。"
            "成道那一刻，你感受到这方天地微微为之一颤——你已是它所能承载的顶峰。"
            "可你也同时明白：化神不是终点。"
            "这一方天地之中，唯有寻到那一道转瞬即逝的空间节点、"
            "踏上那道逆天的渡劫飞升之路，才是你终极的根本。"
            "从今夜起，天地之间只剩下三条路：飞升、陨落、或者老死于此。"
        ),
        "event_type": "important",
        "category": "cultivation",
    }
