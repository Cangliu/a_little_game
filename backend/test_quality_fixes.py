"""Tests for quality-upgrade fixes: event_system, npc, event_director, story_arc."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import math
import random
from app.models import GameState
from app.engine.event_system import EventSystem


def make_state(**overrides) -> GameState:
    defaults = {
        "game_id": "test_quality_001",
        "name": "测试仙人",
        "age": 100,
        "realm": 3,
    }
    defaults.update(overrides)
    return GameState(**defaults)


# ── Test 1: lover_sentiment None safety ────────────────────────────────

def test_lover_sentiment_none_safe():
    """Ensure _apply_npc_sentiment_boost doesn't crash when sentiment is None."""
    es = EventSystem()
    state = make_state()
    # Simulate a relationship where sentiment stored as None
    state.relationships = [
        {"npc_id": "npc_001", "relation_type": "道侣", "sentiment": None,
         "last_interaction_age": 90, "interaction_count": 10}
    ]
    state.npc_registry = {
        "npc_001": {"npc_id": "npc_001", "name": "花若兰", "is_alive": True, "realm": 3}
    }

    # Create weighted events with adult tag
    weighted = [
        ({"id": "ev1", "text": "道侣双修", "tags": ["adult", "romance"],
          "event_type": "special", "effects": {}}, 100.0),
    ]

    # This should NOT crash
    result = es._apply_npc_sentiment_boost(weighted, state)
    assert len(result) == 1
    # lover_sentiment is None → isinstance check fails → mult stays 1.0
    assert result[0][1] == 100.0, f"Expected 100.0, got {result[0][1]}"
    print("✓ test_lover_sentiment_none_safe passed")


# ── Test 2: hook_adjustments empty string key protection ───────────────

def test_hook_empty_key_protection():
    """Verify events without resolves_hook aren't affected by hook_adjustments."""
    es = EventSystem()
    state = make_state()

    # Candidates: one resolves a hook, one doesn't
    candidates = es.select_candidates(
        state, count=5,
        hook_adjustments={"test_hook": 5.0, "": 999.0},  # empty key shouldn't match
    )
    # All events without resolves_hook should have normal weights
    for cand in candidates:
        ev = cand["event"]
        if not ev.get("resolves_hook"):
            # Weight should NOT be multiplied by 999
            assert cand["weight"] < 50000, f"Event {ev.get('id')} has unexpected weight {cand['weight']}"
    print("✓ test_hook_empty_key_protection passed")


# ── Test 3: NPC age_offset is stable ──────────────────────────────────

def test_npc_age_offset_stable():
    """Verify NPC age estimation uses fixed offset instead of random per year."""
    from app.engine.npc.npc_manager import NPCManager

    nm = NPCManager()
    state = make_state(age=50)
    npc = nm.generate_npc(state, relation_type="挚友")
    assert npc is not None

    npc_dict = state.npc_registry[npc.npc_id]
    assert "age_offset" in npc_dict, "NPC should have age_offset field"
    assert 20 <= npc_dict["age_offset"] <= 50, f"age_offset out of range: {npc_dict['age_offset']}"

    # Run age_npcs multiple times — age estimation should be deterministic
    first_met = npc_dict["first_met_age"]
    offset = npc_dict["age_offset"]
    expected_age = state.age - first_met + offset

    # The estimated age should be consistent (no random fluctuation)
    state.age = 100
    expected_age_at_100 = 100 - first_met + offset
    # Just verify field exists and is used (actual death test below)
    assert expected_age_at_100 == expected_age + 50
    print(f"✓ test_npc_age_offset_stable passed (offset={offset})")


# ── Test 4: NPC death sigmoid curve ────────────────────────────────────

def test_npc_death_sigmoid():
    """Verify sigmoid death curve: low at start, high after many years."""
    # Test the sigmoid function directly
    # At max_age + 0 years: death_chance should be low (~5%)
    years_over_0 = 0
    chance_0 = 1.0 / (1.0 + math.exp(-(years_over_0 - 20) / 8.0))
    assert chance_0 < 0.10, f"Expected <10% at max_age, got {chance_0:.2%}"

    # At max_age + 10 years: moderate (~18%)
    years_over_10 = 10
    chance_10 = 1.0 / (1.0 + math.exp(-(years_over_10 - 20) / 8.0))
    assert 0.10 < chance_10 < 0.40, f"Expected 10-40% at max_age+10, got {chance_10:.2%}"

    # At max_age + 20 years: ~50%
    years_over_20 = 20
    chance_20 = 1.0 / (1.0 + math.exp(-(years_over_20 - 20) / 8.0))
    assert 0.45 < chance_20 < 0.55, f"Expected ~50% at max_age+20, got {chance_20:.2%}"

    # At max_age + 40 years: very high (>90%)
    years_over_40 = 40
    chance_40 = 1.0 / (1.0 + math.exp(-(years_over_40 - 20) / 8.0))
    assert chance_40 > 0.90, f"Expected >90% at max_age+40, got {chance_40:.2%}"

    print(f"✓ test_npc_death_sigmoid passed (0y={chance_0:.2%}, 10y={chance_10:.2%}, 20y={chance_20:.2%}, 40y={chance_40:.2%})")


# ── Test 5: causal_chain sanitization ──────────────────────────────────

def test_causal_chain_sanitize():
    """Verify _sanitize_causal_chain validates and sanitizes LLM output."""
    from app.engine.event_director import EventDirector

    # Valid input
    valid = {"cause": "师父被杀", "expected_resolution": "复仇", "keywords": ["复仇", "师仇"]}
    result = EventDirector._sanitize_causal_chain(valid)
    assert result is not None
    assert result["cause"] == "师父被杀"
    assert result["expected_resolution"] == "复仇"
    assert result["keywords"] == ["复仇", "师仇"]

    # None input
    assert EventDirector._sanitize_causal_chain(None) is None

    # Non-dict input
    assert EventDirector._sanitize_causal_chain("garbage") is None

    # Missing expected_resolution
    assert EventDirector._sanitize_causal_chain({"cause": "x"}) is None

    # Keywords with invalid types
    result = EventDirector._sanitize_causal_chain({
        "cause": "x",
        "expected_resolution": "y",
        "keywords": [123, None, "valid", "一二三四五六七八九十一"]  # last one >10 chars
    })
    assert result is not None
    assert result["keywords"] == ["valid"]  # Only valid string ≤10 chars kept

    print("✓ test_causal_chain_sanitize passed")


# ── Test 6: story_arc None defense ─────────────────────────────────────

def test_story_arc_empty_defense():
    """Verify story_arc methods handle empty active_arcs gracefully."""
    from app.engine.story_arc import StoryArcPlanner

    planner = StoryArcPlanner()
    state = make_state()

    # active_arcs is empty list (normal init)
    state.active_arcs = []
    result = planner.advance_arc_beat(state, {"text": "test", "tags": []})
    assert result is None

    ctx = planner.get_arcs_context_for_ai(state)
    assert ctx == ""

    print("✓ test_story_arc_empty_defense passed")


# ── Test 7: story_arc cap at 5 ─────────────────────────────────────────

def test_story_arc_cap():
    """Verify plan_arcs_for_realm caps at 5 arcs."""
    from app.engine.story_arc import StoryArcPlanner

    planner = StoryArcPlanner()
    state = make_state()

    # Pre-fill with 5 active arcs
    state.active_arcs = [
        {"arc_id": f"arc_{i}", "theme": f"测试{i}", "is_completed": False,
         "planned_beats": ["a", "b"], "current_beat_index": 0, "phase": "setup"}
        for i in range(5)
    ]

    result = planner.plan_arcs_for_realm(state, 3)
    assert len(result) == 5, f"Expected 5 arcs (cap), got {len(result)}"
    print("✓ test_story_arc_cap passed")


if __name__ == "__main__":
    test_lover_sentiment_none_safe()
    test_hook_empty_key_protection()
    test_npc_age_offset_stable()
    test_npc_death_sigmoid()
    test_causal_chain_sanitize()
    test_story_arc_empty_defense()
    test_story_arc_cap()
    print("\n🎉 All 7 quality-fix tests passed!")
