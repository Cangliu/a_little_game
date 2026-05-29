"""Core game engine for the cultivation life simulator."""
import json
import os
import re
import random
import uuid
from typing import Optional

from .models import (
    GameState, Attributes, Realm, REALM_NAMES, REALM_MAX_AGE, MAX_REALM,
    NextYearResponse, LifeSummary
)
from .endings import get_title, calculate_score

# Load events at module level
EVENTS_DIR = os.path.join(os.path.dirname(__file__), "events")
ALL_EVENTS = []

def load_events():
    """Load all events from JSON files."""
    global ALL_EVENTS
    all_events_path = os.path.join(EVENTS_DIR, "all_events.json")
    if os.path.exists(all_events_path):
        with open(all_events_path, "r", encoding="utf-8") as f:
            ALL_EVENTS = json.load(f)
    print(f"Loaded {len(ALL_EVENTS)} events")

# Load on import
load_events()

# In-memory game state store
GAME_STATES: dict[str, GameState] = {}

# Cultivation thresholds per realm
# 化神为修为顶峰; realm==5 后 cultivation 用于衡量寻找空间节点的准备程度
REALM_THRESHOLDS = {
    0: 0,       # Mortal -> Qi Refining (handled by awakening)
    1: 400,     # Qi Refining -> Foundation
    2: 1000,    # Foundation -> Golden Core
    3: 2500,    # Golden Core -> Nascent Soul
    4: 6000,    # Nascent Soul -> Deity
    5: 22000,  # Deity -> 空间节点累积阈值 (低资质者终于不及, 困死于此方天地)
}

# Per-realm breakthrough base chance (decreases with realm)
BREAKTHROUGH_BASE_CHANCE = {
    1: 0.15,   # Qi Refining -> Foundation
    2: 0.14,   # Foundation -> Golden Core
    3: 0.14,   # Golden Core -> Nascent Soul
    4: 0.13,   # Nascent Soul -> Deity
}

# Once at 化神 and cultivation >= REALM_THRESHOLDS[5], yearly chance to discover 空间节点
SPACE_NODE_BASE_CHANCE = 0.015  # ~1.5% per year baseline; modulated by fortune & comprehension


def create_game() -> GameState:
    """Create a new game with random attributes (simplified - pure fun)."""
    game_id = str(uuid.uuid4())[:8]
    
    # Random gender
    gender = random.choice(["male", "female"])
    
    # Random attributes for internal use (player doesn't see or choose these)
    attributes = Attributes(
        lifespan=random.randint(2, 6),
        constitution=random.randint(2, 6),
        comprehension=random.randint(2, 6),
        fortune=random.randint(2, 6),
        charisma=random.randint(2, 6),
        willpower=random.randint(2, 6),
    )
    
    state = GameState(
        game_id=game_id,
        age=0,
        realm=0,
        cultivation=0,
        gender=gender,
        attributes=attributes,
        talents=[],
        tags=[],
        events_log=[],
        mortal_max_age=random.randint(50, 80),
        is_dead=False,
        is_ascended=False,
        tribulation_attempted=False,
        space_node_found=False,
    )
    
    GAME_STATES[game_id] = state
    return state


def check_event_conditions(event: dict, state: GameState) -> bool:
    """Check if an event's conditions are met."""
    cond = event.get("conditions", {})
    category = event.get("category", "")

    # --- Implicit safety-net rules ---
    # "common" events without explicit realm constraint are mortal-only.
    if category == "common" and cond.get("min_realm") is None and cond.get("max_realm") is None:
        if state.realm > 0:
            return False

    # Mortals cannot trigger events that grant cultivation (they don't know what it is yet)
    if state.realm == 0:
        effects = event.get("effects", {})
        if effects.get("cultivation", 0) > 0:
            return False

    # Reject events whose narrative age is already in the past
    # e.g. "你5岁时..." should not appear when character is already 9
    narrative_age = _extract_narrative_age(event.get("text", ""))
    if narrative_age is not None and narrative_age < state.age:
        return False
    
    if cond.get("min_age") is not None and state.age < cond["min_age"]:
        return False
    if cond.get("max_age") is not None and state.age > cond["max_age"]:
        return False
    if cond.get("min_realm") is not None and state.realm < cond["min_realm"]:
        return False
    if cond.get("max_realm") is not None and state.realm > cond["max_realm"]:
        return False
    if cond.get("min_cultivation") is not None and state.cultivation < cond["min_cultivation"]:
        return False
    
    # Check required talents
    for talent in cond.get("required_talents", []):
        if talent not in state.talents:
            return False
    
    # Check required tags
    for tag in cond.get("required_tags", []):
        if tag not in state.tags:
            return False
    
    # Check excluded tags
    for tag in cond.get("excluded_tags", []):
        if tag in state.tags:
            return False
    
    # Check gender
    req_gender = cond.get("gender")
    if req_gender and req_gender != state.gender:
        return False
    
    # Check min attributes
    if cond.get("min_attribute"):
        for attr, min_val in cond["min_attribute"].items():
            if hasattr(state.attributes, attr) and getattr(state.attributes, attr) < min_val:
                return False
    
    return True


def apply_event_effects(event: dict, state: GameState) -> None:
    """Apply event effects to game state."""
    effects = event.get("effects", {})
    
    if effects.get("cultivation"):
        state.cultivation += effects["cultivation"]
        if state.cultivation < 0:
            state.cultivation = 0
    
    if effects.get("lifespan"):
        state.attributes.lifespan += effects["lifespan"]
    if effects.get("constitution"):
        state.attributes.constitution += effects["constitution"]
    if effects.get("comprehension"):
        state.attributes.comprehension += effects["comprehension"]
    if effects.get("fortune"):
        state.attributes.fortune += effects["fortune"]
    if effects.get("charisma"):
        state.attributes.charisma += effects["charisma"]
    if effects.get("willpower"):
        state.attributes.willpower += effects["willpower"]
    
    if effects.get("add_tag"):
        if effects["add_tag"] not in state.tags:
            state.tags.append(effects["add_tag"])
    
    # Support add_tags as a list of multiple tags
    if effects.get("add_tags"):
        for tag in effects["add_tags"]:
            if tag not in state.tags:
                state.tags.append(tag)
    
    if effects.get("remove_tag"):
        if effects["remove_tag"] in state.tags:
            state.tags.remove(effects["remove_tag"])
    
    # Check realm up
    if effects.get("realm_up") and state.realm < MAX_REALM:
        state.realm += 1
        state.cultivation = 0


def get_max_age(state: GameState) -> int:
    """Calculate max age based on realm and attributes."""
    if state.realm == 0:
        # Mortal: use the pre-rolled random lifespan (50-80)
        base_max = state.mortal_max_age if state.mortal_max_age > 0 else 70
        lifespan_bonus = state.attributes.lifespan * 3
        return base_max + lifespan_bonus
    else:
        base_max = REALM_MAX_AGE.get(Realm(state.realm), 80)
        return int(base_max * (1 + state.attributes.lifespan * 0.05))


def check_mortal_awakening(state: GameState) -> Optional[dict]:
    """Check if a mortal awakens spiritual roots and enters cultivation.

    Yearly chance ~1.0% with average stats, giving ~50% lifetime probability.
    Randomly selects from cult_entry events for narrative variety.
    """
    if state.realm != 0 or state.age < 1:
        return None

    # Tiered awakening probability by age
    if state.age <= 10:
        base_chance = 0.01      # 1% per year (ages 1-10)
    elif state.age <= 15:
        base_chance = 0.10      # 10% per year (ages 11-15)
    elif state.age <= 20:
        base_chance = 0.20      # 20% per year (ages 16-20)
    elif state.age <= 30:
        base_chance = 0.15      # 15% per year (ages 21-30, declining window)
    else:
        base_chance = 0.05      # 5% per year (ages 31+, rare late bloomer)

    comp_bonus = state.attributes.comprehension * 0.005
    fort_bonus = state.attributes.fortune * 0.003
    chance = base_chance + comp_bonus + fort_bonus

    if random.random() < chance:
        state.realm = 1
        state.cultivation = 0

        # Pick a random cult_entry event for varied narrative
        cult_entries = [e for e in ALL_EVENTS if e.get("id", "").startswith("cult_entry")]
        if cult_entries:
            chosen = random.choice(cult_entries)
            # Apply effects from the chosen entry event
            effects = chosen.get("effects", {})
            if effects.get("constitution"):
                state.attributes.constitution += effects["constitution"]
            if effects.get("comprehension"):
                state.attributes.comprehension += effects["comprehension"]
            if effects.get("fortune"):
                state.attributes.fortune += effects["fortune"]
            if effects.get("add_tag"):
                tag = effects["add_tag"]
                if tag not in state.tags:
                    state.tags.append(tag)
            return {
                "id": chosen.get("id", "spiritual_awakening"),
                "text": chosen.get("text", "你踏入修仙之途！"),
                "expanded_text": chosen.get("expanded_text", ""),
                "event_type": "important",
                "category": "cultivation"
            }
        else:
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
                "category": "cultivation"
            }
    return None


def check_realm_breakthrough(state: GameState) -> Optional[dict]:
    """Check if the player breaks through to the next realm.

    化神为修为顶峰; 达到化神后不再增境, 转而进入寻找空间节点阶段。
    突破失败时 cultivation 跌至阈值的 60% 作为瓶颈。
    """
    if state.realm >= MAX_REALM or state.realm == 0:
        return None

    threshold = REALM_THRESHOLDS.get(state.realm, 99999)

    if state.cultivation >= threshold:
        # Per-realm breakthrough chance
        base_chance = BREAKTHROUGH_BASE_CHANCE.get(state.realm, 0.06)
        comp_bonus = state.attributes.comprehension * 0.008
        fort_bonus = state.attributes.fortune * 0.005
        chance = min(base_chance + comp_bonus + fort_bonus, 0.35)

        if random.random() < chance:
            old_realm = state.realm
            state.realm += 1
            state.cultivation = 0

            new_realm_name = REALM_NAMES.get(Realm(state.realm), "未知")

            if state.realm == MAX_REALM:
                # 达成化神: 修为顶峰, 下一步需寻空间节点渡劫飞升
                return {
                    "id": f"breakthrough_{old_realm}_to_{state.realm}",
                    "text": "你冲破元婴之桎梏，踏入化神之境！自此修为已至此方天地之巅，等待你的唯有寻得空间节点、渡劫飞升一途。",
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

            return {
                "id": f"breakthrough_{old_realm}_to_{state.realm}",
                "text": f"经过漫长的修炼，你终于突破了瓶颈，成功进入{new_realm_name}期！",
                "expanded_text": (
                    f"你盘膝于洞府之中，倾尽所能引动炼化多年的真元。"
                    f"灵力如江水一般在经脉中翻腾，不时撞击着关隘。"
                    f"那道无名的梄梏似乎异常坚固，你一度以为仍需再闭关多时，"
                    f"却忽然听见体内传来丝丝龟裂之声。"
                    f"关隘应声裂开，轰鸣震耳。天地灵气如百川归海般向你涌来。"
                    f"你知道，此生你已然踏入{new_realm_name}之境了。"
                ),
                "event_type": "important",
                "category": "cultivation"
            }
        else:
            # Breakthrough failed! Bottleneck: lose half cultivation
            state.cultivation = int(threshold * 0.6)
            return None

    return None


def check_space_node_tribulation(state: GameState) -> Optional[dict]:
    """化神顶峰后寻找空间节点, 一旦寻得则立即发起渡劫飞升。

    三种结果:
    - 成功: is_ascended = True, 结局 = 飞升成仙
    - 失败: is_dead = True, death_reason = "渡劫陨落"
    - 未触发: 返回 None, 继续老去 (最终可能困死于此方天地)
    """
    if state.realm != MAX_REALM or state.tribulation_attempted:
        return None

    threshold = REALM_THRESHOLDS.get(MAX_REALM, 22000)
    if state.cultivation < threshold:
        return None

    # 逐年查询是否寻得空间节点
    discover_chance = SPACE_NODE_BASE_CHANCE
    discover_chance += state.attributes.fortune * 0.003
    discover_chance += state.attributes.comprehension * 0.002
    discover_chance = min(discover_chance, 0.06)

    if random.random() >= discover_chance:
        return None

    # 寻得空间节点, 立即发起渡劫飞升
    state.space_node_found = True
    state.tribulation_attempted = True

    # 渡劫飞升成功率由多项属性决定
    base = 0.30
    will_bonus = state.attributes.willpower * 0.05    # 心性抗劫
    cons_bonus = state.attributes.constitution * 0.04  # 根骨抗雷
    fort_bonus = state.attributes.fortune * 0.03      # 福缘助劫
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
                "九重雷劫逐道落下——你以心性抵住火雷，以根骨抗住冰雷，以福缘避过暗雷，以悟性看透君雷。"
                "最后一道紫雷过后，天门在云端轰然裂开。"
                "有仙人披霞衣推开仙门，与你目光相对时轻轻颔首。"
                "此方天地在你身后逐渐缩成一点青色，再也与你无关。"
                "仙路漫漫，自此启程。"
            ),
            "event_type": "important",
            "category": "cultivation",
        }
    else:
        # 渡劫陨落
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
                "云开雾散，空间节点闭合如初。下面代代以后的人，永远不会知道今夜云端曾站过一个多么接近仙道的人。"
            ),
            "event_type": "danger",
            "category": "death",
        }


def check_death(state: GameState) -> Optional[dict]:
    """Check if the player dies this year.

    化神顶峰若终生未寻得空间节点 (state.tribulation_attempted == False),
    其老死被特别标记为 "困死人间" / "寿终于此方天地", 用以与 "渡劫陨落" 区分。
    """
    max_age = get_max_age(state)

    # Guaranteed death if over max age
    if state.age >= max_age:
        # 化神顶峰却始终未能渡劫飞升 — 困死于此方天地
        if state.realm == MAX_REALM and not state.tribulation_attempted:
            state.is_dead = True
            state.death_reason = "困死人间"
            return {
                "id": "trapped_in_world",
                "text": "你修至化神之巅, 却终其一世也未能寻得那一道空间节点。寿元耗尽之时, 你只能闭目长叹, 困死于这一方天地之间。",
                "expanded_text": (
                    "洞府之外的山色与你初成化神时并无两样, "
                    "可你已比那时苍老了千年。"
                    "你穷尽神识, 一寸寸搜过这方天地的每一处虚空裂罅, "
                    "却始终没能等到那一线传说中的空间节点显现。"
                    "寿元如沙漏, 终有尽头。这一日, 你盘膝端坐, 望向天外那似近实远的青光, "
                    "轻轻闭上了眼睛。"
                    "化神之巅, 终究困死人间——这一方天地, 留不住你, 也送不出你。"
                ),
                "event_type": "danger",
                "category": "death",
            }

        death_events = [e for e in ALL_EVENTS
                       if e.get("category") == "death"
                       and check_event_conditions(e, state)]
        if death_events:
            event = random.choice(death_events)
            state.is_dead = True
            state.death_reason = event.get("death_reason", "寿元耗尽")
            return event

        state.is_dead = True
        state.death_reason = "寿元耗尽"
        return {
            "id": "natural_death",
            "text": "你的寿元终于耗尽，安详地离开了这个世界。",
            "event_type": "danger",
            "category": "death"
        }
    
    # Random death chance by age/realm
    age_ratio = state.age / max_age
    
    if state.realm == 0:
        # Mortal tiered death probability
        if state.age <= 5:
            death_chance = 0.0  # Infants protected
        elif state.age <= 12:
            death_chance = 0.002  # ~0.2% childhood accidents
        elif state.age <= 20:
            death_chance = 0.003  # ~0.3% teenage risk
        elif state.age <= 35:
            death_chance = 0.005  # ~0.5% young adult
        elif state.age <= 50:
            death_chance = 0.01   # ~1% middle age
        else:
            death_chance = 0.02 + 0.01 * (state.age - 50) / 20  # 2-3% old age, escalating
    else:
        death_chance = 0.0005 * (age_ratio ** 3) * 5
    
    # Fortune reduces death chance
    death_chance *= max(0.1, 1 - state.attributes.fortune * 0.03)
    
    if random.random() < death_chance and state.age > 5:
        death_events = [e for e in ALL_EVENTS 
                       if e.get("category") == "death" 
                       and check_event_conditions(e, state)]
        if death_events:
            event = random.choice(death_events)
            state.is_dead = True
            state.death_reason = event.get("death_reason", "意外身亡")
            return event
    
    return None


def select_events(state: GameState, count: int = 2) -> list[dict]:
    """Select random events for this year.

    每个事件都带有 expanded_text，不再需要拆池。只按 weight + fortune 修正抽取。
    Dedup: events already triggered in this life are excluded.
    """
    used_ids = set(state.used_event_ids)
    eligible = [e for e in ALL_EVENTS
                if e.get("category") != "death"
                and e.get("id") not in used_ids
                and check_event_conditions(e, state)]

    if not eligible:
        return [{
            "id": "nothing",
            "text": "平静的一年，无事发生。",
            "expanded_text": "这一年风调雨顺，门前的桃树几乎是一夜之间就开满了。你起居如常，读书、修炼，都没出什么意外。偶尔抬头看一眼远处的山，那云彩变幻万千，仿佛有许多话要说，却又一句也说不出口。平静也是一种造化，你心中隐隐如是想。",
            "event_type": "normal",
            "category": "common"
        }]

    fortune_mod = 1 + state.attributes.fortune * 0.05

    # Realm-based weight multiplier for adult events
    # Targets: mortal/练气 ~15yr, 筑基 ~20yr, 金丹 ~30yr, 元婴 ~50yr, 化神 ~100yr
    ADULT_REALM_MULTIPLIER = {0: 0.4, 1: 7.0, 2: 3.2, 3: 1.6, 4: 0.9, 5: 0.5}
    adult_mult = ADULT_REALM_MULTIPLIER.get(state.realm, 1.0)

    weighted = []
    for e in eligible:
        w = float(e.get("weight", 50))
        et = e.get("event_type")
        if et == "fortune":
            w *= fortune_mod
        elif et == "danger":
            w *= max(0.5, 1 - state.attributes.fortune * 0.02)
        # Apply adult event realm-based weight scaling
        if 'adult' in e.get('tags', []):
            w *= adult_mult
        weighted.append((e, w))

    selected: list[dict] = []
    for _ in range(min(count, len(weighted))):
        total = sum(w for _, w in weighted)
        if total <= 0:
            break
        r = random.uniform(0, total)
        cum = 0.0
        for i, (event, w) in enumerate(weighted):
            cum += w
            if r <= cum:
                selected.append(event)
                weighted.pop(i)
                break
    return selected


def process_cultivation_gain(state: GameState) -> int:
    """Calculate base cultivation gain per year.

    Deliberately slow: takes ~55-65% of a realm's lifespan to reach threshold,
    leaving limited time for breakthrough attempts.
    """
    if state.realm == 0:
        return 0  # Mortals don't gain cultivation

    base = 2 + state.attributes.comprehension + int(state.attributes.constitution * 0.5)

    # Small realm bonus (keeps pace with exponential thresholds)
    realm_mod = 1 + state.realm * 0.15

    return int(base * realm_mod)


def _extract_narrative_age(text: str) -> int | None:
    """Extract the character age from event text (e.g. '你3岁时' -> 3)."""
    m = re.search(r'(\d+)\s*岁', text)
    if m:
        return int(m.group(1))
    return None


def advance_year(game_id: str) -> NextYearResponse:
    """Advance the game by one year."""
    state = GAME_STATES.get(game_id)
    if not state:
        raise ValueError(f"Game {game_id} not found")
    
    if state.is_dead or state.is_ascended:
        raise ValueError("Game is already over")
    
    state.age += 1
    year_events = []
    
    # Check death first
    death_event = check_death(state)
    if death_event:
        year_events.append({
            "text": death_event["text"],
            "type": death_event.get("event_type", "danger"),
            "age": state.age
        })
        state.events_log.append({"age": state.age, "text": death_event["text"]})
        
        return NextYearResponse(
            age=state.age,
            realm=state.realm,
            realm_name=REALM_NAMES.get(Realm(state.realm), "未知"),
            cultivation=state.cultivation,
            cultivation_max=REALM_THRESHOLDS.get(state.realm, 99999),
            events=year_events,
            attributes=state.attributes,
            is_dead=True,
            death_reason=state.death_reason,
            gender=state.gender,
        )
    
    # Check mortal awakening (enter cultivation path)
    awakening = check_mortal_awakening(state)
    if awakening:
        year_events.append({
            "text": awakening["text"],
            "type": "important",
            "category": "cultivation",
            "age": state.age
        })
        state.events_log.append({"age": state.age, "text": awakening["text"]})
    
    # Base cultivation gain
    cult_gain = process_cultivation_gain(state)
    if cult_gain > 0:
        state.cultivation += cult_gain
    
    # Select and apply events
    event_count = 1 if state.age <= 3 else (2 if state.age <= 12 else random.randint(1, 3))
    selected = select_events(state, event_count)
    
    # Sort by narrative age so earlier events display first (chronological order)
    selected.sort(key=lambda e: _extract_narrative_age(e.get("text", "")) or 9999)
    
    for event in selected:
        apply_event_effects(event, state)
        # Record used event ID for dedup
        if event.get("id"):
            state.used_event_ids.append(event["id"])
        # Sync state.age with narrative age so the timeline stays consistent.
        # If the event text says "你5岁时", state.age becomes max(state.age, 5).
        narrative_age = _extract_narrative_age(event["text"])
        if narrative_age is not None:
            state.age = max(state.age, narrative_age)
        year_events.append({
            "text": event["text"],
            "expanded_text": event.get("expanded_text", ""),
            "type": event.get("event_type", "normal"),
            "category": event.get("category", "common"),
            "age": state.age
        })
        state.events_log.append({"age": state.age, "text": event["text"]})
    
    # Check breakthrough
    breakthrough = check_realm_breakthrough(state)
    if breakthrough:
        year_events.append({
            "text": breakthrough["text"],
            "type": "important",
            "category": "cultivation",
            "age": state.age
        })
        state.events_log.append({"age": state.age, "text": breakthrough["text"]})

    # 化神后逐年判定: 是否寻得空间节点 -> 渡劫飞升 -> 飞升 / 陨落
    tribulation = check_space_node_tribulation(state)
    if tribulation:
        year_events.append({
            "text": tribulation["text"],
            "expanded_text": tribulation.get("expanded_text", ""),
            "type": tribulation.get("event_type", "important"),
            "category": tribulation.get("category", "cultivation"),
            "age": state.age,
        })
        state.events_log.append({"age": state.age, "text": tribulation["text"]})

        if state.is_ascended:
            return NextYearResponse(
                age=state.age,
                realm=state.realm,
                realm_name=REALM_NAMES.get(Realm(state.realm), "化神"),
                cultivation=state.cultivation,
                cultivation_max=0,
                events=year_events,
                attributes=state.attributes,
                is_ascended=True,
                space_node_found=True,
                gender=state.gender,
            )

        if state.is_dead:
            return NextYearResponse(
                age=state.age,
                realm=state.realm,
                realm_name=REALM_NAMES.get(Realm(state.realm), "化神"),
                cultivation=state.cultivation,
                cultivation_max=REALM_THRESHOLDS.get(state.realm, 99999),
                events=year_events,
                attributes=state.attributes,
                is_dead=True,
                death_reason=state.death_reason,
                space_node_found=True,
                gender=state.gender,
            )

    return NextYearResponse(
        age=state.age,
        realm=state.realm,
        realm_name=REALM_NAMES.get(Realm(state.realm), "未知"),
        cultivation=state.cultivation,
        cultivation_max=REALM_THRESHOLDS.get(state.realm, 99999),
        events=year_events,
        attributes=state.attributes,
        space_node_found=state.space_node_found,
        gender=state.gender,
    )


def get_life_summary(game_id: str) -> LifeSummary:
    """Get the life summary after death/ascension."""
    state = GAME_STATES.get(game_id)
    if not state:
        raise ValueError(f"Game {game_id} not found")
    
    title_info = get_title(
        state.age, state.realm,
        is_ascended=state.is_ascended,
        death_reason=state.death_reason or "",
    )
    attrs_dict = state.attributes.model_dump()
    score = calculate_score(
        state.age, state.realm, attrs_dict,
        is_ascended=state.is_ascended,
        death_reason=state.death_reason or "",
    )
    
    # Get key events (important ones)
    key_events = [e["text"] for e in state.events_log
                  if any(kw in e["text"] for kw in [
                      "突破", "飞升", "传承", "大机缘", "走火入魔",
                      "陨落", "渡劫", "空间节点", "困死", "化神",
                  ])]
    
    if not key_events:
        key_events = [e["text"] for e in state.events_log[-5:]]
    
    if state.is_ascended:
        ending = "飞升成仙"
    elif state.is_dead:
        ending = state.death_reason or "寿元耗尽"
    else:
        ending = "未知"

    return LifeSummary(
        total_age=state.age,
        max_realm=state.realm,
        max_realm_name=REALM_NAMES.get(Realm(state.realm), "未知"),
        death_reason=ending,
        key_events=key_events[:10],
        talents=state.talents,
        final_attributes=state.attributes,
        score=score,
        title=title_info["title"],
        gender=state.gender,
    )
