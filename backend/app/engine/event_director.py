"""Event Director — unified LLM call for event selection + narration + branching.

Replaces the old multi-call approach (separate event selection, narrative expansion,
and choice generation) with a single LLM call that:
1. Chooses the best event from top-10 candidates
2. Generates immersive narrative (200-300 chars)
3. Optionally generates choice branches (if event is dramatic enough)

Falls back to weighted random pick + raw text when LLM is unavailable.
"""
from __future__ import annotations

import json
import logging
import random
from typing import Optional, Generator, TYPE_CHECKING

if TYPE_CHECKING:
    from .ai.llm_client import LLMClient
    from .npc.npc_manager import NPCManager
    from .causality import CausalityManager
    from .story_arc import StoryArcPlanner
    from .main_storyline import MainStorylinePlanner
    from .saga import SagaManager
    from .world_era import WorldEraManager
    from .memory.memory_manager import MemoryManager
    from ..models import GameState

from .ai.prompt_templates import EVENT_DIRECTOR_SYSTEM, EVENT_DIRECTOR_USER, EVENT_DIRECTOR_STREAM_SYSTEM
from .ai.llm_client import MODEL_PRO
from .foreshadowing import build_foreshadowing_context, build_emotional_tokens_context, build_repertoire_context
from .repertoire_pool import sample_acquisition_items
from .life_phase import LifePhase, LifePhaseManager

logger = logging.getLogger(__name__)

# ── Pro model upgrade thresholds ─────────────────────────────────────────
_PRO_TENSION_THRESHOLD = 70
_PRO_SAGA_MOMENTUM_THRESHOLD = 60
_PROMPT_CHAR_LIMIT = 7000  # ~3500 tokens, generous upper bound

# ── Cost optimization: skip LLM for low-value turns ──────────────────────
_LOW_VALUE_TENSION_THRESHOLD = 40  # 张力低于此值视为低价值
_LOW_VALUE_MAX_CONSECUTIVE = 1     # 最多连续跳过1次, 第2次强制走LLM


class EventDirector:
    """Unified LLM call: choose event + narrate + optional branches.

    This is the central narrative intelligence of the game. Given a set of
    candidate events pre-filtered by the rule system, it uses a single LLM
    call to select the most narratively appropriate event, generate rich
    prose, and optionally create meaningful player choices.
    """

    def __init__(
        self,
        llm_client: "LLMClient",
        npc_manager: "NPCManager",
        hook_manager: "CausalityManager",
        arc_planner: "StoryArcPlanner",
        storyline_planner: "MainStorylinePlanner",
        saga_manager: "SagaManager" = None,
        era_manager: "WorldEraManager" = None,
        memory_manager: "MemoryManager" = None,
    ):
        self._llm = llm_client
        self._npc_manager = npc_manager
        self._hook_manager = hook_manager
        self._arc_planner = arc_planner
        self._storyline_planner = storyline_planner
        self._saga_manager = saga_manager
        self._era_manager = era_manager
        self._memory_manager = memory_manager

    # ── Model routing ─────────────────────────────────────────────────────

    def _should_use_pro(self, state: "GameState") -> bool:
        """Decide whether this turn warrants the Pro model.

        Conditions (any one triggers upgrade):
        - tension >= 70
        - active saga with momentum >= 60
        - just broke through (realm_just_advanced flag)
        - world era just changed (era_just_changed flag)
        """
        if state.tension >= _PRO_TENSION_THRESHOLD:
            return True
        # Check active sagas momentum
        for saga in getattr(state, "sagas", None) or []:
            if saga.get("status") == "active" and saga.get("momentum", 0) >= _PRO_SAGA_MOMENTUM_THRESHOLD:
                return True
        # Breakthrough / era change (flags set by director._post_year_update)
        if getattr(state, "_realm_just_advanced", False):
            return True
        if getattr(state, "_era_just_changed", False):
            return True
        return False

    # ── Core methods ──────────────────────────────────────────────────────

    def direct_event(self, candidates: list[dict], state: "GameState") -> dict:
        """Single LLM call to choose event, generate narrative, and optionally branch.

        Args:
            candidates: List of candidate dicts from EventSystem.select_candidates()
                        Each has: {"event": dict, "weight": float, "summary": str, "index": int}
            state: Current game state

        Returns:
            {
                "chosen_index": int,      # Index into candidates list
                "narrative": str,         # 200-300 char narrative text
                "has_choice": bool,       # Whether branches are generated
                "branches": list | None,  # Choice branches if has_choice
            }
        """
        if not candidates:
            return self._empty_result()

        # ── Adult 保护: 有详细 expanded_text 的 adult 事件跳过 LLM 改写 ──
        top_candidate = max(candidates, key=lambda c: c["weight"])
        top_ev = top_candidate["event"]
        if self._is_adult_protected(top_ev):
            idx = candidates.index(top_candidate)
            return {
                "chosen_index": idx,
                "narrative": top_ev.get("expanded_text", ""),
                "has_choice": False,
                "branches": None,
                "ai_used": False,
            }

        # ── 低价值回合跳过 LLM (省成本, 连续≤2次) ──────────────────
        if self._should_skip_llm(top_ev, state):
            # 从top-3候选中随机选一个（引入变异，避免总选top-1）
            pool = candidates[:min(3, len(candidates))]
            chosen_candidate = random.choice(pool)
            idx = candidates.index(chosen_candidate)
            chosen_ev = chosen_candidate["event"]
            state._llm_skip_streak = getattr(state, "_llm_skip_streak", 0) + 1
            return {
                "chosen_index": idx,
                "narrative": chosen_ev.get("expanded_text", "") or chosen_ev.get("text", ""),
                "has_choice": False,
                "branches": None,
                "ai_used": False,
            }
        # 走LLM时重置连续跳过计数
        state._llm_skip_streak = 0

        # Try LLM generation
        if self._llm and self._llm.available:
            result = self._generate_via_llm(candidates, state)
            if result:
                result["ai_used"] = True
                return result

        # Fallback: weighted random + raw text
        fallback = self._fallback(candidates, state)
        fallback["ai_used"] = False
        return fallback

    def _should_skip_llm(self, ev: dict, state: "GameState") -> bool:
        """Determine if this turn can skip LLM to save cost.

        Conditions (ALL must be met):
        0. 已觉醒 (凡人阶段每个事件都很重要，不跳过)
        1. 张力 < 40 (低张力回合)
        2. 事件无 npc_roles (非NPC专属事件)
        3. 事件类型为 normal/funny (非 important/danger/fortune)
        4. expanded_text > 80 chars (已有高质量预写文本)
        5. 连续跳过次数 < 1 (防止重复感)
        6. 无紧迫因果链 (urgency >= 3)
        7. 无高动量Saga (momentum >= 40)
        """
        # 条件0: 凡人阶段不跳过（童年事件皆为叙事根基）
        if getattr(state, "realm", 0) < 1:
            return False

        # 条件5: 连续跳过不超过1次
        streak = getattr(state, "_llm_skip_streak", 0)
        if streak >= _LOW_VALUE_MAX_CONSECUTIVE:
            return False

        # 条件1: 低张力
        if getattr(state, "tension", 50) >= _LOW_VALUE_TENSION_THRESHOLD:
            return False

        # 条件2: 无NPC关联
        if ev.get("npc_roles"):
            return False

        # 条件3: 非高价值事件类型
        if ev.get("event_type", "normal") in ("important", "danger", "fortune"):
            return False

        # 条件4: 已有足够好的预写文本
        expanded = ev.get("expanded_text", "")
        if len(expanded) <= 80:
            return False

        # 条件6: 如果有紧迫因果链则不跳过
        for chain in (getattr(state, "causal_chains", None) or []):
            if not chain.get("is_resolved") and chain.get("urgency", 1) >= 3.0:
                return False

        # 条件7: 如果有活跃Saga高动量则不跳过
        for saga in (getattr(state, "sagas", None) or []):
            if saga.get("is_active") and saga.get("momentum", 0) >= 40:
                return False

        return True

    @staticmethod
    def _is_adult_protected(ev: dict) -> bool:
        """Check if an adult event should skip LLM rewriting.

        Protection condition: has 'adult' tag AND expanded_text > 50 chars.
        Events with empty expanded_text (new NPC events) will NOT be protected.
        """
        tags = set(ev.get("tags", []))
        if "adult" not in tags:
            return False
        expanded = ev.get("expanded_text", "")
        return len(expanded) > 50

    def _generate_via_llm(self, candidates: list[dict], state: "GameState") -> Optional[dict]:
        """Generate unified response via LLM."""
        try:
            system_prompt, user_prompt = self._build_director_prompt(candidates, state)
            use_model = MODEL_PRO if self._should_use_pro(state) else None
            raw = self._llm.generate_sync(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=800,
                temperature=0.80,
                model=use_model,
            )
            if not raw:
                return None

            return self._parse_response(raw, candidates, state)
        except Exception as e:
            logger.warning("EventDirector LLM call failed: %s", e)
            return None

    def _build_director_prompt(
        self, candidates: list[dict], state: "GameState"
    ) -> tuple[str, str]:
        """Build system + user prompt pair for the unified director call."""
        from ..models import REALM_NAMES, Realm

        realm_name = REALM_NAMES.get(Realm(state.realm), "未知")
        gender = "男" if state.gender == "male" else "女"

        # Narrative tone from life phase
        try:
            phase = LifePhase(state.life_phase)
            tone = LifePhaseManager.get_narrative_tone(phase)
        except (ValueError, KeyError):
            tone = "平淡叙事"

        # Build candidates text
        candidates_lines = []
        for i, cand in enumerate(candidates):
            ev = cand["event"]
            ev_type = ev.get("event_type", "normal")
            tags = ", ".join(ev.get("tags", [])[:3]) if ev.get("tags") else ""
            resolves = ev.get("resolves_hook", "")
            priority_hint = cand.get("priority_hint", "")

            # 带★标记的特殊事件排在前面，让LLM立即注意到
            prefix = f"{i + 1}."
            if priority_hint:
                prefix = f"{i + 1}. {priority_hint}"

            line = f"{prefix} {ev.get('text', '')[:80]} [{ev_type}]"
            if tags:
                line += f" 标签:{tags}"
            if resolves:
                line += f" (可解决因果:{resolves})"

            # Show effects briefly
            effects = ev.get("effects", {})
            if effects:
                parts = []
                for k, v in effects.items():
                    if k in ("cultivation", "constitution", "comprehension",
                             "fortune", "charisma", "willpower") and v:
                        sign = "+" if v > 0 else ""
                        parts.append(f"{k}{sign}{v}")
                if parts:
                    line += f" 效果:{','.join(parts[:4])}"

            candidates_lines.append(line)

        candidates_text = "\n".join(candidates_lines)

        # Sect info
        sect_info = "散修"
        if state.sect_membership:
            mem = state.sect_membership
            sects = state.sect_world.get("sects", {})
            sect = sects.get(mem.get("sect_id", ""), {})
            if sect:
                sect_info = f"{sect.get('name', '未知')}·{mem.get('rank', '弟子')}"

        # NPC relationships
        npc_str = "暂无重要人际关系"
        if self._npc_manager:
            npc_str = self._npc_manager.get_npc_context_string(state) or npc_str

        # Dead NPC list — prevent narrative contradictions
        dead_npc_names = []
        for npc_dict in state.npc_registry.values():
            if not npc_dict.get("is_alive", True):
                dead_npc_names.append(npc_dict.get("name", ""))
        dead_npc_warning = ""
        if dead_npc_names:
            dead_npc_warning = f"\n【已死亡NPC】{'、'.join(dead_npc_names)}（请勿在叙事中让他们再次出现、对话或行动）"

        # NPC interaction history (for all NPCs involved in candidates, up to 3)
        npc_history = ""
        if self._npc_manager:
            npc_histories = []
            seen_npc_ids = set()
            for cand in candidates:
                npc_id = cand["event"].get("involved_npc_id", "")
                if npc_id and npc_id not in seen_npc_ids:
                    seen_npc_ids.add(npc_id)
                    history = self._npc_manager.get_npc_interaction_history(
                        state, npc_id, max_entries=5
                    )
                    # Append destiny beat summary for narrative continuity
                    destiny_summary = self._get_npc_destiny_summary(state, npc_id)
                    if destiny_summary:
                        history = (history + "\n" + destiny_summary) if history else destiny_summary
                    if history:
                        npc_histories.append(history)
                    if len(npc_histories) >= 4:
                        break
            npc_history = "\n".join(npc_histories) if npc_histories else ""

        # Unresolved hooks + causal chains context
        hooks_str = "无"
        if self._hook_manager:
            h = self._hook_manager.get_hooks_context_for_ai(state)
            if h:
                hooks_str = h
            # Add causal chains context
            chains_ctx = self._hook_manager.get_chains_context_for_ai(state)
        else:
            chains_ctx = ""

        # Saga context
        saga_context = ""
        if self._saga_manager:
            saga_context = self._saga_manager.get_saga_context_for_ai(state) or ""

        # World era context
        era_context = ""
        if self._era_manager:
            era_context = self._era_manager.get_era_context_for_ai(state) or ""

        # Arc + storyline context
        arc_context = ""
        if self._arc_planner:
            arc_context = self._arc_planner.get_arcs_context_for_ai(state) or ""
        if self._storyline_planner:
            try:
                storyline_ctx = self._storyline_planner.get_storyline_context_for_ai(state)
                if storyline_ctx:
                    arc_context = (arc_context + "\n" + storyline_ctx).strip() if arc_context else storyline_ctx
            except Exception:
                pass

        # Biography
        bio = state.biography_summary or "尚无传记"

        # Recent experiences (realm-adaptive)
        recent = ""
        if self._memory_manager:
            recent = self._memory_manager.get_recent_context(state)
        if not recent and state.memory_working:
            # Fallback: simple last 5 if memory_manager unavailable
            recent_items = state.memory_working[-5:]
            recent = "\n".join(f"- {m.get('text', '')[:50]}" for m in recent_items)

        # Relevant memories (BM25+Embedding retrieval based on candidates)
        relevant_memories = ""
        if self._memory_manager:
            # Extract candidate event texts for query
            cand_texts = [
                c["event"].get("text", "") for c in candidates[:5]
                if c["event"].get("text")
            ]
            relevant_memories = self._memory_manager.retrieve_for_event(
                state, cand_texts, top_k=3
            )

        # Foreshadowing hints (predictive narrative cues)
        foreshadowing = build_foreshadowing_context(state)

        # Emotional tokens context (随身之物)
        emotional_tokens_ctx = build_emotional_tokens_context(state)

        # Repertoire context (修行积累)
        repertoire_ctx = build_repertoire_context(state)

        # Acquisition pool (当前可获得的修行资源)
        acquisition_items = sample_acquisition_items(state, count=3)
        if acquisition_items:
            pool_lines = []
            for item in acquisition_items:
                _cat_map = {"technique": "功法", "treasure": "法宝", "secret_art": "秘术", "puppet": "傀儡", "spirit_beast": "灵兽", "element": "天地精华"}
                cat = _cat_map.get(item.get("category", ""), "法宝")
                pool_lines.append(f"- [{cat}] {item['name']}：{item['desc']}")
            acquisition_pool = "\n".join(pool_lines)
        else:
            acquisition_pool = "无可用资源"

        attrs = state.attributes
        system_prompt = EVENT_DIRECTOR_SYSTEM.format(
            realm_name=realm_name,
            gender=gender,
        )
        user_prompt = EVENT_DIRECTOR_USER.format(
            candidates_text=candidates_text,
            realm_name=realm_name,
            age=state.age,
            gender=gender,
            constitution=attrs.constitution,
            comprehension=attrs.comprehension,
            fortune=attrs.fortune,
            charisma=attrs.charisma,
            willpower=attrs.willpower,
            sect_info=sect_info,
            tension=int(state.tension),
            narrative_tone=tone,
            npc_relationships=npc_str,
            npc_history=npc_history or "无相关交往史",
            unresolved_hooks=hooks_str,
            arc_context=arc_context or "无活跃剧情线",
            biography=bio,
            recent_events=recent or "暂无近期经历",
            relevant_memories=relevant_memories or "无相关往事可追溯",
            world_era_context=era_context or "天下太平，无特殊大势",
            saga_context=saga_context or "无活跃长线Saga",
            causal_chains_context=chains_ctx or "无活跃因果链",
            foreshadowing_hints=foreshadowing or "无伏笔暗线",
            emotional_tokens_context=emotional_tokens_ctx or "无随身之物",
            repertoire_context=repertoire_ctx or "无修行积累",
            acquisition_pool=acquisition_pool,
        )

        # Append dead NPC warning after user prompt to prevent contradictions
        if dead_npc_warning:
            user_prompt += dead_npc_warning

        user_prompt = self._trim_prompt_if_needed(user_prompt)

        return system_prompt, user_prompt

    def _trim_prompt_if_needed(self, user_prompt: str) -> str:
        """Trim user prompt if it exceeds the character limit.

        Truncation priority (lowest priority trimmed first):
        1. saga_context -> 100 chars
        2. npc_history -> 300 chars
        3. recent_events -> 200 chars
        4. arc_context -> 200 chars
        """
        if len(user_prompt) <= _PROMPT_CHAR_LIMIT:
            return user_prompt

        import re

        # Section markers and their trim limits (ordered by trim priority)
        trim_rules = [
            ("【活跃 Saga】", 100),
            ("【与涉事NPC的交往史】", 500),
            ("【近期经历】", 200),
            ("【剧情线/命运线】", 200),
        ]

        result = user_prompt
        for marker, limit in trim_rules:
            if len(result) <= _PROMPT_CHAR_LIMIT:
                break
            # Find section and truncate its content
            idx = result.find(marker)
            if idx < 0:
                continue
            # Find the next section marker
            next_section = len(result)
            for other_marker, _ in trim_rules:
                if other_marker == marker:
                    continue
                other_idx = result.find(other_marker, idx + len(marker))
                if other_idx > 0:
                    next_section = min(next_section, other_idx)
            # Also check other known markers
            for known in ["【候选事件】", "【主角状态】", "【天地大势】",
                          "【因果暗线】", "【人际关系】", "【未了之事】",
                          "【伏笔暗线", "【传记摘要】", "请选择"]:
                ki = result.find(known, idx + len(marker))
                if ki > 0:
                    next_section = min(next_section, ki)
            # Trim section content
            content_start = idx + len(marker)
            section_content = result[content_start:next_section]
            if len(section_content) > limit:
                trimmed = section_content[:limit] + "...(已截断)"
                result = result[:content_start] + trimmed + result[next_section:]

        if len(result) < len(user_prompt):
            logger.debug(
                "Prompt trimmed: %d -> %d chars",
                len(user_prompt), len(result)
            )
        return result

    @staticmethod
    def _get_npc_destiny_summary(state, npc_id: str) -> str:
        """Build a summary of completed destiny beats for an NPC.

        Provides narrative continuity context so LLM can reference
        previous destiny milestones in its expansion.
        """
        npc_dict = state.npc_registry.get(npc_id)
        if not npc_dict:
            return ""

        destiny_beats = npc_dict.get("destiny_beats", [])
        idx = npc_dict.get("current_destiny_index", 0)
        if idx == 0:
            return ""

        name = npc_dict.get("name", "某人")
        completed = destiny_beats[:idx]
        lines = [f"与{name}的命运节点:"]
        for i, beat in enumerate(completed):
            desc = beat.get("description", "")
            lines.append(f"  {i+1}. {desc}（已发生）")

        # Show next pending beat hint (without spoiling details)
        if idx < len(destiny_beats):
            next_type = destiny_beats[idx].get("event_type", "")
            lines.append(f"  [下一节点: {next_type}类型，尚未触发]")

        return "\n".join(lines)

    def _parse_response(self, raw: str, candidates: list[dict], state: "GameState") -> Optional[dict]:
        """Parse LLM JSON response, validate, and sanitize."""
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (fences)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    data = json.loads(text[start:end])
                except json.JSONDecodeError:
                    logger.warning("EventDirector: failed to parse JSON response")
                    return None
            else:
                return None

        # Validate chosen index
        chosen = data.get("chosen", 1)
        # LLM outputs 1-based index, convert to 0-based
        if isinstance(chosen, int):
            chosen_index = chosen - 1
        else:
            chosen_index = 0

        if chosen_index < 0 or chosen_index >= len(candidates):
            chosen_index = 0

        # Extract narrative
        narrative = data.get("narrative", "")
        if not narrative or len(narrative) < 20:
            # Use raw event text as fallback
            narrative = candidates[chosen_index]["event"].get("text", "")

        # Extract choice branches
        has_choice = bool(data.get("has_choice", False))
        branches = None
        if has_choice:
            raw_branches = data.get("branches", [])
            if raw_branches and isinstance(raw_branches, list):
                branches = self._sanitize_branches(raw_branches)
                if not branches:
                    has_choice = False

        return {
            "chosen_index": chosen_index,
            "narrative": narrative,
            "has_choice": has_choice,
            "branches": branches,
            "combat_loot": self._sanitize_combat_loot(data.get("combat_loot")),
            "causal_chain": self._sanitize_causal_chain(data.get("causal_chain")),
            "emotional_token": self._sanitize_emotional_token(data.get("emotional_token")),
        }

    def _sanitize_branches(self, branches: list) -> Optional[list[dict]]:
        """Validate and sanitize choice branches from LLM output."""
        if not branches or len(branches) < 2:
            return None

        valid_attrs = ("constitution", "comprehension", "fortune", "charisma", "willpower")

        sanitized = []
        for b in branches[:3]:  # Max 3 branches
            if not isinstance(b, dict):
                continue
            text = b.get("text", "")
            if not text:
                continue

            # Sanitize effects
            effects = self._sanitize_effects(b.get("effects", {}))
            # Sanitize failure_effects
            failure_effects = self._sanitize_effects(b.get("failure_effects", {}))

            # Sanitize success_rate
            try:
                success_rate = max(10, min(95, int(b.get("success_rate", 60))))
            except (ValueError, TypeError):
                success_rate = 60

            # Sanitize check_attribute
            check_attr = str(b.get("check_attribute", ""))
            if check_attr not in valid_attrs:
                check_attr = ""

            branch = {
                "text": text[:20],
                "success_rate": success_rate,
                "check_attribute": check_attr,
                "effects": effects,
                "result_text": b.get("result_text", "")[:150],
                "failure_effects": failure_effects,
                "failure_text": b.get("failure_text", "")[:150],
                "consequence_tag": b.get("consequence_tag", "") or "",
                "consequence_desc": b.get("consequence_desc", "") or "",
            }
            # Preserve combat_risk flag for fortune+combat integration
            if b.get("combat_risk"):
                branch["combat_risk"] = True
            # Preserve acquisition field for repertoire system
            acq = b.get("acquisition")
            if acq and isinstance(acq, dict) and acq.get("name"):
                branch["acquisition"] = {
                    "name": str(acq["name"])[:15],
                    "category": acq.get("category", "treasure") if acq.get("category") in ("technique", "treasure", "secret_art", "puppet", "spirit_beast", "element") else "treasure",
                    "desc": str(acq.get("desc", ""))[:30],
                    "power": min(5, max(1, int(acq.get("power", 1)))) if isinstance(acq.get("power"), (int, float)) else 1,
                }
            sanitized.append(branch)

        return sanitized if len(sanitized) >= 2 else None

    @staticmethod
    def _sanitize_effects(effects) -> dict:
        """Sanitize and clamp effect values."""
        if not isinstance(effects, dict):
            return {}
        clean_effects = {}
        for k, v in effects.items():
            if k == "cultivation" and isinstance(v, (int, float)):
                clean_effects[k] = max(-30, min(50, int(v)))
            elif k in ("constitution", "comprehension", "fortune",
                       "charisma", "willpower") and isinstance(v, (int, float)):
                clean_effects[k] = max(-3, min(3, int(v)))
            elif k == "add_tag" and isinstance(v, str):
                clean_effects[k] = v[:20]
        return clean_effects

    @staticmethod
    def _sanitize_emotional_token(raw) -> Optional[dict]:
        """Validate emotional_token from LLM output."""
        if not isinstance(raw, dict):
            return None
        name = raw.get("name", "")
        if not name:
            return None
        return {
            "name": name[:6],
            "description": raw.get("description", "")[:30],
            "source_npc": raw.get("source_npc", "")[:10],
            "keywords": [str(k)[:8] for k in raw.get("keywords", []) if isinstance(k, str)][:3],
        }

    @staticmethod
    def _sanitize_combat_loot(raw) -> Optional[dict]:
        """Validate combat_loot from LLM output (战后缴获)."""
        if not isinstance(raw, dict):
            return None
        name = raw.get("name", "")
        if not name:
            return None
        category = raw.get("category", "treasure")
        valid_categories = ("technique", "treasure", "secret_art", "puppet", "spirit_beast", "element")
        if category not in valid_categories:
            category = "treasure"
        try:
            power = min(5, max(1, int(raw.get("power", 2))))
        except (ValueError, TypeError):
            power = 2
        return {
            "name": name[:15],
            "category": category,
            "desc": str(raw.get("desc", ""))[:30],
            "power": power,
        }

    @staticmethod
    def _sanitize_causal_chain(raw) -> Optional[dict]:
        """Validate and sanitize LLM-generated causal chain data.

        Expected schema: {cause: str, expected_resolution: str, keywords: list[str]}
        Returns None if invalid.
        """
        if not isinstance(raw, dict):
            return None
        cause = raw.get("cause", "")
        expected = raw.get("expected_resolution", "")
        keywords = raw.get("keywords", [])

        if not expected or not isinstance(expected, str):
            return None
        if not isinstance(cause, str):
            cause = ""
        if not isinstance(keywords, list):
            keywords = []
        # Sanitize keywords: only keep short strings
        keywords = [str(k)[:10] for k in keywords if isinstance(k, str) and len(k) <= 10][:8]

        return {
            "cause": cause[:80],
            "expected_resolution": expected[:60],
            "keywords": keywords,
        }

    def _fallback(self, candidates: list[dict], state: "GameState") -> dict:
        """Fallback when LLM is unavailable: weighted random pick + raw text."""
        # Weighted random selection
        total_weight = sum(c["weight"] for c in candidates)
        if total_weight <= 0:
            chosen_index = 0
        else:
            r = random.uniform(0, total_weight)
            cum = 0.0
            chosen_index = 0
            for i, c in enumerate(candidates):
                cum += c["weight"]
                if r <= cum:
                    chosen_index = i
                    break

        ev = candidates[chosen_index]["event"]
        # Use expanded_text if available, else raw text
        narrative = ev.get("expanded_text", "") or ev.get("text", "")

        return {
            "chosen_index": chosen_index,
            "narrative": narrative,
            "has_choice": False,
            "branches": None,
        }

    @staticmethod
    def _empty_result() -> dict:
        """Return empty result when no candidates available."""
        return {
            "chosen_index": 0,
            "narrative": "平静的一年，无事发生。",
            "has_choice": False,
            "branches": None,
        }

    # ── Streaming variant ─────────────────────────────────────────

    def direct_event_stream(
        self, candidates: list[dict], state: "GameState"
    ) -> Generator[dict, None, None]:
        """Streaming variant of direct_event.

        Yields:
          {"type": "meta", "data": {chosen_index, has_choice, branches, ai_used}}
          {"type": "narrative_chunk", "data": "text chunk"}
          {"type": "done"}
        """
        if not candidates:
            yield {"type": "meta", "data": {**self._empty_result(), "ai_used": False}}
            yield {"type": "narrative_chunk", "data": "平静的一年，无事发生。"}
            yield {"type": "done"}
            return

        top_candidate = max(candidates, key=lambda c: c["weight"])
        top_ev = top_candidate["event"]

        # ── Adult 保护: 有详细 expanded_text 的 adult 事件跳过 LLM 改写 ──
        if self._is_adult_protected(top_ev):
            idx = candidates.index(top_candidate)
            meta = {"chosen_index": idx, "narrative": top_ev.get("expanded_text", ""),
                    "has_choice": False, "branches": None, "ai_used": False}
            yield {"type": "meta", "data": meta}
            yield {"type": "narrative_chunk", "data": meta["narrative"]}
            yield {"type": "done"}
            return

        # ── 低价值回合跳过 LLM (省成本, 连续≤1次) ──
        if self._should_skip_llm(top_ev, state):
            # 从top-3候选中随机选一个（引入变异）
            pool = candidates[:min(3, len(candidates))]
            chosen_candidate = random.choice(pool)
            idx = candidates.index(chosen_candidate)
            chosen_ev = chosen_candidate["event"]
            state._llm_skip_streak = getattr(state, "_llm_skip_streak", 0) + 1
            narrative = chosen_ev.get("expanded_text", "") or chosen_ev.get("text", "")
            meta = {"chosen_index": idx, "narrative": narrative,
                    "has_choice": False, "branches": None, "ai_used": False}
            yield {"type": "meta", "data": meta}
            yield {"type": "narrative_chunk", "data": narrative}
            yield {"type": "done"}
            return
        # 走LLM时重置连续跳过计数
        state._llm_skip_streak = 0

        if not (self._llm and self._llm.available):
            fb = self._fallback(candidates, state)
            fb["ai_used"] = False
            yield {"type": "meta", "data": fb}
            yield {"type": "narrative_chunk", "data": fb["narrative"]}
            yield {"type": "done"}
            return

        # Build streaming prompt
        system_prompt, user_prompt = self._build_director_prompt_stream(candidates, state)

        buffer = ""
        meta_parsed = False
        had_output = False
        use_model = MODEL_PRO if self._should_use_pro(state) else None

        try:
            for chunk in self._llm.generate_stream(
                system_prompt, user_prompt, max_tokens=800, temperature=0.80,
                model=use_model,
            ):
                had_output = True
                buffer += chunk

                if not meta_parsed:
                    # Look for === delimiter
                    if "===" in buffer:
                        parts = buffer.split("===", 1)
                        meta_json = parts[0].strip()
                        meta_data = self._parse_stream_meta(meta_json, candidates)
                        meta_data["ai_used"] = True
                        yield {"type": "meta", "data": meta_data}
                        meta_parsed = True
                        # Remaining text after delimiter is narrative start
                        remaining = parts[1].lstrip("\n")
                        if remaining:
                            yield {"type": "narrative_chunk", "data": remaining}
                        buffer = ""
                else:
                    # Stream narrative chunks directly
                    yield {"type": "narrative_chunk", "data": chunk}
        except Exception as e:
            logger.warning("EventDirector stream failed: %s", e)
            # Reset skip streak so next turn will attempt LLM again
            state._llm_skip_streak = 0

        # Handle case where delimiter never arrived or LLM had no output
        if not meta_parsed:
            if had_output:
                # Try to parse as original JSON format (LLM ignored stream format)
                result = self._parse_response(buffer, candidates, state)
                if result:
                    result["ai_used"] = True
                    yield {"type": "meta", "data": result}
                    yield {"type": "narrative_chunk", "data": result["narrative"]}
                else:
                    fb = self._fallback(candidates, state)
                    fb["ai_used"] = False
                    yield {"type": "meta", "data": fb}
                    yield {"type": "narrative_chunk", "data": fb["narrative"]}
            else:
                # No output at all - pure fallback
                fb = self._fallback(candidates, state)
                fb["ai_used"] = False
                yield {"type": "meta", "data": fb}
                yield {"type": "narrative_chunk", "data": fb["narrative"]}

        yield {"type": "done"}

    def _build_director_prompt_stream(
        self, candidates: list[dict], state: "GameState"
    ) -> tuple[str, str]:
        """Build streaming-variant prompt (same user prompt, different system prompt)."""
        from ..models import REALM_NAMES, Realm

        realm_name = REALM_NAMES.get(Realm(state.realm), "未知")
        gender = "男" if state.gender == "male" else "女"

        system_prompt = EVENT_DIRECTOR_STREAM_SYSTEM.format(
            realm_name=realm_name,
            gender=gender,
        )
        # Reuse the same user prompt builder
        _, user_prompt = self._build_director_prompt(candidates, state)
        return system_prompt, user_prompt

    def _parse_stream_meta(self, meta_json: str, candidates: list[dict]) -> dict:
        """Parse the metadata JSON from streaming output."""
        try:
            # Strip markdown fences if present
            text = meta_json.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines)

            data = json.loads(text)

            # Validate chosen index (1-based to 0-based)
            chosen = data.get("chosen", 1)
            chosen_index = (chosen - 1) if isinstance(chosen, int) else 0
            if chosen_index < 0 or chosen_index >= len(candidates):
                chosen_index = 0

            # Extract branches
            has_choice = bool(data.get("has_choice", False))
            branches = None
            if has_choice:
                raw_branches = data.get("branches", [])
                if raw_branches and isinstance(raw_branches, list):
                    branches = self._sanitize_branches(raw_branches)
                    if not branches:
                        has_choice = False

            return {
                "chosen_index": chosen_index,
                "narrative": "",  # Will be streamed separately
                "has_choice": has_choice,
                "branches": branches,
            }
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning("Failed to parse stream meta JSON: %s", e)
            # Fallback: pick first candidate
            return {
                "chosen_index": 0,
                "narrative": "",
                "has_choice": False,
                "branches": None,
            }
