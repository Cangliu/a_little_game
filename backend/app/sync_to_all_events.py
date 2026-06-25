"""
主从同步脚本：从各独立分类文件汇总生成 all_events.json

架构：
  - 主（Source of Truth）：各独立分类文件（cultivation.json, fortune.json, ...）
  - 从（Derived）：all_events.json —— 由本脚本从主文件合并生成，游戏引擎唯一加载此文件

用法：
  python sync_to_all_events.py          # 合并所有独立文件 → all_events.json
  python sync_to_all_events.py --check  # 仅检查，不写入

注意：
  - breakthrough.json 为 dict 格式，由 realm_system.py 单独加载，不参与合并
  - all_events.backup*.json 为备份文件，不参与合并
"""
import json
import os
import sys
from pathlib import Path
from collections import Counter

EVENTS_DIR = Path(__file__).parent / "events"
OUTPUT_FILE = EVENTS_DIR / "all_events.json"

# 不参与合并的文件
EXCLUDE_FILES = {
    'all_events.json',
    'all_events.backup.json',
    'all_events.backup_pre_dedup.json',
    'breakthrough.json',
}

# 各独立文件及其预期 category（用于完整性校验）
SOURCE_FILES = [
    ('cultivation.json', {'cultivation'}),
    ('fortune.json', {'fortune'}),
    ('social.json', {'social'}),
    ('calamity.json', {'calamity'}),
    ('common.json', {'common', 'death', 'exploration'}),
    ('world.json', {'world'}),
    ('death.json', {'death'}),
    ('adult.json', {'adult', 'cultivation', 'calamity', 'exploration', 'social'}),
    ('npc_exclusive.json', {'social'}),
    ('violence.json', {'calamity'}),
]


def load_source_files():
    """加载所有独立分类文件，返回事件列表和统计信息"""
    all_events = []
    file_stats = {}
    id_source = {}  # 记录每个 ID 来自哪个文件（检测重复）

    for fname, expected_cats in SOURCE_FILES:
        fpath = EVENTS_DIR / fname
        if not fpath.exists():
            print(f"  [WARN] 文件不存在: {fname}")
            continue

        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"  [SKIP] {fname} 不是数组格式")
            continue

        count = 0
        dupes = 0
        for ev in data:
            eid = ev['id']
            if eid in id_source:
                dupes += 1
                # 后来的文件不覆盖（先出现的优先）
                continue
            id_source[eid] = fname
            all_events.append(ev)
            count += 1

        file_stats[fname] = {'loaded': count, 'dupes': dupes, 'total': len(data)}

    return all_events, file_stats, id_source


def check_for_unknown_files():
    """检查是否有未纳入 SOURCE_FILES 的 JSON 文件"""
    known = EXCLUDE_FILES | {f for f, _ in SOURCE_FILES}
    unknown = []
    for fname in os.listdir(EVENTS_DIR):
        if fname.endswith('.json') and fname not in known:
            unknown.append(fname)
    return unknown


def main():
    check_only = '--check' in sys.argv

    print("=" * 60)
    print("事件池主从同步" + ("（检查模式）" if check_only else ""))
    print("=" * 60)

    # 检查未知文件
    unknown = check_for_unknown_files()
    if unknown:
        print(f"\n[WARN] 发现未纳入的 JSON 文件: {unknown}")
        print("  如需纳入，请在 SOURCE_FILES 中添加配置")

    # 加载所有源文件
    print("\n加载源文件:")
    all_events, file_stats, id_source = load_source_files()

    for fname, stats in file_stats.items():
        dupe_info = f" ({stats['dupes']} 重复已跳过)" if stats['dupes'] else ""
        print(f"  {fname:<25} {stats['loaded']:>5} 个事件{dupe_info}")

    print(f"\n合计: {len(all_events)} 个唯一事件")

    # 质量统计
    lengths = [len(ev.get('expanded_text', '')) for ev in all_events]
    empty = sum(1 for l in lengths if l == 0)
    short = sum(1 for l in lengths if 0 < l < 100)
    print(f"expanded_text: empty={empty}, <100字={short}, avg={sum(lengths)//max(len(lengths),1)}")

    # 境界分布
    realm_names = {0: '凡人', 1: '练气', 2: '筑基', 3: '金丹', 4: '元婴', 5: '化神'}
    realm_dist = Counter(ev.get('conditions', {}).get('min_realm', 0) for ev in all_events)
    print("\n境界分布:")
    for r in range(6):
        cnt = realm_dist.get(r, 0)
        pct = cnt * 100 / max(len(all_events), 1)
        print(f"  {realm_names.get(r, f'R{r}')}: {cnt:>5} ({pct:.1f}%)")

    # category 分布
    cat_dist = Counter(ev.get('category', '?') for ev in all_events)
    print("\ncategory分布:")
    for cat, cnt in cat_dist.most_common():
        print(f"  {cat:<15} {cnt:>5}")

    # 对比现有 all_events.json
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            old_events = json.load(f)
        old_ids = {ev['id'] for ev in old_events}
        new_ids = {ev['id'] for ev in all_events}
        added = new_ids - old_ids
        removed = old_ids - new_ids
        if added or removed:
            print(f"\n与现有 all_events.json 差异:")
            print(f"  新增: {len(added)}, 移除: {len(removed)}")
        else:
            print(f"\n与现有 all_events.json 一致（{len(old_events)}条）")

    if check_only:
        print("\n[CHECK] 检查完毕，未写入文件")
        return

    # 写入
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)

    print(f"\n已写入: {OUTPUT_FILE}")
    print(f"总计: {len(all_events)} 个事件")


if __name__ == '__main__':
    main()
