"""
分段推演脚本 — 单步 dump-then-inject 模式。

用法:
  python simulate_game.py start          # 开始新游戏
  python simulate_game.py step           # 推进1回合, dump turn_data 到 JSON
  python simulate_game.py inject         # 读取 my_response.json, 注入回state
  python simulate_game.py status         # 当前状态快照
  python simulate_game.py run [N=15]     # 连续跑 N 回合(fallback模式, 快速测试)
"""
import sys
import os
import json
import random
import types

# 如果命令行带 --llm 参数则启用 LLM，否则禁用
_USE_LLM = "--llm" in sys.argv
if not _USE_LLM:
    os.environ["DEEPSEEK_API_KEY"] = ""
else:
    sys.argv.remove("--llm")

sys.path.insert(0, os.path.dirname(__file__))

from app.engine import GameDirector
from app.engine.state import get_state, GAME_STATE_STORE
from app.models import Realm, REALM_NAMES

# ── Paths ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
STATE_FILE = os.path.join(BASE_DIR, ".sim_game_id")
SIM_DATA_DIR = os.path.join(BASE_DIR, "simulation_data")
TURN_COUNTER_FILE = os.path.join(SIM_DATA_DIR, ".turn_counter")

os.makedirs(SIM_DATA_DIR, exist_ok=True)

director = GameDirector()


# ── Helper functions ──────────────────────────────────────────────────

def realm_name(r: int) -> str:
    return REALM_NAMES.get(Realm(r), "凡人") if r in [e.value for e in Realm] else f"未知({r})"


def get_turn_counter() -> int:
    if os.path.exists(TURN_COUNTER_FILE):
        return int(open(TURN_COUNTER_FILE).read().strip())
    return 0


def set_turn_counter(n: int):
    with open(TURN_COUNTER_FILE, "w") as f:
        f.write(str(n))


def get_game_id() -> str:
    if not os.path.exists(STATE_FILE):
        print("错误: 没有进行中的游戏，请先 start")
        sys.exit(1)
    return open(STATE_FILE).read().strip()


def snapshot_state(state) -> dict:
    """Create a readable state snapshot."""
    sect_info = None
    if state.sect_membership:
        mem = state.sect_membership
        sects = state.sect_world.get("sects", {})
        sect = sects.get(mem.get("sect_id", ""), {})
        if sect:
            sect_info = {
                "name": sect.get("name", ""),
                "rank": mem.get("rank", ""),
                "contribution": mem.get("contribution", 0),
                "sect_type": sect.get("sect_type", ""),
                "reputation_in_sect": mem.get("reputation_in_sect", 50),
            }

    npcs = []
    for rel in state.relationships:
        npc_id = rel.get("npc_id", "")
        npc = state.npc_registry.get(npc_id, {})
        if npc:
            npcs.append({
                "npc_id": npc_id,
                "name": npc.get("name", "?"),
                "relation_type": rel.get("relation_type", "?"),
                "sentiment": rel.get("sentiment", 0),
                "is_alive": npc.get("is_alive", True),
                "realm": npc.get("realm", 0),
                "personality": npc.get("personality", ""),
            })

    arcs = []
    for arc in (state.active_arcs or []):
        arcs.append({
            "theme": arc.get("theme", ""),
            "phase": arc.get("phase", "setup"),
            "npc_name": arc.get("npc_name", ""),
            "current_beat_index": arc.get("current_beat_index", 0),
            "total_beats": len(arc.get("planned_beats", [])),
            "is_completed": arc.get("is_completed", False),
        })

    return {
        "age": state.age,
        "realm": state.realm,
        "realm_name": realm_name(state.realm),
        "gender": state.gender,
        "life_phase": getattr(state, "life_phase", ""),
        "cultivation": state.cultivation,
        "tension": round(state.tension, 1),
        "attributes": {
            "constitution": state.attributes.constitution,
            "comprehension": state.attributes.comprehension,
            "fortune": state.attributes.fortune,
            "charisma": state.attributes.charisma,
            "willpower": state.attributes.willpower,
        },
        "sect": sect_info,
        "npcs": npcs,
        "npc_count": len(state.npc_registry),
        "npc_alive_count": sum(1 for n in state.npc_registry.values() if n.get("is_alive", True)),
        "active_arcs": arcs,
        "main_storyline": state.main_storyline if state.main_storyline else None,
        "used_event_count": len(state.used_event_ids),
        "events_log_count": len(state.events_log),
        "is_dead": state.is_dead,
        "is_ascended": state.is_ascended,
        "biography_summary": state.biography_summary or "",
        "pending_choice": state.pending_choice.get("id") if state.pending_choice else None,
    }


def format_candidate(cand: dict, idx: int) -> dict:
    """Format a candidate event for JSON output."""
    ev = cand["event"]
    return {
        "index": idx,
        "id": ev.get("id", ""),
        "text": ev.get("text", "")[:150],
        "expanded_text": (ev.get("expanded_text", "") or "")[:200],
        "weight": round(cand["weight"], 2),
        "event_type": ev.get("event_type", "normal"),
        "category": ev.get("category", ""),
        "tags": ev.get("tags", []),
        "effects": ev.get("effects", {}),
        "npc_roles": ev.get("npc_roles", []),
        "resolves_hook": ev.get("resolves_hook", ""),
        "min_realm": ev.get("min_realm", 0),
        "priority_hint": cand.get("priority_hint", ""),
    }


def format_event_brief(ev: dict) -> dict:
    """Format a priority/chain event briefly."""
    return {
        "text": (ev.get("text", ""))[:120],
        "event_type": ev.get("event_type", ""),
        "tags": ev.get("tags", []),
        "effects": ev.get("effects", {}),
        "involved_npc": ev.get("involved_npc", "") or ev.get("involved_npc_name", ""),
    }


# ══════════════════════════════════════════════════════════════════════
#  Monkey-patch: intercept EventDirector.direct_event to dump context
# ══════════════════════════════════════════════════════════════════════

_captured_turn_data = {}  # module-level capture dict


# Save original method for LLM mode
_original_direct_event = None  # will be set after import


def _patched_direct_event(self, candidates, state):
    """Replacement for EventDirector.direct_event that captures context.
    If --llm mode, calls the real LLM; otherwise uses fallback."""
    global _captured_turn_data

    if not candidates:
        result = self._empty_result()
        _captured_turn_data["event_selection"] = {
            "candidates": [],
            "context_prompt": "(无候选事件)",
            "chosen_by_fallback": result,
        }
        return result

    # ── Build the full prompt (same as real LLM path) ──
    try:
        system_prompt, user_prompt = self._build_director_prompt(candidates, state)
    except Exception as e:
        system_prompt = f"(prompt构建失败: {e})"
        user_prompt = ""

    # ── Should we skip LLM? ──
    top_candidate = max(candidates, key=lambda c: c["weight"])
    top_ev = top_candidate["event"]
    skip_reason = None

    if self._is_adult_protected(top_ev):
        skip_reason = "adult保护(已有expanded_text)"
    elif self._should_skip_llm(top_ev, state):
        skip_reason = f"低价值回合跳过(tension={state.tension:.0f})"

    # ── Get result: LLM mode or fallback mode ──
    if _USE_LLM:
        # Call the real direct_event logic (will use LLM)
        result = _original_direct_event(self, candidates, state)
    else:
        result = self._fallback(candidates, state)
        result["ai_used"] = False

    # ── Determine if LLM would be needed ──
    llm_would_be_needed = skip_reason is None
    model_grade = "Pro" if self._should_use_pro(state) else "Flash"

    # ── Capture everything ──
    _captured_turn_data["event_selection"] = {
        "candidates": [format_candidate(c, i) for i, c in enumerate(candidates)],
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "llm_would_be_needed": llm_would_be_needed,
        "llm_skip_reason": skip_reason,
        "model_grade": model_grade,
        "fallback_chosen_index": result.get("chosen_index", 0),
        "fallback_narrative_preview": result.get("narrative", "")[:200],
        "ai_used": result.get("ai_used", False),
    }

    return result


# ══════════════════════════════════════════════════════════════════════
#  Monkey-patch: intercept NarrativeProvider.get_breakthrough_narrative
# ══════════════════════════════════════════════════════════════════════

def _patched_breakthrough_narrative(self, breakthrough, state):
    """Replacement that captures breakthrough context and returns raw text."""
    _captured_turn_data.setdefault("breakthrough", {})
    _captured_turn_data["breakthrough"] = {
        "event_text": breakthrough.get("text", "")[:200],
        "realm": state.realm,
        "note": "突破叙事需要LLM扩写(当前返回原始文本)",
    }
    return breakthrough.get("expanded_text", "") or breakthrough.get("text", "")


# Apply monkey-patches
from app.engine.event_director import EventDirector
from app.engine.narrative import NarrativeProvider

_original_direct_event = EventDirector.direct_event  # save before patching
EventDirector.direct_event = _patched_direct_event
NarrativeProvider.get_breakthrough_narrative = _patched_breakthrough_narrative


# ══════════════════════════════════════════════════════════════════════
#  Commands
# ══════════════════════════════════════════════════════════════════════

def cmd_start(gender: str = None):
    """开始新游戏。可选指定性别: female/male"""
    state = director.start_game()
    # Override gender if specified
    if gender:
        state.gender = gender
    # Persist after full initialization (sect world + era)
    GAME_STATE_STORE.set(state.game_id, state)
    with open(STATE_FILE, "w") as f:
        f.write(state.game_id)
    set_turn_counter(0)

    # Dump initial state
    init_data = {
        "action": "start",
        "game_id": state.game_id,
        "initial_state": snapshot_state(state),
    }
    out_path = os.path.join(SIM_DATA_DIR, "turn_000_init.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(init_data, f, ensure_ascii=False, indent=2)

    print(f"=== 新游戏开始 ===")
    print(f"Game ID: {state.game_id}")
    print(f"年龄: {state.age} | 境界: {realm_name(state.realm)} | 性别: {state.gender}")
    print(f"初始数据已保存: {out_path}")


def cmd_step():
    """执行1回合, dump全量上下文到 JSON。"""
    global _captured_turn_data
    _captured_turn_data = {}

    game_id = get_game_id()
    state = get_state(game_id)
    if state is None:
        print(f"错误: 游戏 {game_id} 不存在")
        return

    if state.is_dead or state.is_ascended:
        print(f"游戏已结束 ({'死亡' if state.is_dead else '飞升'})")
        return

    # Auto-resolve pending choice (pick option 0)
    if state.pending_choice is not None:
        ev_id = state.pending_choice.get("id", "")
        try:
            director.make_choice(game_id, ev_id, 0)
            _captured_turn_data["auto_choice"] = {
                "event_id": ev_id,
                "chosen_option": 0,
            }
        except Exception as e:
            _captured_turn_data["auto_choice_error"] = str(e)
            state.pending_choice = None

    # Snapshot pre-state
    pre_state = snapshot_state(state)

    # Capture priority events by hooking into the event list
    pre_event_count = len(state.events_log)

    # ── Run the turn ──
    try:
        result = director.advance_year(game_id)
    except ValueError as e:
        print(f"错误: {e}")
        return

    # Persist state to disk (since each step is a separate process)
    state = get_state(game_id)
    GAME_STATE_STORE.set(game_id, state)

    post_state = snapshot_state(state)

    # Extract events from result
    events_this_turn = []
    for ev in result.events:
        events_this_turn.append({
            "text": ev.get("text", "")[:200],
            "expanded_text": (ev.get("expanded_text", "") or "")[:300],
            "type": ev.get("type", ""),
            "category": ev.get("category", ""),
            "age": ev.get("age", 0),
        })

    # ── Build turn data ──
    turn_num = get_turn_counter() + 1
    set_turn_counter(turn_num)

    turn_data = {
        "turn": turn_num,
        "pre_state": pre_state,
        "post_state": post_state,
        "events": events_this_turn,
        "event_selection": _captured_turn_data.get("event_selection", {}),
        "breakthrough": _captured_turn_data.get("breakthrough"),
        "auto_choice": _captured_turn_data.get("auto_choice"),
        "result_summary": {
            "age": result.age,
            "realm": result.realm,
            "realm_name": result.realm_name,
            "years_passed": result.years_passed,
            "is_dead": result.is_dead,
            "death_reason": result.death_reason,
            "is_ascended": result.is_ascended,
            "has_choice": result.has_choice,
            "tension": result.tension,
            "ai_enhanced": result.ai_enhanced,
        },
    }

    out_path = os.path.join(SIM_DATA_DIR, f"turn_{turn_num:03d}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(turn_data, f, ensure_ascii=False, indent=2)

    # Print brief summary
    print(f"── 回合{turn_num} | {result.age}岁 | {result.realm_name} | 事件×{len(events_this_turn)} ──")
    for i, ev in enumerate(events_this_turn, 1):
        text = ev["expanded_text"] or ev["text"]
        if len(text) > 80:
            text = text[:77] + "..."
        print(f"  {i}. [{ev['type']}] {text}")

    if result.is_dead:
        print(f"  *** 死亡: {result.death_reason} ***")
    elif result.is_ascended:
        print(f"  *** 飞升 ***")

    cands = _captured_turn_data.get("event_selection", {}).get("candidates", [])
    print(f"  候选事件: {len(cands)} | 详细数据: {out_path}")
    print()


def cmd_inject():
    """读取 my_response.json, 将LLM响应注入回state。"""
    game_id = get_game_id()
    state = get_state(game_id)
    if state is None:
        print(f"错误: 游戏 {game_id} 不存在")
        return

    resp_path = os.path.join(SIM_DATA_DIR, "my_response.json")
    if not os.path.exists(resp_path):
        print(f"错误: 找不到 {resp_path}")
        print("请创建 my_response.json 包含: chosen_index, narrative, has_choice, branches, causal_chain")
        return

    with open(resp_path, encoding="utf-8") as f:
        resp = json.load(f)

    # Update the last event's expanded_text with my narrative
    narrative = resp.get("narrative", "")
    if narrative and state.events_log:
        state.events_log[-1]["expanded_text"] = narrative

    # Handle causal chain injection
    causal_chain = resp.get("causal_chain")
    if causal_chain and isinstance(causal_chain, dict):
        from app.engine.event_director import EventDirector
        sanitized = EventDirector._sanitize_causal_chain(causal_chain)
        if sanitized:
            director.hook_manager.create_causal_chain(state, sanitized, {})
            print(f"  注入因果链: {sanitized.get('expected_resolution', '?')}")

    # Persist state after injection
    GAME_STATE_STORE.set(game_id, state)
    print(f"  叙事注入完成 ({len(narrative)}字)")


def cmd_status():
    """当前状态快照。"""
    game_id = get_game_id()
    state = get_state(game_id)
    if state is None:
        print(f"游戏 {game_id} 不存在")
        return
    snap = snapshot_state(state)
    print(json.dumps(snap, ensure_ascii=False, indent=2))


def cmd_run(n: int = 15):
    """连续跑 N 回合(fallback模式, 快速测试)。"""
    for _ in range(n):
        game_id = get_game_id()
        state = get_state(game_id)
        if state.is_dead or state.is_ascended:
            print(f"游戏已结束 ({'死亡' if state.is_dead else '飞升'})")
            break
        cmd_step()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python simulate_game.py [start|step|inject|status|run] [参数]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "start":
        g = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_start(gender=g)
    elif cmd == "step":
        cmd_step()
    elif cmd == "inject":
        cmd_inject()
    elif cmd == "status":
        cmd_status()
    elif cmd == "run":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        cmd_run(n)
    else:
        print(f"未知命令: {cmd}")
