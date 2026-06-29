"""叙事引擎量化推演模拟器 — 无LLM、纯规则推演N局，输出三维指标报告。

三大维度：
  1. 多样性 (Diversity)    — 事件重复率、类别熵、NPC轮转率
  2. 涌现性 (Emergence)    — Saga形成率、NPC命运推进、因果链活跃度、系统协同度
  3. 叙事质量 (Narrative)  — 张力波动、peril激活率、选择频率、弧线完成率

运行方式：
  cd backend && python3 simulate_metrics.py [--runs 50]
"""
import os
import sys
import math
import random
import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field

# Disable LLM by clearing API key BEFORE imports
os.environ.pop("DEEPSEEK_API_KEY", None)
os.environ["DEEPSEEK_API_KEY"] = ""

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.engine.director import GameDirector
from app.engine.state import create_game, GAME_STATE_STORE


# ── Metrics Collector ─────────────────────────────────────────────────────

@dataclass
class GameMetrics:
    """单局统计数据"""
    # 基础
    total_turns: int = 0
    final_age: int = 0
    final_realm: int = 0
    death_reason: str = ""

    # 多样性
    event_ids: list = field(default_factory=list)
    event_categories: list = field(default_factory=list)
    event_types: list = field(default_factory=list)
    npcs_encountered: set = field(default_factory=set)

    # 涌现性
    sagas_formed: int = 0
    saga_max_momentum: float = 0
    arcs_started: int = 0
    arcs_completed: int = 0
    causal_chains_created: int = 0
    causal_chains_resolved: int = 0
    npc_destiny_beats_advanced: int = 0
    npc_pivots: int = 0

    # 叙事质量
    tension_history: list = field(default_factory=list)
    peril_history: list = field(default_factory=list)
    choices_offered: int = 0
    era_transitions: int = 0

    # 系统协同度（每回合有多少系统同时贡献事件）
    systems_per_turn: list = field(default_factory=list)


def run_single_game(director: GameDirector, max_turns: int = 500) -> GameMetrics:
    """执行一局完整游戏，收集指标。"""
    state = director.start_game()
    game_id = state.game_id
    metrics = GameMetrics()

    for turn in range(max_turns):
        if state.is_dead or state.is_ascended:
            break

        # Snapshot pre-turn state for delta detection
        pre_sagas = len(getattr(state, "sagas", None) or [])
        pre_used_ids = len(state.used_event_ids)
        pre_events_log_len = len(state.events_log)
        pre_destiny_total = sum(
            npc.get("current_destiny_index", 0)
            for npc in state.npc_registry.values()
        )

        try:
            response = director.advance_year(game_id)
        except (ValueError, Exception) as e:
            # Handle pending choice by auto-selecting first branch
            if "Pending choice" in str(e) and state.pending_choice:
                try:
                    director.make_choice(game_id, 0)
                    metrics.choices_offered += 1
                except Exception:
                    state.pending_choice = None
                continue
            break

        metrics.total_turns += 1

        # Track pending choices
        if state.pending_choice is not None:
            metrics.choices_offered += 1
            # Auto-resolve choice for simulation
            try:
                director.make_choice(game_id, random.randint(0, 1))
            except Exception:
                state.pending_choice = None

        # Collect event data from response.events (list[dict])
        for ev_data in (response.events or []):
            category = ev_data.get("category", "")
            ev_type = ev_data.get("type", "")
            if category:
                metrics.event_categories.append(category)
            if ev_type:
                metrics.event_types.append(ev_type)

        # Collect unique event IDs from state.used_event_ids delta
        new_used = len(state.used_event_ids) - pre_used_ids
        metrics.event_ids.extend(list(state.used_event_ids)[-new_used:] if new_used > 0 else [])

        # System co-activation count for this turn
        systems_active = 0
        if getattr(state, "active_era", None):
            systems_active += 1
        if any(s.get("is_active") for s in (getattr(state, "sagas", None) or [])):
            systems_active += 1
        if any(not c.get("is_resolved") for c in (getattr(state, "causal_chains", None) or [])):
            systems_active += 1
        if any(not a.get("is_completed") for a in (getattr(state, "active_arcs", None) or [])):
            systems_active += 1
        if state.peril_index > 30:
            systems_active += 1
        if state.tension > 50:
            systems_active += 1
        metrics.systems_per_turn.append(systems_active)

        # Track NPC encounters
        for npc_id in state.npc_registry:
            metrics.npcs_encountered.add(npc_id)

        # Track tension/peril
        metrics.tension_history.append(state.tension)
        metrics.peril_history.append(state.peril_index)

        # Detect saga formation
        post_sagas = len(getattr(state, "sagas", None) or [])
        if post_sagas > pre_sagas:
            metrics.sagas_formed += post_sagas - pre_sagas

        # Detect arc changes (from completed_arcs_history growth)
        # Track new events_log entries for era transitions
        new_logs = state.events_log[pre_events_log_len:]
        for log in new_logs:
            text = log.get("text", "")
            if "天地大势" in text:
                metrics.era_transitions += 1

        # Count newly resolved chains
        metrics.causal_chains_created = len(getattr(state, "causal_chains", None) or [])
        metrics.causal_chains_resolved = sum(
            1 for c in (getattr(state, "causal_chains", None) or [])
            if c.get("is_resolved")
        )

        # Destiny beats advanced
        post_destiny_total = sum(
            npc.get("current_destiny_index", 0)
            for npc in state.npc_registry.values()
        )
        if post_destiny_total > pre_destiny_total:
            metrics.npc_destiny_beats_advanced += post_destiny_total - pre_destiny_total

    # Final state
    metrics.final_age = state.age
    metrics.final_realm = state.realm
    metrics.death_reason = state.death_reason or ("飞升" if state.is_ascended else "存活")
    metrics.arcs_completed = len(getattr(state, "completed_arcs_history", None) or [])
    metrics.arcs_started = metrics.arcs_completed + len([
        a for a in (getattr(state, "active_arcs", None) or [])
        if not a.get("is_completed")
    ])
    metrics.saga_max_momentum = max(
        (s.get("momentum", 0) for s in (getattr(state, "sagas", None) or [])),
        default=0
    )
    # Overwrite event_ids with accurate final count
    metrics.event_ids = list(state.used_event_ids)
    # NPC pivots
    metrics.npc_pivots = sum(
        len(npc.get("pivot_history", []))
        for npc in state.npc_registry.values()
    )

    # Cleanup
    try:
        GAME_STATE_STORE._store.pop(game_id, None)
    except Exception:
        pass

    return metrics


# ── Aggregate Statistics ──────────────────────────────────────────────────

def shannon_entropy(items: list) -> float:
    """计算列表的Shannon熵（归一化到0-1）"""
    if not items:
        return 0.0
    counter = Counter(items)
    total = len(items)
    n_classes = len(counter)
    if n_classes <= 1:
        return 0.0
    entropy = -sum((c / total) * math.log2(c / total) for c in counter.values())
    max_entropy = math.log2(n_classes)
    return entropy / max_entropy if max_entropy > 0 else 0.0


def compute_aggregate(all_metrics: list[GameMetrics]) -> dict:
    """从多局数据计算聚合指标"""
    n = len(all_metrics)

    # ═══ 1. 多样性 ═══
    pool_utilization = []  # 事件池利用率: used / total_pool
    category_entropies = []
    type_entropies = []
    npc_counts = []
    total_pool_size = 5965  # ALL_EVENTS count

    for m in all_metrics:
        pool_utilization.append(len(set(m.event_ids)) / total_pool_size if m.event_ids else 0)
        category_entropies.append(shannon_entropy(m.event_categories))
        type_entropies.append(shannon_entropy(m.event_types))
        npc_counts.append(len(m.npcs_encountered))

    # ═══ 2. 涌现性 ═══
    saga_rates = [m.sagas_formed for m in all_metrics]
    arc_completions = [m.arcs_completed for m in all_metrics]
    destiny_advances = [m.npc_destiny_beats_advanced for m in all_metrics]
    chain_creates = [m.causal_chains_created for m in all_metrics]
    chain_resolves = [m.causal_chains_resolved for m in all_metrics]
    pivot_counts = [m.npc_pivots for m in all_metrics]
    system_coactivation = []
    for m in all_metrics:
        if m.systems_per_turn:
            system_coactivation.append(sum(m.systems_per_turn) / len(m.systems_per_turn))

    # ═══ 3. 叙事质量 ═══
    tension_volatilities = []
    peril_engagement_rates = []
    choice_rates = []
    era_counts = []

    for m in all_metrics:
        if m.tension_history:
            mean_t = sum(m.tension_history) / len(m.tension_history)
            var_t = sum((x - mean_t) ** 2 for x in m.tension_history) / len(m.tension_history)
            tension_volatilities.append(math.sqrt(var_t))
        if m.peril_history:
            engaged = sum(1 for p in m.peril_history if p > 30)
            peril_engagement_rates.append(engaged / len(m.peril_history))
        if m.total_turns > 0:
            choice_rates.append(m.choices_offered / m.total_turns)
        era_counts.append(m.era_transitions)

    # ═══ 基础统计 ═══
    ages = [m.final_age for m in all_metrics]
    realms = [m.final_realm for m in all_metrics]
    turns = [m.total_turns for m in all_metrics]
    death_reasons = Counter(m.death_reason for m in all_metrics)

    return {
        "基础": {
            "模拟局数": n,
            "平均回合数": f"{_avg(turns):.1f}",
            "平均终局年龄": f"{_avg(ages):.0f}",
            "平均终局境界": f"{_avg(realms):.1f}",
            "死因分布": dict(death_reasons.most_common(8)),
        },
        "多样性(纯规则)": {
            "事件池利用率(used/5965)": f"{_avg(pool_utilization)*100:.1f}%",
            "类别熵(归一化)": f"{_avg(category_entropies):.3f}",
            "类型熵(归一化)": f"{_avg(type_entropies):.3f}",
            "平均NPC遭遇数": f"{_avg(npc_counts):.1f}",
        },
        "涌现性(需LLM时标★)": {
            "★平均Saga形成数": f"{_avg(saga_rates):.2f}",
            "★平均弧线完成数": f"{_avg(arc_completions):.1f}",
            "★平均NPC命运推进拍": f"{_avg(destiny_advances):.1f}",
            "★平均NPC命运转折(pivot)": f"{_avg(pivot_counts):.2f}",
            "★平均因果链创建": f"{_avg(chain_creates):.1f}",
            "★平均因果链解决": f"{_avg(chain_resolves):.1f}",
            "系统协同度(每回合)": f"{_avg(system_coactivation):.2f}/6",
        },
        "叙事质量(纯规则)": {
            "张力波动(std)": f"{_avg(tension_volatilities):.1f}",
            "peril激活率(>30)": f"{_avg(peril_engagement_rates)*100:.1f}%",
            "选择频率(每回合)": f"{_avg(choice_rates)*100:.1f}%",
            "纪元转换次数": f"{_avg(era_counts):.1f}",
        },
    }


def _avg(lst):
    return sum(lst) / len(lst) if lst else 0


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="叙事引擎量化推演")
    parser.add_argument("--runs", type=int, default=50, help="模拟局数")
    args = parser.parse_args()

    print(f"═══ 叙事引擎量化推演 ({args.runs}局, 无LLM纯规则) ═══\n")

    director = GameDirector()
    all_metrics: list[GameMetrics] = []

    for i in range(args.runs):
        m = run_single_game(director)
        all_metrics.append(m)
        # Progress indicator
        realm_names = ["凡人", "练气", "筑基", "金丹", "元婴", "化神"]
        rn = realm_names[m.final_realm] if m.final_realm < len(realm_names) else f"R{m.final_realm}"
        status = f"局{i+1:3d}: {m.total_turns:3d}回合 | 年龄{m.final_age:4d} | {rn} | {m.death_reason}"
        print(status)

    print("\n" + "═" * 60)
    print("             聚合统计报告")
    print("═" * 60)

    report = compute_aggregate(all_metrics)
    for section, data in report.items():
        print(f"\n【{section}】")
        for key, val in data.items():
            if isinstance(val, dict):
                print(f"  {key}:")
                for k, v in val.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {val}")

    # ── 综合评分 ──
    print("\n" + "═" * 60)
    print("             综合评分")
    print("═" * 60)

    diversity_score = _score_diversity(report)
    emergence_score = _score_emergence(report)
    narrative_score = _score_narrative(report)
    total = (diversity_score + emergence_score + narrative_score) / 3

    print(f"  多样性:   {diversity_score:.1f}/10")
    print(f"  涌现性:   {emergence_score:.1f}/10")
    print(f"  叙事质量: {narrative_score:.1f}/10")
    print(f"  ────────────────")
    print(f"  总评:     {total:.1f}/10")


def _score_diversity(report: dict) -> float:
    """多样性评分 0-10"""
    score = 0.0
    d = report["多样性(纯规则)"]
    # 事件池利用率: 2%+ = 10 (100+/5965), 1% = 6
    util = float(d["事件池利用率(used/5965)"].rstrip("%")) / 100
    score += min(10, util * 500)  # 2% = 10
    # 类别熵: 0.8+ = 10, 0.6 = 7
    entropy = float(d["类别熵(归一化)"])
    score += min(10, entropy * 12)
    # NPC数: 10+ = 10, 5 = 5
    npc = float(d["平均NPC遭遇数"])
    score += min(10, npc * 1.0)
    return score / 3


def _score_emergence(report: dict) -> float:
    """涌现性评分 0-10 (★标项在无LLM下为0，仅评系统协同)"""
    d = report["涌现性(需LLM时标★)"]
    # 无LLM时仅有系统协同度可评
    coact = float(d["系统协同度(每回合)"].split("/")[0])
    return min(10, coact * 3.3)


def _score_narrative(report: dict) -> float:
    """叙事质量评分 0-10"""
    score = 0.0
    d = report["叙事质量(纯规则)"]
    # 张力波动: 15-25最佳(=10), <10或>35差(=5)
    vol = float(d["张力波动(std)"])
    if 15 <= vol <= 25:
        score += 10
    elif 10 <= vol <= 35:
        score += 7
    else:
        score += 4
    # peril激活率: 20-50%最佳
    peril = float(d["peril激活率(>30)"].rstrip("%")) / 100
    if 0.2 <= peril <= 0.5:
        score += 10
    elif 0.1 <= peril <= 0.6:
        score += 7
    else:
        score += 4
    # 选择频率: 10-30%最佳
    choice = float(d["选择频率(每回合)"].rstrip("%")) / 100
    if 0.1 <= choice <= 0.3:
        score += 10
    elif 0.05 <= choice <= 0.4:
        score += 7
    else:
        score += 4
    return score / 3


if __name__ == "__main__":
    main()
