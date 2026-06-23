"""Game Director — yearly advancement pipeline.

Replaces the old monolithic ``advance_year()`` with a clear 10-phase
pipeline that fixes execution-order issues and enables AI integration.
Now includes NPC system, memory management, LLM narrative, plot hooks,
event-NPC binding, and story arc planning.
"""
from typing import Generator

from ..models import GameState, NextYearResponse, LifeSummary, Realm, REALM_NAMES
from ..endings import get_title, calculate_score
from .config import REALM_THRESHOLDS, TIME_STEP_BY_REALM, TENSION_DECAY_PER_TURN, TENSION_BY_EVENT_TYPE
from .life_phase import LifePhaseManager
from .event_system import EventSystem, _extract_narrative_age, find_event_by_id
from .realm_system import RealmSystem
from .death_system import DeathSystem
from .narrative import NarrativeProvider
from .context import GameContext
from .state import GAME_STATES, create_game, get_state
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
from .choice_generator import ChoiceGenerator
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
        # Wire LLM into narrative provider (with full context access)
        self.narrative = NarrativeProvider(
            llm_client=self.llm_client,
            prompt_builder=self.prompt_builder,
            npc_manager=self.npc_manager,
            memory_manager=self.memory_manager,
            hook_manager=self.hook_manager,
            arc_planner=self.arc_planner,
        )
        # Main storyline planner (骨骼系统)
        self.storyline_planner = MainStorylinePlanner(
            llm_client=self.llm_client,
            prompt_builder=self.prompt_builder,
            npc_manager=self.npc_manager,
        )
        # Sect system (独立宗门策略系统)
        self.sect_manager = SectManager()
        # Choice generator (LLM动态选择 - 保留作为降级备用)
        self.choice_generator = ChoiceGenerator(
            llm_client=self.llm_client,
            prompt_builder=self.prompt_builder,
            npc_manager=self.npc_manager,
            hook_manager=self.hook_manager,
        )
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
        import random as _rand
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
        # Get story arc keywords for event selection
        arc_keywords = self._get_arc_keywords(state)
        # Get destiny keywords from main storyline (骨骼引导血肉, ×3 boost)
        destiny_keywords = self.storyline_planner.get_destiny_keywords(state)
        if destiny_keywords:
            arc_keywords = (arc_keywords or []) + destiny_keywords

        # Phase 6.1: Priority events (NPC/Sect) - pure rules, no LLM
        priority_events = []
        # World era transition check
        era_event = self.era_manager.check_era_transition(state)
        if era_event:
            priority_events.append(era_event)
        npc_events = self.npc_manager.check_npc_events(state)
        priority_events.extend(npc_events)
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
        # NPC destiny advancement
        destiny_events = self.npc_manager.advance_npc_destiny(state)
        priority_events.extend(destiny_events)

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
        import random as _rand
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
        arc_keywords = self._get_arc_keywords(state)
        destiny_keywords = self.storyline_planner.get_destiny_keywords(state)
        if destiny_keywords:
            arc_keywords = (arc_keywords or []) + destiny_keywords

        # Phase 6.1: Priority events
        priority_events = []
        # World era transition check
        era_event = self.era_manager.check_era_transition(state)
        if era_event:
            priority_events.append(era_event)
        npc_events = self.npc_manager.check_npc_events(state)
        priority_events.extend(npc_events)
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
        destiny_events = self.npc_manager.advance_npc_destiny(state)
        priority_events.extend(destiny_events)

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
            })

    def _post_year_update(self, state: GameState, events: list) -> None:
        """End-of-year housekeeping: memory recording, NPC aging, arc advancement, destiny advancement, tension update, context update."""
        self.memory_manager.tick_year(state)
        self.npc_manager.age_npcs(state)
        # Advance story arcs based on events + check for saga emergence
        for ev in events:
            completed_arc = self.arc_planner.advance_arc_beat(state, ev)
            if completed_arc:
                self.saga_manager.on_arc_completed(state, completed_arc)
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
        # ── Record ALL events into memory (after forced resolutions) ───
        self.memory_manager.record_events(state, events)
        # ── Tension curve update ───────────────────────────────────────
        delta = 0.0
        for ev in events:
            et = ev.get("event_type", "normal")
            delta += TENSION_BY_EVENT_TYPE.get(et, 0.0)
        # Apply world era tension modifier
        era_tension_mod = self.era_manager.get_tension_modifier(state)
        state.tension = max(0.0, min(100.0, state.tension + delta - TENSION_DECAY_PER_TURN + era_tension_mod))
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

        state.pending_choice = None

        return {
            "result_text": result_text,
            "event_id": event_id,
            "choice_index": choice_index,
            "choice_text": branch.get("text", ""),
            "is_success": is_success,
            "final_success_rate": final_rate,
        }

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
        is_success = random.random() * 100 < final_rate
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
