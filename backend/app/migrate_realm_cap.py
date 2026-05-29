"""One-off migration: cap realm system at 化神 (5) and adapt events.

Run from project root:
    python -m backend.app.migrate_realm_cap
or:
    python backend/app/migrate_realm_cap.py
"""
import json
import os
import shutil
from typing import Any

EVENTS_DIR = os.path.join(os.path.dirname(__file__), "events")
TARGET = os.path.join(EVENTS_DIR, "all_events.json")
BACKUP = os.path.join(EVENTS_DIR, "all_events.backup.json")

# Specific event IDs whose narrative is built around 飞升劫/合体/大乘/渡劫 期 — drop or rewrite.
DROP_BREAKTHROUGH_PREFIXES = ("breakthrough_002", "breakthrough_003", "breakthrough_004")
# breakthrough_0025..0029 (合体), 0030..0034 (大乘), 0035..0039 (渡劫), 0040..0044 (飞升)

REWRITE_TABLE: dict[str, dict[str, Any]] = {
    "high_009": {
        "text": "你感应到一线空间节点的气息，心头剧震。",
        "expanded_text": (
            "化神之巅的修为让你的神识能扫过这方天地几乎每一寸虚空。"
            "这一日打坐之际, 你忽然感应到极远处一缕几乎察觉不到的空间涟漪——"
            "那是传说中的空间节点掠过的痕迹。你心头剧震: 那扇通往仙路的门, 真的存在。"
            "你睁开眼时, 涟漪早已消散, 可你已经知道——只要再等下去, 它终会再次现身。"
        ),
    },
    "death_high_005": {
        # 飞升失败 -> 渡劫陨落
        "text": "你寻得空间节点踏入渡劫飞升, 却未能挡过最后一道紫雷。",
        "death_reason": "渡劫陨落",
        "expanded_text": (
            "那一道空间节点你苦等千年, 终于在某个黄昏显现。"
            "你纵身踏入, 九重雷劫接连降下。"
            "你扛住了前八道——真元尽散, 法器俱碎, 可你仍咬牙不退。"
            "第九道紫雷劈下时, 你只觉天地为之一暗。"
            "云开雾散后, 空间节点闭合如初, 你的修为、道果, 尽数化作云端一缕青烟。"
        ),
    },
    "death_high_004": {
        # 九道天劫齐降 -> 渡劫陨落 (clamp realm)
        "death_reason": "渡劫陨落",
    },
    "death_high_006": {
        # 高维抹杀 - keep narrative but clamp realm
    },
}

# Realm references in narrative that should be re-mapped (text-level).
# Used selectively where breakthrough events were preserved but mention old realms.
NARRATIVE_REPLACE = [
    # No project-wide replacement; we only rewrite via REWRITE_TABLE.
]


def clamp_realm(cond: dict, key: str, cap: int = 5) -> bool:
    """Clamp a min_realm/max_realm key to <= cap. Returns True if changed."""
    val = cond.get(key)
    if isinstance(val, int) and val > cap:
        cond[key] = cap
        return True
    return False


def migrate(events: list[dict]) -> tuple[list[dict], dict[str, int]]:
    stats = {"dropped_breakthrough": 0, "clamped_min_realm": 0, "clamped_max_realm": 0,
            "rewritten": 0, "kept": 0}
    out: list[dict] = []

    for ev in events:
        eid = ev.get("id", "")

        # 1) Drop obsolete breakthrough events (合体/大乘/渡劫/飞升 期)
        if any(eid.startswith(p) for p in DROP_BREAKTHROUGH_PREFIXES):
            stats["dropped_breakthrough"] += 1
            continue

        # 2) Apply targeted rewrites
        if eid in REWRITE_TABLE:
            for k, v in REWRITE_TABLE[eid].items():
                ev[k] = v
            stats["rewritten"] += 1

        # 3) Clamp realm conditions
        cond = ev.get("conditions") or {}
        if clamp_realm(cond, "min_realm"):
            stats["clamped_min_realm"] += 1
        if clamp_realm(cond, "max_realm"):
            stats["clamped_max_realm"] += 1

        stats["kept"] += 1
        out.append(ev)

    return out, stats


def main() -> None:
    if not os.path.exists(TARGET):
        raise SystemExit(f"all_events.json not found at {TARGET}")

    with open(TARGET, "r", encoding="utf-8") as f:
        events = json.load(f)

    if not os.path.exists(BACKUP):
        shutil.copy(TARGET, BACKUP)
        print(f"Backup written to {BACKUP}")

    print(f"Loaded {len(events)} events.")
    new_events, stats = migrate(events)
    print(f"Migration stats: {stats}")
    print(f"Final count: {len(new_events)}")

    with open(TARGET, "w", encoding="utf-8") as f:
        json.dump(new_events, f, ensure_ascii=False, indent=2)
    print(f"Wrote {TARGET}")


if __name__ == "__main__":
    main()
