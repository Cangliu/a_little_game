"""Game Director — yearly advancement pipeline.

Replaces the old monolithic ``advance_year()`` with a clear 10-phase
pipeline that fixes execution-order issues and enables AI integration.
Now includes NPC system, memory management, LLM narrative, plot hooks,
event-NPC binding, and story arc planning.
"""
import random as _rand
from typing import Generator

from ..models import GameState, NextYearResponse, LifeSummary, Realm, REALM_NAMES
from ..endings import get_title, calculate_score
from .config import (
    REALM_THRESHOLDS, TIME_STEP_BY_REALM, TENSION_DECAY_PER_TURN, TENSION_BY_EVENT_TYPE,
    PERIL_DECAY_PER_TURN, PERIL_SECT_PROTECTION, PERIL_LOW_PROFILE_BONUS, PERIL_CONTRIB,
)
from .life_phase import LifePhaseManager
from .event_system import EventSystem, _extract_narrative_age, find_event_by_id
from .realm_system import RealmSystem
from .death_system import DeathSystem
from .narrative import NarrativeProvider
from .context import GameContext
from .state import create_game, get_state
from .ai import LLMClient, PromptBuilder
from .npc import NPCManager
from .memory import MemoryManager
from .causality import CausalityManager
from .world_era import WorldEraManager
from .saga import SagaManager
from .event_npc_resolver import EventNPCResolver
from .story_arc import StoryArcPlanner
from .main_storyline import MainStorylinePlanner
from .sect import SectManager
from .event_director import EventDirector


class GameDirector:
    """Orchestrates the yearly game loop."""

    def __init__(self) -> None:
        self.phase_manager = LifePhaseManager()
        self.event_system = EventSystem()
        self.realm_system = RealmSystem()
        self.death_system = DeathSystem()
        self.context = GameContext()
        # AI & NPC & Memory subsystems
        self.llm_client = LLMClient()
        self.prompt_builder = PromptBuilder()
        self.npc_manager = NPCManager(llm_client=self.llm_client)
        self.memory_manager = MemoryManager(
            llm_client=self.llm_client,
            prompt_builder=self.prompt_builder,
        )
        # Plot hooks (cause-effect chains)
        self.hook_manager = CausalityManager()
        # World era system
        self.era_manager = WorldEraManager()
        # Saga emergence system
        self.saga_manager = SagaManager(llm_client=self.llm_client)
        # Event-NPC resolver (placeholder replacement)
        self.npc_resolver = EventNPCResolver(self.npc_manager)
        # Story arc planner
        self.arc_planner = StoryArcPlanner(
            llm_client=self.llm_client,
            prompt_builder=self.prompt_builder,
            npc_manager=self.npc_manager,
        )
        # Main storyline planner (骨骼系统) — created before narrative for injection
        self.storyline_planner = MainStorylinePlanner(
            llm_client=self.llm_client,
            prompt_builder=self.prompt_builder,
            npc_manager=self.npc_manager,
        )
        # Wire LLM into narrative provider (with full context access)
        self.narrative = NarrativeProvider(
            llm_client=self.llm_client,
            prompt_builder=self.prompt_builder,
            npc_manager=self.npc_manager,
            memory_manager=self.memory_manager,
            hook_manager=self.hook_manager,
            arc_planner=self.arc_planner,
            storyline_planner=self.storyline_planner,
        )
        # Sect system (独立宗门策略系统)
        self.sect_manager = SectManager()
        # Event Director (统一LLM调用: 选事件+叙事+分支)
        self.event_director = EventDirector(
            llm_client=self.llm_client,
            npc_manager=self.npc_manager,
            hook_manager=self.hook_manager,
            arc_planner=self.arc_planner,
            storyline_planner=self.storyline_planner,
            saga_manager=self.saga_manager,
            era_manager=self.era_manager,
            memory_manager=self.memory_manager,
        )

    # ── Public API ───────────────────────────────────────────────────

    def start_game(self) -> GameState:
        """Create a new game and return its initial state."""
        state = create_game()
        # Initialize sect world
        self.sect_manager.initialize_world(state)
        # Initialize world era system
        self.era_manager.initialize(state)
        return state

    def advance_year(self, game_id: str) -> NextYearResponse:
        """Advance the game by one story beat (variable time step based on realm)."""
        state = get_state(game_id)
        if state is None:
            raise ValueError(f"Game {game_id} not found")

        if state.is_dead or state.is_ascended:
            raise ValueError("Game is already over")

        # Block advancement if a player choice is pending
        if state.pending_choice is not None:
            raise ValueError("Pending choice must be resolved first")

        # Variable time step based on realm
        min_step, max_step = TIME_STEP_BY_REALM.get(state.realm, (1, 1))
        time_step = _rand.randint(min_step, max_step)
        state.age += time_step
        total_years = time_step  # Track total years for this turn
        events: list[dict] = []

        # Phase 1: Update life phase
        self.phase_manager.update_phase(state)

        # Phase 2: Natural death check (lifespan exhausted)
        death_event = self.death_system.check_natural_death(state)
        if death_event:
            events.append(death_event)
            self._post_year_update(state, events)
            return self._build_response(state, events, total_years)

        # Phase 3: Mortal awakening (only for realm == 0)
        awakening = self.realm_system.check_awakening(state)
        if awakening:
            events.append(awakening)
            self.phase_manager.update_phase(state)  # Immediately update phase
            # Auto sect-join on awakening (70% chance)
            sect_join = self.sect_manager.random_sect_join_at_awakening(state)
            if sect_join:
                events.append(sect_join)
                # Batch generate 2-3 fellow disciples for multi-NPC rotation
                self.npc_manager.generate_fellow_disciples(state, count=_rand.randint(2, 3))

        # Phase 4: Cultivation gain (scaled by time step)
        self.realm_system.process_cultivation(state, years=time_step)

        # Phase 5: Breakthrough foreshadow
        foreshadow = self.realm_system.check_breakthrough_foreshadow(state)
        if foreshadow:
            events.append(foreshadow)

        # Phase 5.5: Saga omen — foreshadow upcoming long-term narrative
        omen_text = self.saga_manager.check_omen(state)
        if omen_text:
            events.append({
                "text": omen_text,
                "event_type": "saga_omen",
                "tags": ["saga", "foreshadow"],
                "effects": {},
            })

        # Phase 6: Event selection via unified LLM Director
        # Get hook weight adjustments for event selection
        hook_adjustments = self.hook_manager.get_weight_adjustments(state)
        # Get world era category weight adjustments
        era_adjustments = self.era_manager.get_era_weight_adjustments(state)
        # Get story arc keywords for event selection
        arc_keywords = self._get_arc_keywords(state)
        # Get destiny keywords from main storyline (骨骼引导血肉, ×3 boost)
        destiny_keywords = self.storyline_planner.get_destiny_keywords(state)
        if destiny_keywords:
            arc_keywords = (arc_keywords or []) + destiny_keywords
        # Get causal chain resolution keywords (因果前瞻, ×2.5 boost via Layer 6)
        from .foreshadowing import get_causal_chain_keywords
        chain_keywords = get_causal_chain_keywords(state)
        if chain_keywords:
            arc_keywords = (arc_keywords or []) + chain_keywords

        # Phase 6.1: Priority events (NPC/Sect) - pure rules, no LLM
        priority_events = []
        # World era transition check
        era_event = self.era_manager.check_era_transition(state)
        if era_event:
            priority_events.append(era_event)

        # NPC destiny advancement FIRST (may kill NPCs, affecting subsequent checks)
        destiny_events = self.npc_manager.advance_npc_destiny(state)
        priority_events.extend(destiny_events)

        # Immediately sync tombstones for NPCs killed by destiny beats
        self._sync_dead_npc_tombstones(state)

        # NPC regular events AFTER destiny (dead NPCs naturally skipped by is_alive check)
        npc_events = self.npc_manager.check_npc_events(state)
        priority_events.extend(npc_events)

        # Periodic NPC encounter (wandering cultivators) — non-streaming path
        encounter_event = self.npc_manager.check_periodic_encounter(state)
        if encounter_event:
            priority_events.append(encounter_event)

        # Sect events
        sect_events = self.sect_manager.check_sect_events(state)
        priority_events.extend(sect_events)
        # Sect world evolution, promotion, crisis
        world_events = self.sect_manager.advance_sect_world(state)
        priority_events.extend(world_events)
        promotion_event = self.sect_manager.check_rank_promotion(state)
        if promotion_event:
            priority_events.append(promotion_event)
        crisis_event = self.sect_manager.check_sect_crisis(state)
        if crisis_event:
            priority_events.append(crisis_event)
        # Sect political intrigue (faction struggles, espionage, etc.)
        politics_event = self.sect_manager.check_sect_politics(state)
        if politics_event:
            priority_events.append(politics_event)
        # Check expulsion / demotion (reputation-based)
        expulsion = self.sect_manager.check_expulsion(state)
        if expulsion:
            priority_events.append(expulsion)
        else:
            demotion = self.sect_manager.check_demotion(state)
            if demotion:
                priority_events.append(demotion)
        # Wandering cultivator may get recruited by a new sect
        if not state.sect_membership:
            opportunity = self.sect_manager.check_new_sect_opportunity(state)
            if opportunity:
                priority_events.append(opportunity)

        # ── Mutual exclusion filter: remove conflicting events ──────────
        priority_events = self._filter_conflicting_priority_events(priority_events)

        for ev in priority_events:
            self.event_system.apply_effects(ev, state)
            events.append(ev)

        # Phase 6.2: Inject chain events from previous turn (priority)
        if state.pending_chain_events:
            chain_id = state.pending_chain_events.pop(0)
            chain_ev = find_event_by_id(chain_id)
            if chain_ev:
                self.event_system.apply_effects(chain_ev, state)
                self.npc_resolver.resolve_event(chain_ev, state)
                self.hook_manager.process_event(state, chain_ev)
                if chain_ev.get("id"):
                    state.used_event_ids.add(chain_ev["id"])
                events.append(chain_ev)

        # Phase 6.3: LLM Director selects main event (1 unified call)
        candidates = self.event_system.select_candidates(
            state, count=10,
            hook_adjustments=hook_adjustments if hook_adjustments else None,
            arc_keywords=arc_keywords if arc_keywords else None,
            era_adjustments=era_adjustments if era_adjustments else None,
        )
        # Apply causal chain weight boosts to candidates
        self.hook_manager.match_candidates_with_chains(state, candidates)
        director_result = self.event_director.direct_event(candidates, state)
        main_ev = candidates[director_result["chosen_index"]]["event"]
        main_ev["expanded_text"] = director_result["narrative"]
        # Track whether LLM was actually used this turn (for frontend indicator)
        ai_used_this_turn = director_result.get("ai_used", False)

        # Apply effects or set pending choice
        if director_result["has_choice"] and director_result.get("branches"):
            main_ev["branches"] = director_result["branches"]
            state.pending_choice = main_ev  # effects deferred to make_choice
        else:
            self.event_system.apply_effects(main_ev, state)

        # Phase 6.4: Post-processing for main event
        if main_ev.get("id"):
            state.used_event_ids.add(main_ev["id"])
        # Accumulate event duration
        event_duration = main_ev.get("duration", 0)
        if event_duration > 0:
            state.age += event_duration
            total_years += event_duration
            self.realm_system.process_cultivation(state, years=event_duration)
        # Resolve NPC slot
        self.npc_resolver.resolve_event(main_ev, state)
        # Process plot hooks (create/resolve)
        self.hook_manager.process_event(state, main_ev)
        # Handle dynamic causal chain from LLM output
        causal_chain_data = director_result.get("causal_chain")
        if causal_chain_data and isinstance(causal_chain_data, dict):
            self.hook_manager.create_causal_chain(state, causal_chain_data, main_ev)
        # Handle emotional token from LLM output (随身之物)
        token = director_result.get("emotional_token")
        if token and isinstance(token, dict):
            token["source_age"] = state.age
            state.emotional_tokens.append(token)
            if len(state.emotional_tokens) > 10:
                state.emotional_tokens = state.emotional_tokens[-10:]
        # Check for chain event trigger
        trigger_id = main_ev.get("effects", {}).get("trigger_event_id", "")
        if trigger_id:
            state.pending_chain_events.append(trigger_id)
        # Update NPC relationship
        if main_ev.get("involved_npc_id"):
            self.npc_manager.update_relationship(
                state,
                npc_id=main_ev["involved_npc_id"],
                delta_sentiment=self._calc_sentiment_delta(main_ev),
                interaction_type=main_ev.get("category", ""),
                event_text=main_ev.get("text", "")[:60],
            )
        events.append(main_ev)

        # Phase 6.4.1: Combat wound detection (战伤标记)
        if main_ev.get("event_type") == "danger" and {"combat", "calamity"} & set(main_ev.get("tags", [])):
            effects = main_ev.get("effects", {})
            if effects.get("constitution", 0) < 0 or effects.get("cultivation", 0) < -15:
                state.combat_wounded = True
                state.combat_wound_age = state.age

        # Phase 6.5: Force-resolve expired hooks
        expiring = self.hook_manager.check_expiring_hooks(state)
        for hook in expiring:
            resolution = self.hook_manager.generate_forced_resolution(state, hook)
            if resolution:
                self.hook_manager.process_event(state, resolution)
                events.append(resolution)

        # Phase 7: Breakthrough check
        breakthrough = self.realm_system.check_breakthrough(state)
        if breakthrough:
            # Inject active Saga context into breakthrough narrative
            saga_ctx = self.saga_manager.get_saga_context_for_ai(state)
            if saga_ctx:
                breakthrough["_saga_context"] = saga_ctx
            # Use breakthrough-specific narrative expansion
            bt_expanded = self.narrative.get_breakthrough_narrative(breakthrough, state)
            if bt_expanded:
                breakthrough["expanded_text"] = bt_expanded
            events.append(breakthrough)
            self.phase_manager.update_phase(state)  # Phase may change after breakthrough
            # Trigger story arc planning on breakthrough
            self.arc_planner.plan_arcs_for_realm(state, state.realm)
            # Generate main storyline on first breakthrough (骨骼初始化)
            if not state.main_storyline.get("storyline_id"):
                self.storyline_planner.generate_storyline(state, state.realm)
            # Generate new NPCs on realm breakthrough (non-streaming path)
            self.npc_manager.generate_realm_npcs(state, state.realm)

        # Phase 7.5: Combat death check (斗法致死)
        if main_ev.get("event_type") == "danger" and {"combat", "calamity"} & set(main_ev.get("tags", [])):
            cf_sync = director_result.get("combat_factors")
            if cf_sync:
                cf_sync = self._validate_combat_factors(state, cf_sync)
            combat_outcome = director_result.get("combat_outcome")
            combat_death = self.death_system.check_combat_death(state, main_ev, cf_sync, combat_outcome)
            if combat_death:
                events.append(combat_death)
                self._post_year_update(state, events)
                return self._build_response(state, events, total_years)
            # ── 战后结局分支处理 (存活时) ──
            self._process_combat_outcome(state, director_result, cf_sync, combat_outcome)

        # Phase 7.6: Combat loot (战后缴获 — 存活后的修行积累获取)
        # 非胜利结局不产出战利品
        combat_outcome_sync = director_result.get("combat_outcome")
        if combat_outcome_sync in ("enemy_fled", "player_fled", "draw"):
            pass  # 跳过战利品
        else:
            self._process_combat_loot(state, main_ev, director_result)

        # Phase 7.7: Ally NPC risk (助战NPC可能受伤/死亡)
        if main_ev.get("event_type") == "danger" and {"combat", "calamity"} & set(main_ev.get("tags", [])):
            self._process_ally_risk(state, director_result.get("combat_factors"), survived=not state.is_dead)

        # Phase 8: Accidental death check (based on post-event state)
        accidental_death = self.death_system.check_accidental_death(state)
        if accidental_death:
            events.append(accidental_death)
            self._post_year_update(state, events)
            return self._build_response(state, events, total_years)

        # Phase 9: Tribulation (post-化神)
        tribulation = self.realm_system.check_tribulation(state)
        if tribulation:
            events.append(tribulation)
            # Tribulation may result in ascension or death
            if state.is_ascended or state.is_dead:
                self._post_year_update(state, events)
                return self._build_response(state, events, total_years)

        # Phase 10: Update context, memory, and NPC aging
        self._post_year_update(state, events)

        return self._build_response(state, events, total_years, ai_used=ai_used_this_turn)

    # ── Streaming variant ────────────────────────────────────────────

    def advance_year_stream(self, game_id: str) -> Generator[dict, None, None]:
        """Streaming variant of advance_year.

        Yields SSE-ready events:
          {"event": "state", "data": {partial game data without expanded_text}}
          {"event": "narrative_chunk", "data": "text fragment"}
          {"event": "done", "data": {final data with choice/branches/ai_enhanced}}
        """
        state = get_state(game_id)
        if state is None:
            raise ValueError(f"Game {game_id} not found")

        if state.is_dead or state.is_ascended:
            raise ValueError("Game is already over")

        if state.pending_choice is not None:
            raise ValueError("Pending choice must be resolved first")

        # Variable time step based on realm
        min_step, max_step = TIME_STEP_BY_REALM.get(state.realm, (1, 1))
        time_step = _rand.randint(min_step, max_step)
        state.age += time_step
        total_years = time_step
        events: list[dict] = []

        # Phase 1: Update life phase
        self.phase_manager.update_phase(state)

        # Phase 2: Natural death check
        death_event = self.death_system.check_natural_death(state)
        if death_event:
            events.append(death_event)
            self._post_year_update(state, events)
            resp = self._build_response(state, events, total_years)
            yield {"event": "state", "data": resp.model_dump()}
            yield {"event": "done", "data": {"ai_enhanced": False}}
            return

        # Phase 3: Mortal awakening
        awakening = self.realm_system.check_awakening(state)
        if awakening:
            events.append(awakening)
            self.phase_manager.update_phase(state)
            sect_join = self.sect_manager.random_sect_join_at_awakening(state)
            if sect_join:
                events.append(sect_join)
                # Batch generate 2-3 fellow disciples for multi-NPC rotation
                self.npc_manager.generate_fellow_disciples(state, count=_rand.randint(2, 3))

        # Phase 4: Cultivation gain
        self.realm_system.process_cultivation(state, years=time_step)

        # Phase 5: Breakthrough foreshadow
        foreshadow = self.realm_system.check_breakthrough_foreshadow(state)
        if foreshadow:
            events.append(foreshadow)

        # Phase 5.5: Saga omen — foreshadow upcoming long-term narrative
        omen_text = self.saga_manager.check_omen(state)
        if omen_text:
            events.append({
                "text": omen_text,
                "event_type": "saga_omen",
                "tags": ["saga", "foreshadow"],
                "effects": {},
            })

        # Phase 6: Event selection
        hook_adjustments = self.hook_manager.get_weight_adjustments(state)
        era_adjustments = self.era_manager.get_era_weight_adjustments(state)
        arc_keywords = self._get_arc_keywords(state)
        destiny_keywords = self.storyline_planner.get_destiny_keywords(state)
        if destiny_keywords:
            arc_keywords = (arc_keywords or []) + destiny_keywords
        # Causal chain resolution keywords (因果前瞻, ×2.5 boost via Layer 6)
        from .foreshadowing import get_causal_chain_keywords
        chain_keywords = get_causal_chain_keywords(state)
        if chain_keywords:
            arc_keywords = (arc_keywords or []) + chain_keywords

        # Phase 6.1: Priority events
        priority_events = []
        # World era transition check
        era_event = self.era_manager.check_era_transition(state)
        if era_event:
            priority_events.append(era_event)

        # NPC destiny advancement FIRST (may kill NPCs, affecting subsequent checks)
        destiny_events = self.npc_manager.advance_npc_destiny(state)
        priority_events.extend(destiny_events)

        # Immediately sync tombstones for NPCs killed by destiny beats
        self._sync_dead_npc_tombstones(state)

        # NPC regular events AFTER destiny (dead NPCs naturally skipped)
        npc_events = self.npc_manager.check_npc_events(state)
        priority_events.extend(npc_events)

        # Periodic NPC encounter (wandering cultivators)
        encounter_event = self.npc_manager.check_periodic_encounter(state)
        if encounter_event:
            priority_events.append(encounter_event)

        # Sect events
        sect_events = self.sect_manager.check_sect_events(state)
        priority_events.extend(sect_events)
        world_events = self.sect_manager.advance_sect_world(state)
        priority_events.extend(world_events)
        promotion_event = self.sect_manager.check_rank_promotion(state)
        if promotion_event:
            priority_events.append(promotion_event)
        crisis_event = self.sect_manager.check_sect_crisis(state)
        if crisis_event:
            priority_events.append(crisis_event)
        # Sect political intrigue (streaming path)
        politics_event = self.sect_manager.check_sect_politics(state)
        if politics_event:
            priority_events.append(politics_event)
        # Check expulsion / demotion (streaming path)
        expulsion = self.sect_manager.check_expulsion(state)
        if expulsion:
            priority_events.append(expulsion)
        else:
            demotion = self.sect_manager.check_demotion(state)
            if demotion:
                priority_events.append(demotion)
        # Wandering cultivator may get recruited (streaming path)
        if not state.sect_membership:
            opportunity = self.sect_manager.check_new_sect_opportunity(state)
            if opportunity:
                priority_events.append(opportunity)

        # ── Mutual exclusion filter: remove conflicting events ──────────
        priority_events = self._filter_conflicting_priority_events(priority_events)

        for ev in priority_events:
            self.event_system.apply_effects(ev, state)
            events.append(ev)

        # Phase 6.2: Chain events
        if state.pending_chain_events:
            chain_id = state.pending_chain_events.pop(0)
            chain_ev = find_event_by_id(chain_id)
            if chain_ev:
                self.event_system.apply_effects(chain_ev, state)
                self.npc_resolver.resolve_event(chain_ev, state)
                self.hook_manager.process_event(state, chain_ev)
                if chain_ev.get("id"):
                    state.used_event_ids.add(chain_ev["id"])
                events.append(chain_ev)

        # Phase 6.3: LLM Director STREAMING
        candidates = self.event_system.select_candidates(
            state, count=10,
            hook_adjustments=hook_adjustments if hook_adjustments else None,
            arc_keywords=arc_keywords if arc_keywords else None,
            era_adjustments=era_adjustments if era_adjustments else None,
        )
        # Apply causal chain weight boosts to candidates
        self.hook_manager.match_candidates_with_chains(state, candidates)

        # Collect streaming result
        meta_data = None
        narrative_chunks: list[str] = []
        ai_used_this_turn = False

        for chunk in self.event_director.direct_event_stream(candidates, state):
            if chunk["type"] == "meta":
                meta_data = chunk["data"]
                ai_used_this_turn = meta_data.get("ai_used", False)
                # Now we have chosen event, yield partial state
                main_ev = candidates[meta_data["chosen_index"]]["event"]
                partial_events = []
                for ev in events:
                    partial_events.append({
                        "text": ev.get("text", ""),
                        "expanded_text": "",
                        "type": ev.get("event_type", "normal"),
                        "category": ev.get("category", "common"),
                        "age": state.age,
                    })
                # Add main event header (no narrative yet)
                partial_events.append({
                    "text": main_ev.get("text", ""),
                    "expanded_text": "",
                    "type": main_ev.get("event_type", "normal"),
                    "category": main_ev.get("category", "common"),
                    "age": state.age,
                })
                yield {"event": "state", "data": {
                    "age": state.age,
                    "realm": state.realm,
                    "realm_name": REALM_NAMES.get(Realm(state.realm), "未知"),
                    "cultivation": state.cultivation,
                    "cultivation_max": REALM_THRESHOLDS.get(state.realm, 99999),
                    "events": partial_events,
                    "attributes": state.attributes.model_dump(),
                    "tension": state.tension,
                }}
            elif chunk["type"] == "narrative_chunk":
                narrative_chunks.append(chunk["data"])
                yield {"event": "narrative_chunk", "data": chunk["data"]}
            # "done" from event_director just means stream ended

        # Assemble full narrative
        full_narrative = "".join(narrative_chunks)

        # Now apply game effects (same as advance_year Phase 6.3+)
        if meta_data is None:
            meta_data = {"chosen_index": 0, "has_choice": False, "branches": None}

        main_ev = candidates[meta_data["chosen_index"]]["event"]
        main_ev["expanded_text"] = full_narrative

        if meta_data["has_choice"] and meta_data.get("branches"):
            main_ev["branches"] = meta_data["branches"]
            state.pending_choice = main_ev
        else:
            self.event_system.apply_effects(main_ev, state)

        # Phase 6.4: Post-processing
        if main_ev.get("id"):
            state.used_event_ids.add(main_ev["id"])
        event_duration = main_ev.get("duration", 0)
        if event_duration > 0:
            state.age += event_duration
            total_years += event_duration
            self.realm_system.process_cultivation(state, years=event_duration)
        self.npc_resolver.resolve_event(main_ev, state)
        self.hook_manager.process_event(state, main_ev)
        # Handle dynamic causal chain from streaming LLM output
        causal_chain_data = meta_data.get("causal_chain")
        if causal_chain_data and isinstance(causal_chain_data, dict):
            self.hook_manager.create_causal_chain(state, causal_chain_data, main_ev)
        # Handle emotional token from streaming LLM output (随身之物)
        token = meta_data.get("emotional_token")
        if token and isinstance(token, dict):
            token["source_age"] = state.age
            state.emotional_tokens.append(token)
            if len(state.emotional_tokens) > 10:
                state.emotional_tokens = state.emotional_tokens[-10:]
        trigger_id = main_ev.get("effects", {}).get("trigger_event_id", "")
        if trigger_id:
            state.pending_chain_events.append(trigger_id)
        if main_ev.get("involved_npc_id"):
            self.npc_manager.update_relationship(
                state,
                npc_id=main_ev["involved_npc_id"],
                delta_sentiment=self._calc_sentiment_delta(main_ev),
                interaction_type=main_ev.get("category", ""),
                event_text=main_ev.get("text", "")[:60],
            )
        events.append(main_ev)

        # Phase 6.4.1: Combat wound detection (战伤标记)
        if main_ev.get("event_type") == "danger" and {"combat", "calamity"} & set(main_ev.get("tags", [])):
            effects = main_ev.get("effects", {})
            if effects.get("constitution", 0) < 0 or effects.get("cultivation", 0) < -15:
                state.combat_wounded = True
                state.combat_wound_age = state.age

        # Phase 6.5: Expired hooks
        expiring = self.hook_manager.check_expiring_hooks(state)
        for hook in expiring:
            resolution = self.hook_manager.generate_forced_resolution(state, hook)
            if resolution:
                self.hook_manager.process_event(state, resolution)
                events.append(resolution)

        # Phase 7: Breakthrough
        breakthrough = self.realm_system.check_breakthrough(state)
        if breakthrough:
            bt_expanded = self.narrative.get_breakthrough_narrative(breakthrough, state)
            if bt_expanded:
                breakthrough["expanded_text"] = bt_expanded
            events.append(breakthrough)
            self.phase_manager.update_phase(state)
            self.arc_planner.plan_arcs_for_realm(state, state.realm)
            if not state.main_storyline.get("storyline_id"):
                self.storyline_planner.generate_storyline(state, state.realm)
            # Generate new NPCs on realm breakthrough
            self.npc_manager.generate_realm_npcs(state, state.realm)

        # Phase 7.5: Combat death check (斗法致死)
        if main_ev.get("event_type") == "danger" and {"combat", "calamity"} & set(main_ev.get("tags", [])):
            cf = meta_data.get("combat_factors") if meta_data else None
            if cf:
                cf = self._validate_combat_factors(state, cf)
            combat_outcome = meta_data.get("combat_outcome") if meta_data else None
            combat_death = self.death_system.check_combat_death(state, main_ev, cf, combat_outcome)
            if combat_death:
                events.append(combat_death)
                self._post_year_update(state, events)
                self._record_events_log(state, events)
                done_data = {
                    "ai_enhanced": ai_used_this_turn,
                    "is_dead": state.is_dead,
                    "is_ascended": state.is_ascended,
                    "death_reason": state.death_reason,
                    "has_choice": False,
                    "years_passed": total_years,
                }
                yield {"event": "done", "data": done_data}
                return
            # ── 战后结局分支处理 (存活时) ──
            self._process_combat_outcome(state, meta_data, cf, combat_outcome)

        # Phase 7.6: Combat loot (战后缴获 — 存活后的修行积累获取)
        # 非胜利结局不产出战利品
        stream_combat_outcome = meta_data.get("combat_outcome") if meta_data else None
        if stream_combat_outcome in ("enemy_fled", "player_fled", "draw"):
            pass  # 跳过战利品
        else:
            self._process_combat_loot(state, main_ev, meta_data)

        # Phase 7.7: Ally NPC risk (助战NPC可能受伤/死亡)
        if main_ev.get("event_type") == "danger" and {"combat", "calamity"} & set(main_ev.get("tags", [])):
            cf = meta_data.get("combat_factors") if meta_data else None
            self._process_ally_risk(state, cf, survived=not state.is_dead)

        # Phase 8: Accidental death (early termination like sync version)
        accidental_death = self.death_system.check_accidental_death(state)
        if accidental_death:
            events.append(accidental_death)
            self._post_year_update(state, events)
            self._record_events_log(state, events)
            done_data = {
                "ai_enhanced": ai_used_this_turn,
                "is_dead": state.is_dead,
                "is_ascended": state.is_ascended,
                "death_reason": state.death_reason,
                "has_choice": False,
                "years_passed": total_years,
            }
            yield {"event": "done", "data": done_data}
            return

        # Phase 9: Tribulation (may cause death/ascension)
        tribulation = self.realm_system.check_tribulation(state)
        if tribulation:
            events.append(tribulation)
            if state.is_ascended or state.is_dead:
                self._post_year_update(state, events)
                self._record_events_log(state, events)
                done_data = {
                    "ai_enhanced": ai_used_this_turn,
                    "is_dead": state.is_dead,
                    "is_ascended": state.is_ascended,
                    "death_reason": state.death_reason,
                    "has_choice": False,
                    "years_passed": total_years,
                }
                yield {"event": "done", "data": done_data}
                return

        # Phase 10: Post-year update
        self._post_year_update(state, events)
        self._record_events_log(state, events)

        # Build final done data
        done_data = {
            "ai_enhanced": ai_used_this_turn,
            "is_dead": state.is_dead,
            "is_ascended": state.is_ascended,
            "death_reason": state.death_reason,
            "has_choice": state.pending_choice is not None,
            "years_passed": total_years,
        }
        if state.pending_choice is not None:
            ce = state.pending_choice
            done_data["choice_event"] = {
                "id": ce.get("id", ""),
                "text": self._inject_npc_names(ce.get("text", ""), state),
                "expanded_text": self._inject_npc_names(ce.get("expanded_text", ""), state),
                "type": ce.get("event_type", "normal"),
                "category": ce.get("category", "common"),
                "age": state.age,
                "branches": ce.get("branches"),
            }

        yield {"event": "done", "data": done_data}

    def _record_events_log(self, state: GameState, events: list) -> None:
        """Record events into state.events_log (streaming path doesn't call _build_response)."""
        for ev in events:
            state.events_log.append({
                "age": state.age,
                "text": ev.get("text", ""),
                "category": ev.get("category", "common"),
                "event_type": ev.get("event_type", "normal"),
            })

    def _post_year_update(self, state: GameState, events: list) -> None:
        """End-of-year housekeeping: memory recording, NPC aging, arc advancement, destiny advancement, tension update, context update."""
        # 战伤自动痊愈（2回合后）
        if getattr(state, "combat_wounded", False):
            if state.age - getattr(state, "combat_wound_age", 0) >= 2:
                state.combat_wounded = False

        self.memory_manager.tick_year(state)
        self.npc_manager.age_npcs(state)
        # Advance story arcs based on events + check for saga emergence
        for ev in events:
            completed_arc = self.arc_planner.advance_arc_beat(state, ev)
            if completed_arc:
                self.saga_manager.on_arc_completed(state, completed_arc)
        # Auto-advance stale arcs (prevent permanent stall)
        stale_completed = self.arc_planner.auto_advance_stale_arcs(state)
        if stale_completed:
            self.saga_manager.on_arc_completed(state, stale_completed)
        # Ensure minimum arc supply for saga emergence
        self.arc_planner.ensure_minimum_arcs(state)
        # Check saga completion conditions
        self.saga_manager.check_saga_completion(state)
        # Advance main storyline + flesh-to-skeleton feedback (血肉反哺骨骼)
        self.storyline_planner.advance_destiny(state, events)
        # Check NPC destiny pivots (after dramatic events)
        self.npc_manager.check_destiny_pivots(state, events)
        # Check expiring causal chains (forced resolutions added to events)
        expiring_chains = self.hook_manager.check_expiring_chains(state)
        for chain in expiring_chains:
            resolution = self.hook_manager.generate_forced_resolution(state, chain)
            if resolution:
                events.append(resolution)
        # ── Rule-based causal chain creation for ALL events in this turn ──
        for ev in events:
            self.hook_manager._try_rule_based_chain(state, ev)
        # ── Rule-based causal chain creation for ALL events in this turn ──
        for ev in events:
            self.hook_manager._try_rule_based_chain(state, ev)
        # ── Record ALL events into memory (after forced resolutions) ───
        self.memory_manager.record_events(state, events)
        # ── Tension curve update (with peril feedback loop) ────────────
        delta = 0.0
        for ev in events:
            et = ev.get("event_type", "normal")
            delta += TENSION_BY_EVENT_TYPE.get(et, 0.0)
        # Apply world era tension modifier
        era_tension_mod = self.era_manager.get_tension_modifier(state)
        # Peril-tension coupling: high peril reduces tension decay (danger lingers)
        # At peril=100, decay is reduced to 33%; at peril=50, decay is 67%
        peril_factor = max(0.3, 1.0 - state.peril_index / 150.0)
        effective_decay = TENSION_DECAY_PER_TURN * peril_factor
        state.tension = max(0.0, min(100.0, state.tension + delta - effective_decay + era_tension_mod))
        # ── Peril (因果驱动危险系数) update ───────────────────────────
        self._update_peril(state, events)
        self.context.update(state, events)

    @staticmethod
    def _calc_sentiment_delta(event: dict) -> int:
        """Calculate sentiment change from an event's type/effects."""
        event_type = event.get("event_type", "normal")
        category = event.get("category", "")
        effects = event.get("effects", {})

        delta = 0
        if event_type == "fortune":
            delta = 5
        elif event_type == "danger":
            delta = -3
        elif category == "social":
            delta = 3

        # Positive effects increase sentiment
        if effects.get("cultivation", 0) > 0:
            delta += 2
        if effects.get("comprehension", 0) > 0:
            delta += 2
        if effects.get("constitution", 0) < 0:
            delta -= 3  # Injury implies negative interaction

        return max(-10, min(10, delta))

    # ── Combat factors validation & ally risk ────────────────────

    @staticmethod
    def _validate_combat_factors(state: GameState, combat_factors: dict) -> dict:
        """Validate LLM-chosen ally_npc_id against actual game state.

        If the NPC is dead or sentiment < 30, strip ally_npc_id to None.
        """
        if not combat_factors:
            return combat_factors
        ally_id = combat_factors.get("ally_npc_id")
        if not ally_id:
            return combat_factors

        # Check NPC exists, is alive, and has sentiment >= 30
        npc_dict = state.npc_registry.get(ally_id)
        if not npc_dict or not npc_dict.get("is_alive", True):
            combat_factors["ally_npc_id"] = None
            return combat_factors

        # Check relationship sentiment
        for rel in state.relationships:
            if rel.get("npc_id") == ally_id:
                if rel.get("sentiment", 0) < 30:
                    combat_factors["ally_npc_id"] = None
                return combat_factors

        # NPC exists but no relationship found -> cannot assist
        combat_factors["ally_npc_id"] = None
        return combat_factors

    def _process_ally_risk(self, state: GameState, combat_factors: dict, survived: bool) -> None:
        """After combat, the assisting NPC may get hurt or killed.

        - 10% chance ally gets injured (sentiment +5 due to shared danger)
        - 3% chance ally dies (creates blood_feud peril source)
        Only triggers if character survived (dead characters don't witness ally fate).
        """
        if not combat_factors or not survived:
            return
        ally_id = combat_factors.get("ally_npc_id")
        if not ally_id:
            return

        npc_dict = state.npc_registry.get(ally_id)
        if not npc_dict or not npc_dict.get("is_alive", True):
            return

        roll = _rand.random()
        if roll < 0.03:
            # Ally killed in combat (3%)
            npc_dict["is_alive"] = False
            # Update relationship sentiment (grief) and sync tombstone
            for rel in state.relationships:
                if rel.get("npc_id") == ally_id:
                    rel["is_dead"] = True
                    rel["sentiment"] = max(0, rel.get("sentiment", 50) - 20)
                    # Determine intensity based on relation type
                    is_close = rel.get("relation_type") in ("道侣", "师父")
                    intensity = PERIL_CONTRIB["blood_feud"] if is_close else PERIL_CONTRIB["blood_feud"] // 2
                    state.peril_sources.append({
                        "type": "blood_feud",
                        "intensity": intensity,
                        "reason": f"助战{npc_dict.get('name', 'NPC')}战死",
                        "source_age": state.age,
                    })
                    break
        elif roll < 0.13:
            # Ally injured but survived (10%) -> shared danger bonding
            for rel in state.relationships:
                if rel.get("npc_id") == ally_id:
                    rel["sentiment"] = min(100, rel.get("sentiment", 50) + 5)
                    break

    # ── Peril system (因果驱动危险系数) ────────────────────────

    def _update_peril(self, state: GameState, events: list) -> None:
        """Update peril_sources based on this turn's events, then aggregate.

        Peril sources decay over time and grow when narrative causality events happen.
        """
        sources = state.peril_sources

        # ---- 1. Decay all existing sources ----
        has_sect = state.sect_membership is not None
        for src in sources:
            src["intensity"] -= PERIL_DECAY_PER_TURN
            if has_sect:
                src["intensity"] -= PERIL_SECT_PROTECTION

        # Low-profile bonus: 3+ consecutive turns without combat/fortune
        recent_types = [ev.get("event_type") for ev in state.events_log[-3:]] if len(state.events_log) >= 3 else []
        if recent_types and all(t not in ("danger", "fortune") for t in recent_types):
            for src in sources:
                src["intensity"] -= PERIL_LOW_PROFILE_BONUS

        # ---- 2. Add new peril sources from this turn's events ----
        for ev in events:
            et = ev.get("event_type", "")
            tags = set(ev.get("tags", []))
            effects = ev.get("effects", {})

            # 2a. 怀璧其罪: 获得修行积累
            loot_power = ev.get("combat_loot", {}).get("power", 0) if isinstance(ev.get("combat_loot"), dict) else 0
            if loot_power > 0:
                sources.append({
                    "type": "treasure_envy",
                    "intensity": loot_power * PERIL_CONTRIB["treasure_envy"],
                    "reason": f"获得{ev.get('combat_loot', {}).get('name', '宝物')}",
                    "source_age": state.age,
                })

            # 2b. fortune事件触发 (顺境招忌)
            if et == "fortune":
                sources.append({
                    "type": "fortune_streak",
                    "intensity": PERIL_CONTRIB["fortune_streak"],
                    "reason": ev.get("text", "机缘降临")[:20],
                    "source_age": state.age,
                })

            # 2b2. danger+combat事件 (经历杀伐→招来注目)
            if et == "danger" and (tags & {"combat", "calamity"}):
                sources.append({
                    "type": "danger_exposure",
                    "intensity": PERIL_CONTRIB.get("danger_exposure", 15),
                    "reason": ev.get("text", "杀伐之气")[:20],
                    "source_age": state.age,
                })

            # 2c. 突破境界 (树大招风)
            if "breakthrough" in tags or ev.get("id", "").startswith("breakthrough"):
                sources.append({
                    "type": "fame",
                    "intensity": PERIL_CONTRIB["fame"],
                    "reason": "突破境界",
                    "source_age": state.age,
                })

            # 2d. 宗门覆灭 (丧宗之仇)
            if "sect_destroyed" in tags or "sect_disbanded" in tags:
                sources.append({
                    "type": "sect_destroyed",
                    "intensity": PERIL_CONTRIB["sect_destroyed"],
                    "reason": "宗门覆灭",
                    "source_age": state.age,
                })

            # 2e. NPC死亡 (血仇驱动) - 检查NPC命运事件中的死亡
            _DEATH_KW = ("陨落", "身亡", "殒命", "战死", "身死", "化道", "坐化", "魂飞魄散")
            if "npc_destiny" in tags or "npc_death" in tags or "partner_death" in tags or "master_death" in tags:
                ev_text = ev.get("text", "") + ev.get("expanded_text", "")
                npc_died = any(kw in ev_text for kw in _DEATH_KW)
                if not npc_died and ev.get("effects", {}).get("npc_death"):
                    npc_died = True
                if npc_died:
                    # Check if the dead NPC is a close relation (道侣/师父 → higher intensity)
                    involved_npc_id = ev.get("involved_npc_id", "")
                    is_close = False
                    if involved_npc_id:
                        for rel in state.relationships:
                            if rel.get("npc_id") == involved_npc_id:
                                if rel.get("relation_type") in ("道侣", "师父"):
                                    is_close = True
                                break
                    intensity = PERIL_CONTRIB["blood_feud"] if is_close else PERIL_CONTRIB["blood_feud"] // 2
                    sources.append({
                        "type": "blood_feud",
                        "intensity": intensity,
                        "reason": ev.get("text", "至亲被杀")[:20],
                        "source_age": state.age,
                    })

        # 2f. 分支选择后果 (因果纠缠) - 检查choice_history最后一条
        if state.choice_history:
            last_choice = state.choice_history[-1]
            if last_choice.get("age") == state.age and last_choice.get("consequence_tag"):
                sources.append({
                    "type": "consequence",
                    "intensity": PERIL_CONTRIB["consequence"],
                    "reason": last_choice.get("consequence_tag", "因果纠缠")[:20],
                    "source_age": state.age,
                })

        # ---- 3. Dedup: keep only the highest-intensity source per (type, npc_id) ----
        # This prevents the same NPC death from stacking multiple blood_feud entries
        dedup_map: dict[tuple, dict] = {}
        for src in sources:
            if src.get("intensity", 0) <= 0:
                continue
            # For blood_feud, key includes the reason (contains NPC name) to distinguish
            # For other types, key is (type, source_age) to allow same-type from different turns
            src_type = src.get("type", "")
            if src_type == "blood_feud":
                # Group by type + reason prefix (NPC name in first 10 chars)
                key = (src_type, src.get("reason", "")[:10])
            else:
                # Non-blood_feud: allow multiple of same type from different ages
                key = (src_type, src.get("source_age", 0), src.get("reason", "")[:10])
            existing = dedup_map.get(key)
            if existing is None or src["intensity"] > existing["intensity"]:
                dedup_map[key] = src
        state.peril_sources = list(dedup_map.values())

        # ---- 4. Aggregate peril_index and determine dominant source ----
        if state.peril_sources:
            state.peril_index = min(100.0, sum(s["intensity"] for s in state.peril_sources))
            dominant = max(state.peril_sources, key=lambda s: s["intensity"])
            state.peril_dominant = dominant["type"]
        else:
            state.peril_index = 0.0
            state.peril_dominant = ""

    # ── Combat outcome processing (战后结局分支) ───────────────────────

    def _process_combat_outcome(self, state: GameState, director_result: dict,
                                combat_factors: dict = None,
                                combat_outcome: str = None) -> None:
        """Process post-combat outcome effects when the player survives.

        Outcome effects:
        - victory: enemy NPC may die (50%) or create revenge causal chain (50%)
        - enemy_fled: no loot, create causal chain "此仇未了", peril += danger_exposure
        - player_fled: peril += 10, tension += 15, create causal chain
        - draw: tension += 10
        """
        if not combat_outcome or combat_outcome not in ("victory", "enemy_fled", "player_fled", "draw"):
            return

        # Get enemy NPC id from combat_factors
        enemy_npc_id = None
        if combat_factors and isinstance(combat_factors, dict):
            enemy_npc_id = combat_factors.get("enemy_npc_id")

        if combat_outcome == "victory":
            # 胜利: 敌方NPC 50%死亡, 50%重伤+因果链
            if enemy_npc_id and enemy_npc_id in state.npc_registry:
                npc = state.npc_registry[enemy_npc_id]
                if npc.get("is_alive", True):
                    if _rand.random() < 0.5:
                        # 击杀敌方NPC
                        npc["is_alive"] = False
                        npc["death_age"] = state.age
                        npc["death_reason"] = "斗法败亡"
                    else:
                        # 重伤逃脱 → 创建因果链
                        npc_name = npc.get("name", "仇敌")
                        self.hook_manager.create_causal_chain(state, {
                            "cause": f"你击败{npc_name}，但未能将其斩杀",
                            "expected_resolution": f"{npc_name}重伤遁逃，此仇必报",
                            "keywords": [npc_name, "复仇", "重伤"],
                        }, {"text": f"{npc_name}重伤遁逃", "involved_npc_id": enemy_npc_id, "involved_npc": npc_name})

        elif combat_outcome == "enemy_fled":
            # 敌逃: 无战利品(已在调用侧处理)，因果链 + peril
            if enemy_npc_id and enemy_npc_id in state.npc_registry:
                npc = state.npc_registry[enemy_npc_id]
                npc_name = npc.get("name", "仇敌")
                self.hook_manager.create_causal_chain(state, {
                    "cause": f"{npc_name}见势不妙遁逃",
                    "expected_resolution": f"{npc_name}此仇未了，日后必有纠葛",
                    "keywords": [npc_name, "遁逃", "未了"],
                }, {"text": f"{npc_name}遁逃", "involved_npc_id": enemy_npc_id, "involved_npc": npc_name})
            # 增加peril (敌人逃走可能伺机报复)
            state.peril_sources.append({
                "type": "danger_exposure",
                "intensity": PERIL_CONTRIB.get("danger_exposure", 15),
                "reason": "仇敌遁逃",
                "source_age": state.age,
            })
            state.peril_index = min(100.0, sum(s["intensity"] for s in state.peril_sources))

        elif combat_outcome == "player_fled":
            # 我方逃跑: peril += 10, tension += 15, 因果链
            state.peril_sources.append({
                "type": "danger_exposure",
                "intensity": 10,
                "reason": "夺路而逃",
                "source_age": state.age,
            })
            state.peril_index = min(100.0, sum(s["intensity"] for s in state.peril_sources))
            state.tension = min(100, getattr(state, "tension", 0) + 15)
            if enemy_npc_id and enemy_npc_id in state.npc_registry:
                npc = state.npc_registry[enemy_npc_id]
                npc_name = npc.get("name", "仇敌")
                self.hook_manager.create_causal_chain(state, {
                    "cause": f"你败逃于{npc_name}之手",
                    "expected_resolution": f"{npc_name}知你已力竭，早晚再来追杀",
                    "keywords": [npc_name, "败逃", "追杀"],
                }, {"text": f"败逃于{npc_name}", "involved_npc_id": enemy_npc_id, "involved_npc": npc_name})

        elif combat_outcome == "draw":
            # 平手: tension += 10, 保持对抗状态
            state.tension = min(100, getattr(state, "tension", 0) + 10)

    # ── Combat loot system (战后缴获) ─────────────────────────────────

    def _process_combat_loot(self, state: GameState, main_ev: dict, director_result: dict) -> None:
        """Process combat loot after surviving a danger+combat event.

        Two paths:
        1. LLM explicitly output a combat_loot field (validated by event_director)
        2. Probability-based fallback: 15% base * (1 + fortune*0.03)
        Both paths store the item in state.combat_repertoire.
        """
        # Only trigger for danger+combat events that the character survived
        if main_ev.get("event_type") != "danger":
            return
        if not ({"combat", "calamity"} & set(main_ev.get("tags", []))):
            return

        # Path 1: LLM provided combat_loot
        loot = director_result.get("combat_loot")
        if loot and isinstance(loot, dict) and loot.get("name"):
            self._store_repertoire_item(state, loot)
            return

        # Path 2: Probability-based fallback (no LLM loot)
        fortune = getattr(state.attributes, "fortune", 5)
        loot_chance = 0.15 * (1 + fortune * 0.03)
        if _rand.random() < loot_chance:
            from .repertoire_pool import sample_acquisition_items
            items = sample_acquisition_items(state, count=1)
            if items:
                self._store_repertoire_item(state, items[0])

    @staticmethod
    def _store_repertoire_item(state: GameState, item: dict) -> None:
        """Store a single repertoire item into state, respecting capacity limit."""
        name = item.get("name", "")
        if not name:
            return
        owned = {r["name"] for r in state.combat_repertoire}
        if name in owned:
            return  # Already owned, no duplicate
        state.combat_repertoire.append({
            "name": name,
            "category": item.get("category", "treasure"),
            "desc": str(item.get("desc", ""))[:30],
            "power": min(5, max(1, int(item.get("power", 2)))),
            "source_age": state.age,
        })
        # Capacity: 15 items max, discard lowest power
        if len(state.combat_repertoire) > 15:
            state.combat_repertoire.sort(key=lambda x: x.get("power", 0))
            state.combat_repertoire = state.combat_repertoire[1:]

    # ── Priority event mutual exclusion ───────────────────────────────

    @staticmethod
    def _filter_conflicting_priority_events(events: list[dict]) -> list[dict]:
        """Remove mutually exclusive events from the priority event list.

        Rules:
        1. Expulsion/demotion → cancel sect promotion, politics, crisis events
        2. NPC death (destiny beat) → cancel regular events for the same NPC
        3. Sect joined → cancel "new sect opportunity" events
        """
        if not events:
            return events

        # Detect conflict signals
        has_expulsion = any("expulsion" in str(ev.get("tags", [])) or
                           "逐出" in ev.get("text", "") or
                           "开除" in ev.get("text", "")
                           for ev in events)
        has_demotion = any("demotion" in str(ev.get("tags", [])) or
                          "降职" in ev.get("text", "") or
                          "贬为" in ev.get("text", "")
                          for ev in events)

        # Collect NPC IDs that died in destiny beats this turn
        dead_npc_ids: set[str] = set()
        for ev in events:
            if "npc_destiny" in str(ev.get("tags", [])):
                ev_text = ev.get("text", "") + ev.get("expanded_text", "")
                if "陨落" in ev_text or "身亡" in ev_text or "殒命" in ev_text:
                    npc_id = ev.get("involved_npc_id", "")
                    if npc_id:
                        dead_npc_ids.add(npc_id)

        # Apply exclusion rules
        filtered = []
        for ev in events:
            ev_tags = set(ev.get("tags", []))
            ev_text = ev.get("text", "")

            # Rule 1: Expulsion cancels positive sect events
            if has_expulsion:
                if any(t in ev_tags for t in ("sect_promotion", "sect_politics", "sect_crisis")):
                    continue
                if "晋升" in ev_text or "擢升" in ev_text:
                    continue

            # Rule 1b: Demotion cancels promotion
            if has_demotion:
                if "sect_promotion" in ev_tags or "晋升" in ev_text:
                    continue

            # Rule 2: Dead NPC cancels their regular events
            if dead_npc_ids:
                ev_npc_id = ev.get("involved_npc_id", "")
                if ev_npc_id and ev_npc_id in dead_npc_ids:
                    # Keep the destiny death event itself, skip others
                    if "npc_destiny" not in str(ev_tags):
                        continue

            filtered.append(ev)

        return filtered

    @staticmethod
    def _sync_dead_npc_tombstones(state: GameState) -> None:
        """Immediately mark relationships as dead for NPCs whose is_alive was set to False.

        This ensures tombstones are in place before subsequent systems
        (check_npc_events, event_system.check_conditions) query relationships.
        """
        for rel in state.relationships:
            if rel.get("is_dead"):
                continue
            npc_id = rel.get("npc_id", "")
            npc_dict = state.npc_registry.get(npc_id)
            if npc_dict and not npc_dict.get("is_alive", True):
                rel["is_dead"] = True

    @staticmethod
    def _get_arc_keywords(state: GameState) -> list:
        """Extract keywords from active story arcs for event selection boost."""
        keywords = []
        for arc in state.active_arcs:
            # Get current beat's keywords
            beats = arc.get("planned_beats", [])
            phase = arc.get("phase", "setup")
            theme = arc.get("theme", "")

            # Add theme as keyword
            if theme:
                keywords.extend(theme[:10].split())

            # Add current phase beat keywords
            if beats:
                # Get first unresolved beat
                for beat in beats:
                    if isinstance(beat, str):
                        keywords.extend(beat[:20].split())
                        break

        return keywords[:10]  # Limit keywords

    def make_choice(self, game_id: str, event_id: str, choice_index: int) -> dict:
        """Resolve a pending player choice and apply chosen branch effects.

        Enhanced with success/failure randomness and long-term consequences:
        1. Roll success/failure based on success_rate + attribute modifier
        2. Apply corresponding effects (success or failure)
        3. Consequence tags (affect future event triggers) — only on success
        4. Cause-effect hooks (drive future plot) — only on success
        5. NPC sentiment changes
        6. Choice history recording
        """
        state = get_state(game_id)
        if state is None:
            raise ValueError(f"Game {game_id} not found")
        if state.pending_choice is None:
            raise ValueError("No pending choice")

        ev = state.pending_choice
        if ev.get("id") != event_id:
            raise ValueError("Event ID mismatch")

        branches = ev.get("branches", [])
        if not (0 <= choice_index < len(branches)):
            raise ValueError(f"Invalid choice index: {choice_index}")

        branch = branches[choice_index]

        # 0. Roll success/failure
        is_success, final_rate = self._roll_success(branch, state)

        # 1. Apply effects based on success/failure
        if is_success:
            self.event_system.apply_effects({"effects": branch.get("effects", {})}, state)
            result_text = branch.get("result_text", "")
        else:
            self.event_system.apply_effects({"effects": branch.get("failure_effects", {})}, state)
            result_text = branch.get("failure_text", "") or branch.get("result_text", "")

        # 2. Long-term consequence tag (only on success)
        consequence_tag = ""
        if is_success:
            consequence_tag = branch.get("consequence_tag", "")
            if consequence_tag and consequence_tag not in state.tags:
                state.tags.append(consequence_tag)

        # 3. Cause-effect hook for future plot (only on success)
        if is_success:
            consequence_desc = branch.get("consequence_desc", "")
            if consequence_desc:
                self.hook_manager._create_hook(
                    state,
                    hook_id=f"choice_{event_id}_{choice_index}",
                    description=consequence_desc,
                    max_wait=80,
                )

        # 4. NPC sentiment change
        if ev.get("involved_npc_id"):
            sentiment_delta = self._calc_choice_sentiment(branch)
            if not is_success:
                sentiment_delta = max(-3, sentiment_delta - 2)  # Failure dampens sentiment
            self.npc_manager.update_relationship(
                state,
                npc_id=ev["involved_npc_id"],
                delta_sentiment=sentiment_delta,
                interaction_type="choice",
                event_text=branch.get("text", "")[:60],
            )

        # 5. Record choice history
        state.choice_history.append({
            "age": state.age,
            "event_text": ev.get("text", "")[:80],
            "choice_text": branch.get("text", ""),
            "result_text": result_text[:100],
            "consequence_tag": consequence_tag,
            "is_success": is_success,
        })

        # 6. Handle repertoire acquisition (修行积累获取)
        acquisition = branch.get("acquisition")
        if acquisition and isinstance(acquisition, dict):
            acq_name = acquisition.get("name", "")
            if acq_name:
                owned = {r["name"] for r in state.combat_repertoire}
                if acq_name not in owned:
                    state.combat_repertoire.append({
                        "name": acq_name,
                        "type": acquisition.get("type", ""),
                        "desc": str(acquisition.get("desc", ""))[:30],
                        "power": min(5, max(1, int(acquisition.get("power", 1)))),
                        "source_age": state.age,
                        "category": acquisition.get("category", "treasure"),
                    })
                    # 台账上限: 15个（超出时丢弃power最低的）
                    if len(state.combat_repertoire) > 15:
                        state.combat_repertoire.sort(key=lambda x: x.get("power", 0))
                        state.combat_repertoire = state.combat_repertoire[1:]

        # 7. Combat risk check (机缘中的斗法风险 — 触发斗法致死判定)
        combat_death_result = None
        if branch.get("combat_risk"):
            # Construct synthetic combat_factors for fortune ambush scenarios
            # Fortune combat typically involves surprise attacks while distracted by treasure
            ambush_count = _rand.choice([1, 1, 2, 2, 3])  # 40% solo, 40% pair, 20% trio
            gap = _rand.choice([-1, 0, 0, 0, 1])  # mostly same realm
            fortune_cf = {
                "enemy_realm_gap": gap,
                "enemy_count": ambush_count,
                "ally_npc_id": None,
                "enemy_npc_id": None,
                "terrain": "disadvantage",  # caught off guard during fortune event
                "special_threat": None,
            }
            combat_ev = {
                "event_type": "danger",
                "tags": ["combat", "fortune_combat_risk"],
                "effects": branch.get("effects", {}) if is_success else branch.get("failure_effects", {}),
            }
            combat_death = self.death_system.check_combat_death(state, combat_ev, fortune_cf)
            if combat_death:
                state.is_dead = True
                state.death_reason = combat_death.get("death_reason", "斗法身亡")
                combat_death_result = combat_death

        state.pending_choice = None

        # Post-year update if combat death occurred (ensure memory/NPC aging/peril are updated)
        if combat_death_result:
            self._post_year_update(state, [ev, combat_death_result])

        result = {
            "result_text": result_text,
            "event_id": event_id,
            "choice_index": choice_index,
            "choice_text": branch.get("text", ""),
            "is_success": is_success,
            "final_success_rate": final_rate,
        }
        if combat_death_result:
            result["combat_death"] = True
            result["death_reason"] = state.death_reason
        return result

    @staticmethod
    def _calc_choice_sentiment(branch: dict) -> int:
        """Calculate NPC sentiment change from a choice."""
        effects = branch.get("effects", {})
        delta = 0
        if effects.get("charisma", 0) > 0:
            delta += 3
        if effects.get("constitution", 0) < 0:
            delta -= 2  # Getting hurt may concern NPCs
        if effects.get("fortune", 0) > 0:
            delta += 2
        tag = branch.get("consequence_tag", "")
        if "仁" in tag or "义" in tag or "善" in tag:
            delta += 5
        if "贪" in tag or "残" in tag or "恶" in tag:
            delta -= 5
        return max(-10, min(10, delta))

    @staticmethod
    def _roll_success(branch: dict, state) -> tuple[bool, int]:
        """Roll success/failure for a choice branch with attribute modifier.

        Returns:
            (is_success, final_success_rate)
        """
        base_rate = branch.get("success_rate", 100)
        if base_rate >= 100:
            return True, 100  # Backward compat: old branches always succeed

        # Attribute modifier: +2% per point above 5, -2% per point below 5
        check_attr = branch.get("check_attribute", "")
        attr_bonus = 0
        if check_attr:
            attr_value = getattr(state.attributes, check_attr, 5)
            attr_bonus = (attr_value - 5) * 2

        final_rate = max(10, min(95, base_rate + attr_bonus))  # Clamp 10%-95%
        is_success = _rand.random() * 100 < final_rate
        return is_success, final_rate

    def get_life_summary(self, game_id: str) -> LifeSummary:
        """Generate end-of-life summary."""
        state = get_state(game_id)
        if state is None:
            raise ValueError(f"Game {game_id} not found")

        title_info = get_title(
            state.age, state.realm,
            is_ascended=state.is_ascended,
            death_reason=state.death_reason or "",
        )
        attrs_dict = state.attributes.model_dump()
        score = calculate_score(
            state.age, state.realm, attrs_dict,
            is_ascended=state.is_ascended,
            death_reason=state.death_reason or "",
        )

        key_events = [
            e["text"] for e in state.events_log
            if any(kw in e["text"] for kw in [
                "突破", "飞升", "传承", "大机缘", "走火入魔",
                "陨落", "渡劫", "空间节点", "困死", "化神",
            ])
        ]
        if not key_events:
            key_events = [e["text"] for e in state.events_log[-5:]]

        if state.is_ascended:
            ending = "飞升成仙"
        elif state.is_dead:
            ending = state.death_reason or "寿元耗尽"
        else:
            ending = "未知"

        return LifeSummary(
            total_age=state.age,
            max_realm=state.realm,
            max_realm_name=REALM_NAMES.get(Realm(state.realm), "未知"),
            death_reason=ending,
            key_events=key_events[:10],
            talents=state.talents,
            final_attributes=state.attributes,
            score=score,
            title=title_info["title"],
            gender=state.gender,
        )

    # ── NPC 姓名运行时注入 ─────────────────────────────────────────

    # 需要注入的 NPC 角色泛称 → 替换模式
    _NPC_ROLE_PATTERNS = {
        "道侣": ["你的道侣", "与道侣", "道侣"],
        "挚友": ["你的挚友", "与挚友", "挚友"],
        "宿敌": ["你的宿敌", "与宿敌", "宿敌"],
        "师父": ["你的师父", "与师父", "师父"],
        "同门": ["你的同门", "与同门"],  # "同门" 太短不单独替换
        "徒弟": ["你的徒弟", "与徒弟", "徒弟"],
    }

    def _inject_npc_names(self, text: str, state: GameState) -> str:
        """Replace generic NPC role references with actual NPC names.

        For each known role (道侣/挚友/宿敌), find the player's actual NPC
        of that role and replace generic mentions in the text.
        """
        if not text or not state.relationships:
            return text

        # Build role → name mapping from current relationships
        role_name_map: dict[str, str] = {}
        for rel in state.relationships:
            rtype = rel.get("relation_type", "")
            if rtype in self._NPC_ROLE_PATTERNS and rtype not in role_name_map:
                npc_id = rel.get("npc_id", "")
                npc = state.npc_registry.get(npc_id, {})
                name = npc.get("name", "")
                if name:
                    role_name_map[rtype] = name

        if not role_name_map:
            return text

        # Apply replacements (longer patterns first to avoid partial matches)
        for role, name in role_name_map.items():
            patterns = self._NPC_ROLE_PATTERNS[role]
            for pattern in patterns:
                if pattern in text:
                    if pattern.startswith("你的"):
                        text = text.replace(pattern, name)
                    elif pattern.startswith("与"):
                        text = text.replace(pattern, f"与{name}")
                    else:
                        text = text.replace(pattern, name)
        return text

    # ── Response builders ────────────────────────────────────────────

    def _build_response(self, state: GameState, events: list[dict], years_passed: int = 1, ai_used: bool = False) -> NextYearResponse:
        """Build a NextYearResponse from state and collected events."""
        # Record events in the state log
        formatted_events = []
        for ev in events:
            # NPC 姓名注入（对未走 LLM 的事件生效，走过 LLM 的已含真名）
            ev_text = self._inject_npc_names(ev.get("text", ""), state)
            ev_expanded = self._inject_npc_names(ev.get("expanded_text", ""), state)
            formatted_events.append({
                "text": ev_text,
                "expanded_text": ev_expanded,
                "type": ev.get("event_type", "normal"),
                "category": ev.get("category", "common"),
                "age": state.age,
            })
            state.events_log.append({
                "age": state.age,
                "text": ev_text,
                "category": ev.get("category", "common"),
                "event_type": ev.get("event_type", "normal"),
            })

        # Build sect info for frontend
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
                }

        # Build NPC relationships for frontend
        npc_rels = []
        for rel in state.relationships[:8]:
            npc_id = rel.get("npc_id", "")
            npc = state.npc_registry.get(npc_id, {})
            if npc:
                npc_rels.append({
                    "name": npc.get("name", "未知"),
                    "relation_type": rel.get("relation_type", ""),
                    "sentiment": rel.get("sentiment", 0),
                    "is_alive": npc.get("is_alive", True),
                })

        # Format choice_event for frontend (map event_type->type, add age)
        formatted_choice = None
        if state.pending_choice is not None:
            ce = state.pending_choice
            formatted_choice = {
                "id": ce.get("id", ""),
                "text": self._inject_npc_names(ce.get("text", ""), state),
                "expanded_text": self._inject_npc_names(ce.get("expanded_text", ""), state),
                "type": ce.get("event_type", "normal"),
                "category": ce.get("category", "common"),
                "age": state.age,
                "branches": ce.get("branches"),
            }

        return NextYearResponse(
            age=state.age,
            realm=state.realm,
            realm_name=REALM_NAMES.get(Realm(state.realm), "未知"),
            cultivation=state.cultivation,
            cultivation_max=REALM_THRESHOLDS.get(state.realm, 99999),
            events=formatted_events,
            attributes=state.attributes,
            is_dead=state.is_dead,
            death_reason=state.death_reason,
            is_ascended=state.is_ascended,
            space_node_found=state.space_node_found,
            gender=state.gender,
            years_passed=years_passed,
            has_choice=state.pending_choice is not None,
            choice_event=formatted_choice,
            tension=state.tension,
            sect_info=sect_info,
            npc_relationships=npc_rels,
            ai_enhanced=ai_used,
        )

