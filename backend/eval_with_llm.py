"""有LLM的叙事质量评估脚本 — 跑3局，收集LLM特有指标。

运行：cd backend && python3 eval_with_llm.py
"""
import os
import sys
import random
import time

# Load .env
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from app.engine.director import GameDirector
from app.engine.state import GAME_STATE_STORE
from app.models import Realm, REALM_NAMES

NUM_GAMES = 3
MAX_TURNS = 80  # 足够覆盖练气到化神


def run_game(game_idx: int) -> dict:
    """Run a single game with LLM, return metrics."""
    director = GameDirector()
    state = director.start_game()
    game_id = state.game_id

    metrics = {
        "turns": 0,
        "choices_offered": 0,
        "choices_made": 0,
        "causal_chains_created": 0,
        "causal_chains_resolved": 0,
        "sagas_formed": 0,
        "arcs_completed": 0,
        "ai_enhanced_turns": 0,
        "npc_pivots": 0,
        "final_realm": 0,
        "final_age": 0,
        "death_reason": "",
        "peril_max": 0,
        "peril_above30_turns": 0,
        "sample_events": [],
    }

    for turn in range(MAX_TURNS):
        if state.is_dead or state.is_ascended:
            break

        try:
            response = director.advance_year(game_id)
        except Exception as e:
            if "Pending choice" in str(e) and state.pending_choice:
                try:
                    director.make_choice(game_id, random.randint(0, 1))
                    metrics["choices_made"] += 1
                except Exception:
                    state.pending_choice = None
                continue
            break

        metrics["turns"] += 1

        # Track AI enhancement
        if getattr(response, "ai_enhanced", False):
            metrics["ai_enhanced_turns"] += 1

        # Track choices
        if state.pending_choice is not None:
            metrics["choices_offered"] += 1
            try:
                director.make_choice(game_id, random.randint(0, 1))
                metrics["choices_made"] += 1
            except Exception:
                state.pending_choice = None

        # Track peril
        if state.peril_index > metrics["peril_max"]:
            metrics["peril_max"] = state.peril_index
        if state.peril_index > 30:
            metrics["peril_above30_turns"] += 1

        # Sample interesting events (first 5 with expanded_text)
        if len(metrics["sample_events"]) < 5:
            for ev in (response.events or []):
                text = ev.get("text", "")
                if len(text) > 40 and len(metrics["sample_events"]) < 5:
                    metrics["sample_events"].append({
                        "age": state.age,
                        "text": text[:120],
                        "type": ev.get("type", ""),
                    })

        # Progress
        if turn % 20 == 0:
            rn = REALM_NAMES.get(Realm(state.realm), "凡人")
            print(f"  [Game {game_idx+1}] Turn {turn}: age={state.age}, realm={rn}")

    # Final metrics
    metrics["final_realm"] = state.realm
    metrics["final_age"] = state.age
    metrics["death_reason"] = state.death_reason or ("飞升" if state.is_ascended else "存活")
    metrics["causal_chains_created"] = len(state.causal_chains or [])
    metrics["causal_chains_resolved"] = sum(
        1 for c in (state.causal_chains or []) if c.get("is_resolved")
    )
    metrics["sagas_formed"] = len(state.sagas or [])
    metrics["arcs_completed"] = len(state.completed_arcs_history or [])
    metrics["npc_pivots"] = sum(
        len(npc.get("pivot_history", []))
        for npc in state.npc_registry.values()
    )

    # Cleanup
    GAME_STATE_STORE._store.pop(game_id, None)
    return metrics


def main():
    print(f"═══ 有LLM叙事质量评估 ({NUM_GAMES}局, 最多{MAX_TURNS}回合/局) ═══\n")

    all_metrics = []
    for i in range(NUM_GAMES):
        print(f"\n── Game {i+1}/{NUM_GAMES} ──")
        t0 = time.time()
        m = run_game(i)
        elapsed = time.time() - t0
        all_metrics.append(m)

        rn = REALM_NAMES.get(Realm(m["final_realm"]), "?")
        print(f"  完成: {m['turns']}回合 | 年龄{m['final_age']} | {rn} | {m['death_reason']}")
        print(f"  耗时: {elapsed:.1f}s | AI增强: {m['ai_enhanced_turns']}/{m['turns']}回合")
        print(f"  选择: {m['choices_offered']}次 | 因果链: {m['causal_chains_created']}创建/{m['causal_chains_resolved']}解决")
        print(f"  Saga: {m['sagas_formed']} | 弧线完成: {m['arcs_completed']} | NPC转折: {m['npc_pivots']}")
        print(f"  Peril最高: {m['peril_max']:.0f} | >30回合占比: {m['peril_above30_turns']}/{m['turns']}")

    # Aggregate
    print("\n" + "═" * 50)
    print("        聚合结果 (有LLM)")
    print("═" * 50)

    n = len(all_metrics)
    avg = lambda key: sum(m[key] for m in all_metrics) / n

    print(f"  平均回合数: {avg('turns'):.0f}")
    print(f"  AI增强率: {avg('ai_enhanced_turns')/avg('turns')*100:.0f}%")
    print(f"  选择频率: {avg('choices_offered')/avg('turns')*100:.1f}% (每回合)")
    print(f"  因果链创建: {avg('causal_chains_created'):.1f}")
    print(f"  因果链解决: {avg('causal_chains_resolved'):.1f}")
    print(f"  Saga形成: {avg('sagas_formed'):.1f}")
    print(f"  弧线完成: {avg('arcs_completed'):.1f}")
    print(f"  NPC命运转折: {avg('npc_pivots'):.1f}")
    print(f"  Peril>30占比: {avg('peril_above30_turns')/avg('turns')*100:.0f}%")

    # Sample events from first game
    print(f"\n── 叙事样本(Game1前5条) ──")
    for ev in all_metrics[0].get("sample_events", []):
        print(f"  [{ev['age']}岁][{ev['type']}] {ev['text']}")


if __name__ == "__main__":
    main()
