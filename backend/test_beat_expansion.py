#!/usr/bin/env python3
"""Tests for destiny beat expansion from 6 to 13.

Validates:
1. All archetypes produce 13 beats
2. Beat realm distribution covers 1-5
3. Total keywords >= 25
4. Every beat type has >= 3 variants
5. LLM parser handles 12-15 beat JSON correctly
6. _BEAT_REALM mapping is complete

No LLM calls — pure rule-based validation.
"""
import json
import os
import sys
import random

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


# ── Test 1: All archetypes produce 13 beats ────────────────────────────
def test_archetype_beat_count():
    print("\n[Test 1] 每种原型生成13拍")
    from app.engine.main_storyline import (
        ARCHETYPE_STORYLINES, _BEAT_VARIANTS, _BEAT_REALM,
    )

    for name, template in ARCHETYPE_STORYLINES.items():
        seq = template["beat_sequence"]
        check(f"{name}: {len(seq)} beats == 13", len(seq) == 13,
              f"actual: {len(seq)}, seq: {seq}")

        # Verify every beat in sequence exists in _BEAT_VARIANTS
        for beat_key in seq:
            check(f"{name}: '{beat_key}' in _BEAT_VARIANTS",
                  beat_key in _BEAT_VARIANTS,
                  f"missing: {beat_key}")


# ── Test 2: Realm distribution covers 1-5 ──────────────────────────────
def test_realm_coverage():
    print("\n[Test 2] 每种原型的realm分布覆盖1-5")
    from app.engine.main_storyline import ARCHETYPE_STORYLINES, _BEAT_REALM

    for name, template in ARCHETYPE_STORYLINES.items():
        seq = template["beat_sequence"]
        realms = {_BEAT_REALM.get(k, 0) for k in seq}
        check(f"{name}: realms cover {{1,2,3,4,5}}",
              {1, 2, 3, 4, 5}.issubset(realms),
              f"actual: {sorted(realms)}")


# ── Test 3: Total keywords >= 25 per archetype ─────────────────────────
def test_keyword_count():
    print("\n[Test 3] 每种原型的关键词总数 >= 25")
    from app.engine.main_storyline import (
        ARCHETYPE_STORYLINES, _BEAT_VARIANTS,
    )

    for name, template in ARCHETYPE_STORYLINES.items():
        seq = template["beat_sequence"]
        total_kw = 0
        for beat_key in seq:
            variants = _BEAT_VARIANTS[beat_key]
            # Pick a random variant (worst case analysis: use min)
            min_kw = min(len(v["kw"]) for v in variants)
            total_kw += min_kw
        check(f"{name}: min keywords >= 25", total_kw >= 25,
              f"actual min: {total_kw}")


# ── Test 4: Every beat type has >= 3 variants ───────────────────────────
def test_variant_count():
    print("\n[Test 4] 每种节拍类型有 >= 3 个变体")
    from app.engine.main_storyline import _BEAT_VARIANTS

    for beat_type, variants in _BEAT_VARIANTS.items():
        check(f"{beat_type}: {len(variants)} variants >= 3",
              len(variants) >= 3,
              f"actual: {len(variants)}")


# ── Test 5: _BEAT_REALM mapping complete ────────────────────────────────
def test_realm_mapping():
    print("\n[Test 5] _BEAT_REALM 映射完整")
    from app.engine.main_storyline import _BEAT_VARIANTS, _BEAT_REALM

    for beat_type in _BEAT_VARIANTS:
        check(f"{beat_type} has realm mapping",
              beat_type in _BEAT_REALM,
              f"missing from _BEAT_REALM")

    # Verify realm values are in 1-5
    for beat_type, realm in _BEAT_REALM.items():
        check(f"{beat_type}: realm={realm} in [1,5]",
              1 <= realm <= 5,
              f"actual: {realm}")


# ── Test 6: Fallback generation produces 13 beats ──────────────────────
def test_fallback_generation():
    print("\n[Test 6] 降级生成产出13拍")
    from app.engine.main_storyline import MainStorylinePlanner

    # Create planner without LLM (pure fallback)
    planner = MainStorylinePlanner()

    # Mock a minimal GameState
    class MockAttrs:
        constitution = 3
        comprehension = 4
        fortune = 5
        charisma = 2
        willpower = 6
        lifespan = 10

    class MockState:
        main_storyline = None
        realm = 1
        age = 15
        gender = "male"
        talents = ["灵根"]
        attributes = MockAttrs()
        biography_summary = ""

    state = MockState()
    storyline = planner.generate_storyline(state)

    beats = storyline.get("destiny_beats", [])
    check(f"fallback beats count == 13", len(beats) == 13,
          f"actual: {len(beats)}")

    # Check beat 0 auto-completed
    check("beat 0 auto-completed", beats[0].get("is_completed", False))
    check("current_beat_index == 1",
          storyline.get("current_beat_index") == 1,
          f"actual: {storyline.get('current_beat_index')}")

    # Check total keywords
    total_kw = sum(len(b.get("keywords", [])) for b in beats)
    check(f"total keywords ({total_kw}) >= 25", total_kw >= 25)

    # Check realm distribution
    realms = {b.get("target_realm", 0) for b in beats}
    check("realms cover {1,2,3,4,5}", {1, 2, 3, 4, 5}.issubset(realms),
          f"actual: {sorted(realms)}")


# ── Test 7: LLM parser handles 13-beat JSON ─────────────────────────────
def test_llm_parser():
    print("\n[Test 7] LLM解析器处理13拍JSON")
    from app.engine.main_storyline import MainStorylinePlanner, KEYWORD_PALETTE

    planner = MainStorylinePlanner()

    # Build a realistic palette
    palette = []
    for words in KEYWORD_PALETTE.values():
        palette.extend(words)

    # Simulate LLM response with 13 beats
    beats_json = []
    realms = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5]
    descs = [
        "灵根觉醒", "初修入门", "历练红尘",
        "宗门生活", "筑基之路", "秘境试炼",
        "寻觅机缘", "金丹凝结", "劫难降临",
        "实力飞跃", "元婴显化", "恩怨了结",
        "渡劫飞升",
    ]
    for i in range(13):
        kws = random.sample(palette, 3)
        beats_json.append({
            "description": descs[i],
            "target_realm": realms[i],
            "keywords": kws,
        })

    mock_response = json.dumps({
        "archetype": "天命修仙",
        "description": "你生来便注定了非凡的修仙之路",
        "beats": beats_json,
    }, ensure_ascii=False)

    class MockState:
        realm = 1
        age = 15

    result = planner._parse_llm_storyline(
        mock_response, MockState(), set(palette)
    )

    check("parse succeeded", result is not None)
    if result:
        parsed_beats = result.get("destiny_beats", [])
        check(f"parsed {len(parsed_beats)} beats == 13",
              len(parsed_beats) == 13,
              f"actual: {len(parsed_beats)}")

        total_kw = sum(len(b.get("keywords", [])) for b in parsed_beats)
        check(f"parsed keywords ({total_kw}) >= 25", total_kw >= 25)


# ── Test 8: LLM parser rejects too few beats ────────────────────────────
def test_parser_rejects_short():
    print("\n[Test 8] LLM解析器拒绝<8拍的响应")
    from app.engine.main_storyline import MainStorylinePlanner

    planner = MainStorylinePlanner()

    # 5 beats (old format) should be rejected
    mock_response = json.dumps({
        "archetype": "天命",
        "description": "测试",
        "beats": [
            {"description": f"节拍{i}", "target_realm": i, "keywords": ["修炼"]}
            for i in range(5)
        ],
    }, ensure_ascii=False)

    class MockState:
        realm = 1
        age = 15

    result = planner._parse_llm_storyline(mock_response, MockState())
    check("5-beat response rejected (returns None)", result is None)


# ── Test 9: Realm monotonicity in archetype sequences ────────────────────
def test_realm_monotonicity():
    print("\n[Test 9] 原型序列的realm单调递增")
    from app.engine.main_storyline import ARCHETYPE_STORYLINES, _BEAT_REALM

    for name, template in ARCHETYPE_STORYLINES.items():
        seq = template["beat_sequence"]
        realms = [_BEAT_REALM[k] for k in seq]
        is_monotonic = all(realms[i] <= realms[i + 1] for i in range(len(realms) - 1))
        check(f"{name}: realm sequence non-decreasing",
              is_monotonic,
              f"realms: {realms}")


# ── Test 10: Keyword palette coverage ──────────────────────────────────
def test_palette_coverage():
    print("\n[Test 10] 所有变体关键词都在KEYWORD_PALETTE中")
    from app.engine.main_storyline import _BEAT_VARIANTS, KEYWORD_PALETTE

    all_palette_kw = set()
    for words in KEYWORD_PALETTE.values():
        all_palette_kw.update(words)

    missing = []
    for beat_type, variants in _BEAT_VARIANTS.items():
        for v in variants:
            for kw in v["kw"]:
                if kw not in all_palette_kw:
                    missing.append((beat_type, kw))

    check(f"all variant keywords in palette ({len(missing)} missing)",
          len(missing) == 0,
          f"missing: {missing[:5]}")


if __name__ == "__main__":
    # Add backend to path
    sys.path.insert(0, os.path.dirname(__file__))

    print("=" * 60)
    print("命运节拍扩展验证 (6拍 → 13拍)")
    print("=" * 60)

    test_archetype_beat_count()
    test_realm_coverage()
    test_keyword_count()
    test_variant_count()
    test_realm_mapping()
    test_fallback_generation()
    test_llm_parser()
    test_parser_rejects_short()
    test_realm_monotonicity()
    test_palette_coverage()

    print("\n" + "=" * 60)
    print(f"Results: {PASSED} passed, {FAILED} failed, {PASSED + FAILED} total")
    if FAILED:
        print("SOME TESTS FAILED!")
        sys.exit(1)
    else:
        print("All tests passed! ✓")
