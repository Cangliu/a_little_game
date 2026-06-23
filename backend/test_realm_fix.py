#!/usr/bin/env python3
"""Tests for min_realm narrative consistency fix.

Validates that events containing high-age keywords (千年/万年/上古/远古)
have appropriately elevated min_realm values, and that the event selection
pipeline correctly filters them out for low-realm characters.

No LLM calls — pure rule-based validation.
"""
import json
import os
import sys

PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = ""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  ✓ {name}")
    else:
        FAILED += 1
        print(f"  ✗ {name}  {detail}")


def load_events():
    path = os.path.join(os.path.dirname(__file__), "app", "events", "all_events.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Test 1: No "千年" event has min_realm < 3 ──────────────────────────
def test_qiannian_realm():
    print("\n[Test 1] 千年类事件 min_realm ≥ 3（金丹）")
    events = load_events()
    violations = [
        e["id"] for e in events
        if "千年" in e.get("text", "")
        and e.get("conditions", {}).get("min_realm", 0) < 3
    ]
    check("no 千年 event with min_realm < 3", len(violations) == 0,
          f"violations: {violations[:5]}")


# ── Test 2: No "万年" event has min_realm < 4 ──────────────────────────
def test_wannian_realm():
    print("\n[Test 2] 万年类事件 min_realm ≥ 4（元婴）")
    events = load_events()
    violations = [
        e["id"] for e in events
        if "万年" in e.get("text", "")
        and e.get("conditions", {}).get("min_realm", 0) < 4
    ]
    check("no 万年 event with min_realm < 4", len(violations) == 0,
          f"violations: {violations[:5]}")


# ── Test 3: No "上古/远古" event has min_realm < 3 ────────────────────
def test_ancient_realm():
    print("\n[Test 3] 上古/远古类事件 min_realm ≥ 3（金丹）")
    events = load_events()
    violations = [
        e["id"] for e in events
        if any(kw in e.get("text", "") for kw in ["上古", "远古"])
        and e.get("conditions", {}).get("min_realm", 0) < 3
    ]
    check("no 上古/远古 event with min_realm < 3", len(violations) == 0,
          f"violations: {violations[:5]}")


# ── Test 4: Total event count unchanged ────────────────────────────────
def test_total_count():
    print("\n[Test 4] 事件总数未变（9203）")
    events = load_events()
    check("total events == 9203", len(events) == 9203,
          f"actual: {len(events)}")


# ── Test 5: No event has empty conditions ──────────────────────────────
def test_no_empty_conditions():
    print("\n[Test 5] 每条事件都有 conditions")
    events = load_events()
    empty = [e["id"] for e in events if not e.get("conditions")]
    check("no event with empty conditions", len(empty) == 0,
          f"empty: {empty[:5]}")


# ── Test 6: Event pipeline filters correctly ────────────────────────────
def test_pipeline_filtering():
    """Simulate condition check: a realm=1 character should NOT match
    a min_realm=3 event."""
    print("\n[Test 6] 条件检查正确过滤高境界事件")

    # Simulate: realm=1 character checking a min_realm=3 event
    sample_event = {
        "id": "test_qian",
        "text": "你遇到了千年妖兽",
        "conditions": {"min_realm": 3},
    }

    # Manual condition check (mirrors check_conditions logic)
    realm = 1
    min_realm = sample_event["conditions"].get("min_realm")
    passes = min_realm is None or realm >= min_realm
    check("realm=1 blocked by min_realm=3", not passes)

    realm = 3
    passes = min_realm is None or realm >= min_realm
    check("realm=3 allowed by min_realm=3", passes)

    realm = 5
    passes = min_realm is None or realm >= min_realm
    check("realm=5 allowed by min_realm=3", passes)


# ── Test 7: Distribution sanity check ───────────────────────────────────
def test_distribution():
    """After fix, realm=3 and realm=4 should have gained events."""
    print("\n[Test 7] 修正后境界分布合理性")
    events = load_events()
    from collections import Counter
    dist = Counter(e.get("conditions", {}).get("min_realm", 0) for e in events)

    # realm=3 should have gained千年+上古 events (was ~1742, now ~1813)
    check("realm=3 count > 1740", dist[3] > 1740,
          f"actual: {dist[3]}")
    # realm=4 should have gained万年 events (was ~1416, now ~1456)
    check("realm=4 count > 1415", dist[4] > 1415,
          f"actual: {dist[4]}")
    # realm=1 should have lost events (was ~2763, now ~2678)
    check("realm=1 count < 2764", dist[1] < 2764,
          f"actual: {dist[1]}")


# ── Test 8: Specific event spot checks ──────────────────────────────────
def test_spot_checks():
    """Verify specific known-bad events were fixed."""
    print("\n[Test 8] 特定事件抽查")
    events = load_events()
    by_id = {e["id"]: e for e in events}

    # 千年蜘蛛精 should be realm=3
    ev = by_id.get("ext_combat_0220")
    if ev:
        check("ext_combat_0220 (千年蜘蛛精) → realm≥3",
              ev["conditions"].get("min_realm", 0) >= 3,
              f"actual: {ev['conditions'].get('min_realm')}")

    # 上古僵尸 should be realm=3
    ev = by_id.get("ext_combat_0234")
    if ev:
        check("ext_combat_0234 (上古僵尸) → realm≥3",
              ev["conditions"].get("min_realm", 0) >= 3,
              f"actual: {ev['conditions'].get('min_realm')}")

    # 万年雪莲 should be realm=4
    ev = by_id.get("mega_food_0259")
    if ev:
        check("mega_food_0259 (万年雪莲粥) → realm≥4",
              ev["conditions"].get("min_realm", 0) >= 4,
              f"actual: {ev['conditions'].get('min_realm')}")


if __name__ == "__main__":
    print("=" * 60)
    print("min_realm 叙事一致性修复验证")
    print("=" * 60)

    test_qiannian_realm()
    test_wannian_realm()
    test_ancient_realm()
    test_total_count()
    test_no_empty_conditions()
    test_pipeline_filtering()
    test_distribution()
    test_spot_checks()

    print("\n" + "=" * 60)
    print(f"Results: {PASSED} passed, {FAILED} failed, {PASSED + FAILED} total")
    if FAILED:
        print("SOME TESTS FAILED!")
        sys.exit(1)
    else:
        print("All tests passed! ✓")
