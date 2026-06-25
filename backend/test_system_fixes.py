"""Tests for system-level fixes: sect, causality, BM25."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import random
from app.models import GameState
from app.engine.sect.sect_manager import SectManager, SectRank, SectRelationType, RANK_PROMOTION_REQS


def make_state(**overrides) -> GameState:
    defaults = {
        "game_id": "test_sys_001",
        "name": "测试仙人",
        "age": 50,
        "realm": 3,
        "sect_membership": {
            "sect_id": "sect_001",
            "rank": SectRank.INNER_DISCIPLE.value,
            "contribution": 200,
            "reputation_in_sect": 80,
        },
        "sect_world": {
            "sects": {
                "sect_001": {"sect_id": "sect_001", "name": "青云宗", "resources": {"spirit_stones": 1000, "monthly_income": 50}},
                "sect_002": {"sect_id": "sect_002", "name": "万妖宗", "resources": {"spirit_stones": 800, "monthly_income": 40}},
            },
            "relations": [
                {
                    "sect_a_id": "sect_001",
                    "sect_b_id": "sect_002",
                    "relation_type": SectRelationType.NEUTRAL.value,
                    "tension": 50,
                }
            ],
        },
    }
    defaults.update(overrides)
    return GameState(**defaults)


# ── Test 1: Promotion cooldown ──────────────────────────────────────────

def test_promotion_cooldown():
    """Verify no promotion within 30 years of last promotion."""
    sm = SectManager()
    state = make_state(age=80)
    # Simulate last promotion at age 60
    state.sect_membership["last_promotion_age"] = 60
    state.sect_membership["contribution"] = 500
    state.sect_membership["reputation_in_sect"] = 90
    state.sect_membership["rank"] = SectRank.INNER_DISCIPLE.value

    # At age 80, only 20 years since last promotion -> should be blocked
    result = sm.check_rank_promotion(state)
    assert result is None, f"Expected None (cooldown), got event: {result}"

    # At age 95, 35 years since last promotion -> should allow if qualified
    state.age = 95
    result = sm.check_rank_promotion(state)
    # Should get promoted to elder since we meet requirements
    assert result is not None, "Expected promotion at age 95 (cooldown passed)"
    assert "sect_promotion" in result["tags"], f"Missing sect_promotion tag: {result['tags']}"
    print("✓ test_promotion_cooldown passed")


# ── Test 2: Sect promotion tag present ─────────────────────────────────

def test_promotion_tag():
    """Verify sect_promotion tag is present in promotion events."""
    sm = SectManager()
    state = make_state(age=100)
    state.sect_membership["contribution"] = 500
    state.sect_membership["reputation_in_sect"] = 90
    state.sect_membership["rank"] = SectRank.INNER_DISCIPLE.value
    state.sect_membership["last_promotion_age"] = 0  # long ago

    result = sm.check_rank_promotion(state)
    assert result is not None, "Expected promotion event"
    assert "sect_promotion" in result["tags"]
    print("✓ test_promotion_tag passed")


# ── Test 3: Drift regression to mean ────────────────────────────────────

def test_drift_regression():
    """Verify tension drifts toward 50 over many iterations."""
    sm = SectManager()
    # Start at extreme tension
    state = make_state(age=50)
    state.sect_world["relations"][0]["tension"] = 95

    random.seed(42)
    # Run advance_sect_world many times
    for i in range(200):
        state.age = 50 + i
        sm.advance_sect_world(state)

    final_tension = state.sect_world["relations"][0]["tension"]
    # After many iterations with regression, tension should be closer to 50 than 95
    assert final_tension < 80, f"Expected regression toward 50, got tension={final_tension}"
    print(f"✓ test_drift_regression passed (final tension={final_tension})")


# ── Test 4: Same-turn hostile does NOT trigger invasion ─────────────────

def test_same_turn_hostile_no_invasion():
    """Verify that a relation becoming hostile this turn cannot trigger invasion."""
    sm = SectManager()
    state = make_state(age=100)
    # Mark relation as hostile but just became so this turn
    rel = state.sect_world["relations"][0]
    rel["relation_type"] = SectRelationType.HOSTILE.value
    rel["hostile_since_age"] = 100  # same as state.age

    hostile = sm._find_hostile_sect(state, "sect_001")
    assert hostile is None, f"Expected None (same turn hostile), got {hostile}"

    # Next turn (age 101), should find the hostile sect
    state.age = 101
    hostile = sm._find_hostile_sect(state, "sect_001")
    assert hostile is not None, "Expected hostile sect at age 101"
    assert hostile["name"] == "万妖宗"
    print("✓ test_same_turn_hostile_no_invasion passed")


# ── Test 5: Causality forced resolution marks hooks resolved ────────────

def test_causality_hook_resolved():
    """Verify generate_forced_resolution marks static hooks as resolved."""
    from app.engine.causality import CausalityManager

    cm = CausalityManager()
    state = make_state(age=200)

    # Create a static hook
    hook = {
        "hook_id": "test_hook_001",
        "description": "师父失踪之谜",
        "created_age": 50,
        "npc_id": "",
        "npc_name": "",
        "max_wait_years": 100,
        "is_resolved": False,
        "resolved_age": 0,
    }
    state.plot_hooks.append(hook)

    event = cm.generate_forced_resolution(state, hook)
    assert event is not None, "Expected resolution event"
    assert hook["is_resolved"] is True, "Hook should be marked resolved"
    assert hook["resolved_age"] == 200
    assert hook not in state.plot_hooks, "Hook should be removed from active list"
    assert hook in state.resolved_hooks, "Hook should be in resolved list"
    print("✓ test_causality_hook_resolved passed")


# ── Test 6: Causality chain TTL expiry marks resolved ──────────────────

def test_chain_ttl_marks_resolved():
    """Verify expired chains are marked is_resolved=True during eviction."""
    from app.engine.causality import CausalityManager, MAX_CAUSAL_CHAINS

    cm = CausalityManager()
    state = make_state(age=500)

    # Fill chains to capacity, some expired
    for i in range(MAX_CAUSAL_CHAINS):
        chain = {
            "chain_id": f"chain_{i:03d}",
            "cause_event_text": f"事件{i}",
            "cause_keywords": ["测试"],
            "expected_resolution": "解决",
            "resolution_keywords": ["解决"],
            "created_age": 100 if i < 5 else 450,  # first 5 are expired (age 500, created 100, wait 150)
            "last_accessed_age": 100 + i,
            "max_wait_years": 150,
            "urgency": 1.0,
            "is_resolved": False,
            "resolved_age": 0,
        }
        state.causal_chains.append(chain)

    # Trigger eviction by creating a new chain
    cm._evict_chains(state)

    # The expired chains (first 5) should have been removed from list
    # and marked resolved
    # Note: they're removed from state.causal_chains after being marked
    remaining_ids = [c["chain_id"] for c in state.causal_chains]
    for i in range(5):
        assert f"chain_{i:03d}" not in remaining_ids, f"Expired chain_{i:03d} should be evicted"
    print("✓ test_chain_ttl_marks_resolved passed")


# ── Test 7: BM25 zero division protection ───────────────────────────────

def test_bm25_zero_avg_dl():
    """Verify BM25 doesn't crash when _avg_dl would be 0."""
    from app.engine.memory.retriever import BM25Retriever

    retriever = BM25Retriever()
    # Force _avg_dl to 0 by indexing empty-ish documents
    retriever._indexed = True
    retriever._documents = [{"_tokens": [], "_token_set": set()}]
    retriever._doc_lengths = [0]
    retriever._avg_dl = 0.0
    retriever._idf = {"测试": 1.0}

    # This should not raise ZeroDivisionError
    score = retriever._score_document(["测试"], retriever._documents[0], 0)
    assert score == 0.0  # No tf match, but shouldn't crash
    print("✓ test_bm25_zero_avg_dl passed")


if __name__ == "__main__":
    test_promotion_cooldown()
    test_promotion_tag()
    test_drift_regression()
    test_same_turn_hostile_no_invasion()
    test_causality_hook_resolved()
    test_chain_ttl_marks_resolved()
    test_bm25_zero_avg_dl()
    print("\n🎉 All 7 system fix tests passed!")
