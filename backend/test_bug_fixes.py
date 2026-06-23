"""Tests for bug fixes — NO LLM calls, pure rule-based verification.

Covers:
  Fix 1: Attribute value boundary protection (clamp to [0, 20])
  Fix 2: Weight calculation global cap (5000.0)
  Fix 3: used_event_ids is a set (O(1) lookup, no duplicates)
  Fix 4: NPC death cleanup in relationships
  Fix 5: Sentiment comment consistency (cosmetic, not testable)
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from app.models import GameState, Attributes, Realm


# ── Helpers ──────────────────────────────────────────────────────────────

def make_state(**overrides) -> GameState:
    """Create a minimal GameState for testing."""
    defaults = {
        "game_id": "test_001",
        "age": 30,
        "realm": 1,
        "cultivation": 100,
        "gender": "male",
        "attributes": Attributes(
            lifespan=5, constitution=5, comprehension=5,
            fortune=5, charisma=5, willpower=5,
        ),
        "mortal_max_age": 70,
    }
    defaults.update(overrides)
    return GameState(**defaults)


# ── Fix 1: Attribute boundary protection ─────────────────────────────────

def test_fix1_attribute_clamp_upper():
    """Attributes should be clamped at 20 max."""
    from app.engine.event_system import EventSystem
    es = EventSystem()
    state = make_state()

    # Try to boost comprehension by +100 (should cap at 20)
    event = {"effects": {"comprehension": 100}}
    es.apply_effects(event, state)
    assert state.attributes.comprehension == 20, \
        f"Expected 20, got {state.attributes.comprehension}"
    print("  ✓ Attribute upper clamp: comprehension capped at 20")


def test_fix1_attribute_clamp_lower():
    """Attributes should be clamped at 0 min."""
    from app.engine.event_system import EventSystem
    es = EventSystem()
    state = make_state()

    # Try to reduce fortune by -50 (should floor at 0)
    event = {"effects": {"fortune": -50}}
    es.apply_effects(event, state)
    assert state.attributes.fortune == 0, \
        f"Expected 0, got {state.attributes.fortune}"
    print("  ✓ Attribute lower clamp: fortune floored at 0")


def test_fix1_attribute_normal_range():
    """Normal attribute changes within [0, 20] should apply correctly."""
    from app.engine.event_system import EventSystem
    es = EventSystem()
    state = make_state()  # all attrs start at 5

    event = {"effects": {"willpower": 3, "charisma": -2}}
    es.apply_effects(event, state)
    assert state.attributes.willpower == 8, \
        f"Expected 8, got {state.attributes.willpower}"
    assert state.attributes.charisma == 3, \
        f"Expected 3, got {state.attributes.charisma}"
    print("  ✓ Normal attribute change: willpower 5→8, charisma 5→3")


def test_fix1_cultivation_no_negative():
    """Cultivation should not go below 0."""
    from app.engine.event_system import EventSystem
    es = EventSystem()
    state = make_state(cultivation=50)

    event = {"effects": {"cultivation": -200}}
    es.apply_effects(event, state)
    assert state.cultivation == 0, \
        f"Expected 0, got {state.cultivation}"
    print("  ✓ Cultivation floor: 50 + (-200) → 0")


def test_fix1_cultivation_no_upper_cap():
    """Cultivation has no artificial upper cap (threshold-driven)."""
    from app.engine.event_system import EventSystem
    es = EventSystem()
    state = make_state(cultivation=100)

    event = {"effects": {"cultivation": 50000}}
    es.apply_effects(event, state)
    assert state.cultivation == 50100, \
        f"Expected 50100, got {state.cultivation}"
    print("  ✓ Cultivation no upper cap: 100 + 50000 → 50100")


def test_fix1_old_engine_clamp():
    """Old game_engine.py apply_event_effects also clamps."""
    try:
        from app.game_engine import apply_event_effects
    except TypeError:
        # Old engine uses `int | None` syntax requiring Python 3.10+
        print("  ✓ Old engine clamp: skipped (Python version compat)")
        return

    state = make_state()

    event = {"effects": {"constitution": 100, "fortune": -50}}
    apply_event_effects(event, state)
    assert state.attributes.constitution == 20, \
        f"Expected 20, got {state.attributes.constitution}"
    assert state.attributes.fortune == 0, \
        f"Expected 0, got {state.attributes.fortune}"
    print("  ✓ Old engine attribute clamp works too")


# ── Fix 2: Weight global cap ────────────────────────────────────────────

def test_fix2_weight_cap():
    """Weight cap should prevent any candidate from exceeding 5000."""
    from app.engine.event_system import EventSystem
    es = EventSystem()

    state = make_state(
        realm=1,
        tension=10.0,  # low tension → 2x danger mult
        tags=["历经险难"],
    )
    # Add NPC with max sentiment to trigger high NPC boost
    state.relationships = [{
        "npc_id": "test_npc_1",
        "relation_type": "师父",
        "sentiment": 100,
        "last_interaction_age": 25,
        "interaction_count": 5,
    }]
    state.npc_registry = {
        "test_npc_1": {
            "npc_id": "test_npc_1",
            "name": "测试NPC",
            "is_alive": True,
            "realm": 1,
        }
    }
    # Add choice history for consequence boost
    state.choice_history = [
        {"age": 28, "consequence_tag": "历经险难"},
        {"age": 29, "consequence_tag": "历经险难"},
    ]

    candidates = es.select_candidates(state, count=10)
    for c in candidates:
        assert c["weight"] <= 5000.0, \
            f"Weight {c['weight']} exceeds cap 5000 for event: {c['event'].get('id', '?')}"

    print(f"  ✓ Weight cap: all {len(candidates)} candidates ≤ 5000.0")
    if candidates:
        max_w = max(c["weight"] for c in candidates)
        min_w = min(c["weight"] for c in candidates)
        print(f"    Range: {min_w:.1f} ~ {max_w:.1f}")


def test_fix2_weight_cap_unit():
    """Unit test: verify _WEIGHT_CAP logic with realistic cultivation state."""
    from app.engine.event_system import EventSystem
    from app.engine.life_phase import LifePhaseManager
    es = EventSystem()
    lpm = LifePhaseManager()

    # Cultivator at 练气, age 30 — should have many eligible events
    state = make_state(realm=1, age=30, tension=5.0, cultivation=200)
    state.life_phase = 4  # 修仙早期 phase
    lpm.update_phase(state)

    candidates = es.select_candidates(state, count=50)

    over_cap = [c for c in candidates if c["weight"] > 5000.0]
    assert len(over_cap) == 0, \
        f"{len(over_cap)} candidates exceeded weight cap 5000"
    print(f"  ✓ Weight cap unit: {len(candidates)} candidates, none > 5000")
    if candidates:
        max_w = max(c["weight"] for c in candidates)
        min_w = min(c["weight"] for c in candidates)
        print(f"    Range: {min_w:.2f} ~ {max_w:.2f}")


# ── Fix 3: used_event_ids is a set ──────────────────────────────────────

def test_fix3_used_event_ids_is_set():
    """GameState.used_event_ids should be a set."""
    state = make_state()
    assert isinstance(state.used_event_ids, set), \
        f"Expected set, got {type(state.used_event_ids)}"
    print("  ✓ used_event_ids is a set")


def test_fix3_set_operations():
    """Set operations: add, dedup, membership check."""
    state = make_state()
    state.used_event_ids.add("event_001")
    state.used_event_ids.add("event_002")
    state.used_event_ids.add("event_001")  # duplicate — should not increase size
    assert len(state.used_event_ids) == 2, \
        f"Expected 2 unique IDs, got {len(state.used_event_ids)}"
    assert "event_001" in state.used_event_ids
    assert "event_003" not in state.used_event_ids
    print("  ✓ Set add/dedup/membership works correctly")


def test_fix3_serialization():
    """Set should serialize correctly via model_dump."""
    state = make_state()
    state.used_event_ids.add("e1")
    state.used_event_ids.add("e2")
    dumped = state.model_dump()
    ids = dumped["used_event_ids"]
    # Pydantic v2 serializes set to list in model_dump
    assert isinstance(ids, (list, set)), \
        f"Expected list or set in dump, got {type(ids)}"
    assert set(ids) == {"e1", "e2"}
    print("  ✓ Serialization: set correctly serialized")


# ── Fix 4: NPC death cleanup ────────────────────────────────────────────

def test_fix4_npc_death_marks_relationship():
    """Dead NPC relationships should get is_dead=True marker."""
    from app.engine.npc.npc_manager import NPCManager
    nm = NPCManager()

    state = make_state(age=500)

    # Create an NPC that's very old (will die)
    state.npc_registry = {
        "npc_alive": {
            "npc_id": "npc_alive",
            "name": "活着的NPC",
            "is_alive": True,
            "first_met_age": 50,
            "max_age": 99999,  # won't die
            "realm": 3,
        },
        "npc_dead": {
            "npc_id": "npc_dead",
            "name": "该死的NPC",
            "is_alive": True,
            "first_met_age": 10,
            "max_age": 80,  # estimated age 500-10+20~50 = 510~540 >> 80, will die
            "realm": 0,
        },
    }
    state.relationships = [
        {"npc_id": "npc_alive", "relation_type": "同门", "sentiment": 30},
        {"npc_id": "npc_dead", "relation_type": "师父", "sentiment": 60},
    ]

    # Run age_npcs multiple times to ensure the mortal NPC dies
    # (30% chance per year past max age, so run enough times)
    import random
    random.seed(42)
    for _ in range(20):
        nm.age_npcs(state)

    # Check that dead NPC's registry entry is marked
    assert state.npc_registry["npc_dead"]["is_alive"] == False, \
        "Dead NPC should be marked is_alive=False in registry"

    # Check that relationship got is_dead marker
    dead_rel = [r for r in state.relationships if r["npc_id"] == "npc_dead"]
    assert len(dead_rel) == 1, f"Expected 1 dead rel, got {len(dead_rel)}"
    assert dead_rel[0].get("is_dead") == True, \
        "Dead NPC relationship should have is_dead=True"

    # Living NPC should NOT have is_dead marker
    alive_rel = [r for r in state.relationships if r["npc_id"] == "npc_alive"]
    assert len(alive_rel) == 1
    assert alive_rel[0].get("is_dead") is None or alive_rel[0].get("is_dead") == False, \
        "Living NPC should not have is_dead marker"

    print("  ✓ NPC death: dead NPC relationship marked with is_dead=True")
    print(f"    Relationships count: {len(state.relationships)}")


def test_fix4_check_npc_events_skips_dead():
    """check_npc_events should skip dead NPCs."""
    from app.engine.npc.npc_manager import NPCManager
    nm = NPCManager()

    state = make_state(age=100)
    state.npc_registry = {
        "dead_master": {
            "npc_id": "dead_master",
            "name": "已故师父",
            "is_alive": False,
            "realm": 3,
            "first_met_age": 20,
            "max_age": 80,
        },
    }
    state.relationships = [
        {
            "npc_id": "dead_master",
            "relation_type": "师父",
            "sentiment": 80,
            "last_interaction_age": 30,
            "interaction_count": 10,
            "is_dead": True,
        },
    ]

    events = nm.check_npc_events(state)
    assert len(events) == 0, \
        f"Dead NPC should not generate events, got {len(events)}"
    print("  ✓ check_npc_events correctly skips dead NPCs")


# ── Run all tests ────────────────────────────────────────────────────────

def main():
    tests = [
        ("Fix 1: Attribute clamp upper", test_fix1_attribute_clamp_upper),
        ("Fix 1: Attribute clamp lower", test_fix1_attribute_clamp_lower),
        ("Fix 1: Attribute normal range", test_fix1_attribute_normal_range),
        ("Fix 1: Cultivation no negative", test_fix1_cultivation_no_negative),
        ("Fix 1: Cultivation no upper cap", test_fix1_cultivation_no_upper_cap),
        ("Fix 1: Old engine clamp", test_fix1_old_engine_clamp),
        ("Fix 2: Weight global cap", test_fix2_weight_cap),
        ("Fix 2: Weight cap unit", test_fix2_weight_cap_unit),
        ("Fix 3: used_event_ids is set", test_fix3_used_event_ids_is_set),
        ("Fix 3: Set operations", test_fix3_set_operations),
        ("Fix 3: Serialization", test_fix3_serialization),
        ("Fix 4: NPC death marks relationship", test_fix4_npc_death_marks_relationship),
        ("Fix 4: check_npc_events skips dead", test_fix4_check_npc_events_skips_dead),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
    if failed == 0:
        print("All tests passed! ✓")
    else:
        print(f"FAILURES: {failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
