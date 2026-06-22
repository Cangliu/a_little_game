"""Event Annotator — auto-tag events with npc_slot and replace hardcoded names with placeholders.

Run this script to annotate all_events.json with:
1. npc_slot field (master/lover/rival/fellow/friend/elder/any_known/null)
2. Text placeholders ({master}, {rival}, etc.) replacing hardcoded role names
3. creates_hook / resolves_hook for ~200 cause-effect event pairs

Usage:
    python -m app.event_annotator
"""
import json
import re
import os
import copy
from pathlib import Path
from typing import Optional, Tuple

# ── NPC Slot Detection Rules ─────────────────────────────────────────────────

# Keywords that indicate a specific NPC slot requirement
SLOT_RULES = {
    "master": {
        "keywords": ["师父", "师尊", "传授", "指点", "教导", "恩师", "掌门", "拜师", "收徒"],
        "placeholder": "{master}",
        "replacements": ["师父", "师尊", "恩师"],
    },
    "lover": {
        "keywords": ["道侣", "双修", "心仪之人", "伴侣", "红颜", "知己", "情投意合"],
        "placeholder": "{lover}",
        "replacements": ["道侣", "心仪之人"],
    },
    "rival": {
        "keywords": ["宿敌", "死对头", "仇家", "仇人", "死敌", "劲敌"],
        "placeholder": "{rival}",
        "replacements": ["宿敌", "仇家", "仇人", "死敌", "劲敌"],
    },
    "fellow": {
        "keywords": ["同门", "师兄", "师弟", "师姐", "师妹", "同窗"],
        "placeholder": "{fellow}",
        "replacements": ["同门师兄", "同门师弟", "同门师姐", "同门师妹", "同门"],
    },
    "friend": {
        "keywords": ["挚友", "好友", "至交", "结伴", "同行"],
        "placeholder": "{friend}",
        "replacements": ["挚友", "好友", "至交"],
    },
    "elder": {
        "keywords": ["前辈", "长老", "老者", "高人", "仙人指点", "路过的修士"],
        "placeholder": "{elder}",
        "replacements": ["前辈", "一位长老", "一位老者"],
    },
    "any_known": {
        "keywords": ["故人", "老友", "多年未见", "久别重逢", "旧识", "故交"],
        "placeholder": "{known_npc}",
        "replacements": ["故人", "老友", "旧识"],
    },
}

# ── Hook Templates (Cause-Effect Pairs) ──────────────────────────────────────

# Define hook archetypes that can be created and resolved
HOOK_ARCHETYPES = [
    # Master-related
    {
        "id": "master_secret",
        "create_keywords": ["师父.*秘密", "师父.*隐瞒", "师尊.*离去", "师父.*失踪"],
        "resolve_keywords": ["真相.*师父", "发现.*师父", "师父.*回归"],
        "description": "师父的秘密",
        "max_wait": 100,
        "npc_slot": "master",
    },
    {
        "id": "master_injured",
        "create_keywords": ["师父.*受伤", "师父.*重伤", "师尊.*遇袭"],
        "resolve_keywords": ["替师.*报仇", "为师.*复仇", "仇人.*伏诛"],
        "description": "替师报仇",
        "max_wait": 80,
        "npc_slot": "master",
    },
    # Rival-related
    {
        "id": "rival_humiliation",
        "create_keywords": ["被.*羞辱", "惨败", "不敌.*对手", "宿敌.*挑衅"],
        "resolve_keywords": ["击败.*宿敌", "一雪前耻", "复仇成功"],
        "description": "一雪前耻",
        "max_wait": 120,
        "npc_slot": "rival",
    },
    # Treasure / Secret
    {
        "id": "mysterious_map",
        "create_keywords": ["残图", "藏宝图", "神秘地图", "古图"],
        "resolve_keywords": ["按图.*寻找", "地图.*指引", "图中.*之地"],
        "description": "破解古图之谜",
        "max_wait": 100,
        "npc_slot": None,
    },
    {
        "id": "incomplete_technique",
        "create_keywords": ["残缺功法", "残篇", "功法.*不全", "缺失.*后半"],
        "resolve_keywords": ["功法.*补全", "完整.*功法", "残篇.*合一"],
        "description": "补全残缺功法",
        "max_wait": 150,
        "npc_slot": None,
    },
    # Lover-related
    {
        "id": "lover_separation",
        "create_keywords": ["道侣.*离别", "被迫分离", "天各一方"],
        "resolve_keywords": ["道侣.*重逢", "终于.*再会", "再次.*相见"],
        "description": "与道侣重逢",
        "max_wait": 80,
        "npc_slot": "lover",
    },
    # Self-cultivation
    {
        "id": "inner_demon",
        "create_keywords": ["心魔.*种下", "心魔.*萌芽", "执念.*深种"],
        "resolve_keywords": ["心魔.*化解", "斩断.*心魔", "放下.*执念"],
        "description": "化解心魔",
        "max_wait": 100,
        "npc_slot": None,
    },
    {
        "id": "tribulation_preparation",
        "create_keywords": ["天劫.*预兆", "劫云.*隐现", "天劫.*临近"],
        "resolve_keywords": ["渡劫.*成功", "天劫.*化解", "劫后重生"],
        "description": "渡过天劫",
        "max_wait": 60,
        "npc_slot": None,
    },
    # World events
    {
        "id": "sect_crisis",
        "create_keywords": ["宗门.*危机", "宗门.*被攻", "大敌.*来犯"],
        "resolve_keywords": ["宗门.*化险", "击退.*来敌", "宗门.*重建"],
        "description": "化解宗门危机",
        "max_wait": 50,
        "npc_slot": None,
    },
    {
        "id": "cursed_artifact",
        "create_keywords": ["诅咒.*法器", "邪物.*入体", "被.*侵蚀"],
        "resolve_keywords": ["诅咒.*解除", "邪物.*净化", "侵蚀.*消退"],
        "description": "解除诅咒",
        "max_wait": 60,
        "npc_slot": None,
    },
]


# Additional keywords for broader social event detection
SOCIAL_NPC_KEYWORDS = [
    "切磋", "论道", "交流", "相遇", "来访", "邀请", "比试", "对弈",
    "共饮", "赠送", "馈赠", "求助", "帮助", "救助", "合作",
    "同行", "偶遇", "邂逅", "造访", "拜访", "请教", "讨论",
    "宴会", "聚会", "接待", "送别", "迎接", "托付", "委托",
    "交易", "买卖", "换取", "与人", "某人", "一位修士", "路人",
    "陌生人", "来客", "访客", "门客", "友人", "熟人", "邻居",
]


def detect_npc_slot(event: dict) -> Optional[str]:
    """Detect which NPC slot an event requires based on text/tags/category."""
    text = event.get("text", "") + " " + event.get("expanded_text", "")
    tags = set(event.get("tags", []))
    category = event.get("category", "")

    # Check tag-based rules first (most reliable)
    tag_to_slot = {
        "master_event": "master",
        "lover_event": "lover",
        "rival_event": "rival",
        "fellow_event": "fellow",
        "npc_interaction": None,  # generic, will check text
    }
    for tag, slot in tag_to_slot.items():
        if tag in tags and slot:
            return slot

    # Check keyword-based rules (order matters: more specific first)
    # Priority: master > lover > rival > fellow > any_known > friend > elder
    priority_order = ["master", "lover", "rival", "fellow", "any_known", "friend", "elder"]

    for slot_name in priority_order:
        rule = SLOT_RULES[slot_name]
        if any(kw in text for kw in rule["keywords"]):
            return slot_name

    # For social-category events without specific slot, assign "any_known"
    if category == "social":
        # Check if event implies any person interaction
        if any(kw in text for kw in SOCIAL_NPC_KEYWORDS):
            return "any_known"
        # Social events almost always involve someone
        return "any_known"

    # Check for general NPC keywords in non-social events
    if any(kw in text for kw in SOCIAL_NPC_KEYWORDS):
        return "any_known"

    return None


def apply_placeholder(text: str, slot: str) -> str:
    """Replace hardcoded role names with placeholders in event text."""
    if not slot or slot not in SLOT_RULES:
        return text

    rule = SLOT_RULES[slot]
    placeholder = rule["placeholder"]

    # Only replace the FIRST occurrence of a role-specific noun
    # to avoid double-replacing in long expanded_text
    for old_word in rule["replacements"]:
        if old_word in text:
            # Replace first occurrence only
            text = text.replace(old_word, placeholder, 1)
            break

    return text


def detect_hooks(event: dict) -> Tuple[Optional[dict], Optional[str]]:
    """Detect if an event creates or resolves a plot hook.

    Returns (creates_hook_dict_or_None, resolves_hook_id_or_None)
    """
    text = event.get("text", "") + " " + event.get("expanded_text", "")

    creates = None
    resolves = None

    for archetype in HOOK_ARCHETYPES:
        # Check creates
        for pattern in archetype["create_keywords"]:
            if re.search(pattern, text):
                creates = {
                    "id": archetype["id"],
                    "description": archetype["description"],
                    "max_wait": archetype["max_wait"],
                }
                break

        # Check resolves
        for pattern in archetype["resolve_keywords"]:
            if re.search(pattern, text):
                resolves = archetype["id"]
                break

    # Don't let same event both create and resolve the SAME hook
    if creates and resolves and creates["id"] == resolves:
        resolves = None

    return creates, resolves


def annotate_events(events: list) -> list:
    """Annotate all events with npc_slot, placeholders, and hooks."""
    annotated = []
    stats = {"total": 0, "with_slot": 0, "creates_hook": 0, "resolves_hook": 0}
    slot_counts = {}

    for event in events:
        ev = copy.deepcopy(event)
        stats["total"] += 1

        # 1. Detect NPC slot
        slot = detect_npc_slot(ev)
        if slot:
            ev["npc_slot"] = slot
            stats["with_slot"] += 1
            slot_counts[slot] = slot_counts.get(slot, 0) + 1

            # 2. Apply placeholder to text fields
            ev["text"] = apply_placeholder(ev["text"], slot)
            if ev.get("expanded_text"):
                ev["expanded_text"] = apply_placeholder(ev["expanded_text"], slot)

        # 3. Detect hooks
        creates, resolves = detect_hooks(ev)
        if creates:
            ev["creates_hook"] = creates
            stats["creates_hook"] += 1
        if resolves:
            ev["resolves_hook"] = resolves
            stats["resolves_hook"] += 1

        annotated.append(ev)

    print(f"\n=== Annotation Stats ===")
    print(f"Total events: {stats['total']}")
    print(f"Events with npc_slot: {stats['with_slot']} ({stats['with_slot']*100//stats['total']}%)")
    print(f"Events creating hooks: {stats['creates_hook']}")
    print(f"Events resolving hooks: {stats['resolves_hook']}")
    print(f"\nSlot distribution:")
    for slot, count in sorted(slot_counts.items(), key=lambda x: -x[1]):
        print(f"  {slot:12s}: {count}")

    return annotated


def main():
    """Run annotation on all_events.json."""
    events_path = Path(__file__).parent / "events" / "all_events.json"

    print(f"Loading events from: {events_path}")
    with open(events_path, "r", encoding="utf-8") as f:
        events = json.load(f)

    print(f"Loaded {len(events)} events")

    # Annotate
    annotated = annotate_events(events)

    # Write back
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(annotated, f, ensure_ascii=False, indent=2)

    print(f"\nAnnotated events written to: {events_path}")


if __name__ == "__main__":
    main()
