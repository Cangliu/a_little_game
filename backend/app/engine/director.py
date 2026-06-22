"""Game Director — yearly advancement pipeline.

Replaces the old monolithic ``advance_year()`` with a clear 10-phase
pipeline that fixes execution-order issues and enables AI integration.
Now includes NPC system, memory management, LLM narrative, plot hooks,
event-NPC binding, and story arc planning.
"""
from ..models import GameState, NextYearResponse, LifeSummary, Realm, REALM_NAMES
from ..endings import get_title, calculate_score
from .config import REALM_THRESHOLDS, TIME_STEP_BY_REALM
from .life_phase import LifePhaseManager
from .event_system import EventSystem, _extract_narrative_age
from .realm_system import RealmSystem
from .death_system import DeathSystem
from .narrative import NarrativeProvider
from .context import GameContext
from .state import GAME_STATES, create_game, get_state
from .ai import LLMClient, PromptBuilder
from .npc import NPCManager
from .memory import MemoryManager
from .plot_hooks import PlotHookManager
from .event_npc_resolver import EventNPCResolver
from .story_arc import StoryArcPlanner
from .main_storyline import MainStorylinePlanner


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
        self.npc_manager = NPCManager()
        self.memory_manager = MemoryManager(
            llm_client=self.llm_client,
            prompt_builder=self.prompt_builder,
        )
        # Plot hooks (cause-effect chains)
        self.hook_manager = PlotHookManager()
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

    # ── Public API ───────────────────────────────────────────────────

    def start_game(self) -> GameState:
        """Create a new game and return its initial state."""
        return create_game()

    def advance_year(self, game_id: str) -> NextYearResponse:
        """Advance the game by one story beat (variable time step based on realm)."""
        state = get_state(game_id)
        if state is None:
            raise ValueError(f"Game {game_id} not found")

        if state.is_dead or state.is_ascended:
            raise ValueError("Game is already over")

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

        # Phase 4: Cultivation gain (scaled by time step)
        self.realm_system.process_cultivation(state, years=time_step)

        # Phase 5: Breakthrough foreshadow
        foreshadow = self.realm_system.check_breakthrough_foreshadow(state)
        if foreshadow:
            events.append(foreshadow)

        # Phase 6: Select and apply year events (phase-aware)
        # Get hook weight adjustments for event selection
        hook_adjustments = self.hook_manager.get_weight_adjustments(state)
        # Get story arc keywords for event selection
        arc_keywords = self._get_arc_keywords(state)
        # Get destiny keywords from main storyline (骨骼引导血肉, ×3 boost)
        destiny_keywords = self.storyline_planner.get_destiny_keywords(state)
        if destiny_keywords:
            arc_keywords = (arc_keywords or []) + destiny_keywords

        year_events = self.event_system.select_events(
            state,
            hook_adjustments=hook_adjustments if hook_adjustments else None,
            arc_keywords=arc_keywords if arc_keywords else None,
        )
        for ev in year_events:
            self.event_system.apply_effects(ev, state)
            # Record for dedup
            if ev.get("id"):
                state.used_event_ids.append(ev["id"])
            # Accumulate event duration
            event_duration = ev.get("duration", 0)
            if event_duration > 0:
                state.age += event_duration
                total_years += event_duration
                # Extra cultivation for duration-based events
                self.realm_system.process_cultivation(state, years=event_duration)
            # Resolve NPC slot (replace placeholders, bind NPC)
            self.npc_resolver.resolve_event(ev, state)
            # LLM narrative expansion (after NPC resolver so names are resolved)
            existing_expanded = ev.get("expanded_text", "")
            if not existing_expanded or len(existing_expanded) <= 50:
                ev["expanded_text"] = self.narrative.get_event_narrative(ev, state)
            # Process plot hooks (create/resolve)
            self.hook_manager.process_event(state, ev)
            # Update NPC relationship if event involves an NPC
            if ev.get("involved_npc_id"):
                self.npc_manager.update_relationship(
                    state,
                    npc_id=ev["involved_npc_id"],
                    delta_sentiment=self._calc_sentiment_delta(ev),
                    interaction_type=ev.get("category", ""),
                    event_text=ev.get("text", "")[:60],
                )
            events.append(ev)

        # Phase 6.5: NPC-driven events (recurring interactions)
        npc_events = self.npc_manager.check_npc_events(state)
        for ev in npc_events:
            events.append(ev)

        # Phase 6.6: Force-resolve expired hooks
        expiring = self.hook_manager.check_expiring_hooks(state)
        for hook in expiring:
            resolution = self.hook_manager.generate_forced_resolution(state, hook)
            if resolution:
                self.hook_manager.process_event(state, resolution)
                events.append(resolution)

        # Phase 7: Breakthrough check
        breakthrough = self.realm_system.check_breakthrough(state)
        if breakthrough:
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

        return self._build_response(state, events, total_years)

    def _post_year_update(self, state: GameState, events: list) -> None:
        """End-of-year housekeeping: memory recording, NPC aging, arc advancement, destiny advancement, context update."""
        self.memory_manager.record_events(state, events)
        self.memory_manager.tick_year(state)
        self.npc_manager.age_npcs(state)
        # Advance story arcs based on events
        for ev in events:
            self.arc_planner.advance_arc_beat(state, ev)
        # Advance main storyline + flesh-to-skeleton feedback (血肉反哺骨骼)
        self.storyline_planner.advance_destiny(state, events)
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

    # ── Response builders ────────────────────────────────────────────

    def _build_response(self, state: GameState, events: list[dict], years_passed: int = 1) -> NextYearResponse:
        """Build a NextYearResponse from state and collected events."""
        # Record events in the state log
        formatted_events = []
        for ev in events:
            formatted_events.append({
                "text": ev.get("text", ""),
                "expanded_text": ev.get("expanded_text", ""),
                "type": ev.get("event_type", "normal"),
                "category": ev.get("category", "common"),
                "age": state.age,
            })
            state.events_log.append({
                "age": state.age,
                "text": ev.get("text", ""),
            })

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
        )
