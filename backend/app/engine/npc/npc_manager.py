"""NPC Manager — generation, lifecycle, relationship graph, and NPC-driven events.

Manages persistent NPCs across a game session. NPCs can recur,
evolve relationships, age, die, and trigger their own events.
"""
from __future__ import annotations

import random
import uuid
import math
import logging
from typing import Optional

from ...models import GameState, REALM_NAMES, REALM_MAX_AGE, Realm
from .models import NPC, Relationship, RelationType, NPCPersonality, NPCInteraction
from .npc_templates import generate_name, get_backstory
from .npc_destiny import get_destiny_template, NpcDestinyGenerator

logger = logging.getLogger(__name__)

# Maximum persistent NPCs per game (avoid memory bloat)
MAX_NPCS = 80

# NPC event cooldowns (in years)
MASTER_EVENT_INTERVAL = (5, 10)
LOVER_EVENT_INTERVAL = (3, 5)
RIVAL_EVENT_INTERVAL = (10, 20)
REUNION_MIN_ABSENCE = 30
REUNION_SENTIMENT_THRESHOLD = 50

# ── NPC Personality Depth Pools ─────────────────────────────────────────

MOTIVATION_POOL = [
    "追求剑道极致", "守护宗门安宁", "寻找失散的亲人",
    "突破自身血脉诅咒", "实现师父遗愿", "追求永生不死",
    "报灭门之仇", "集齐古方炼制神丹", "探索天地大道真谛",
    "护佑一方百姓平安", "证明自己的修炼之道", "寻回前世记忆",
    "成为天下第一的炼丹师", "解开古修士留下的谜团",
]

SECRET_POOL = [
    "实为魔修后裔", "暗恋主角多年", "曾背叛过前一任师父",
    "身上封印着古魔", "真实身份是皇族血脉", "曾经误杀无辜之人",
    "拥有预见未来的能力", "寿元已所剩无几", "被一个强大的存在监视着",
    "其实是被放逐的上界仙人", "体内藏有远古传承", "心中其实早已不信任任何人",
    "", "", "",  # 30% chance of no secret
]

GROWTH_ARC_POOL = [
    "从冷漠到温情", "从正直到堕落", "从懦弱到坚强",
    "从狂傲到谦逊", "从天真到深沉", "从孤僻到开放",
    "从执着到释然", "从自私到无私", "从怯懦到无畏",
    "", "",  # 20% chance of no defined growth arc
]


class NPCManager:
    """Manages NPC entities and their relationships with the player."""

    def __init__(self, llm_client=None):
        """Initialize NPCManager with optional LLM client for dynamic destiny generation."""
        self._destiny_generator = None
        if llm_client is not None:
            self._destiny_generator = NpcDestinyGenerator(llm_client)

    def generate_npc(
        self,
        state: GameState,
        role: Optional[str] = None,
        relation_type: Optional[str] = None,
        realm: Optional[int] = None,
    ) -> Optional[NPC]:
        """Generate a new NPC and register it in the game state.

        Returns None if MAX_NPCS limit is reached.
        """
        if len(state.npc_registry) >= MAX_NPCS:
            logger.debug("NPC limit reached (%d), skipping generation", MAX_NPCS)
            return None

        # Determine NPC gender (roughly balanced)
        gender = random.choice(["male", "female"])

        # Determine realm (similar to or lower than player)
        if realm is None:
            if state.realm == 0:
                npc_realm = 0
            else:
                # NPC realm: player realm +/- 1, weighted toward same
                delta = random.choices([-1, 0, 1], weights=[20, 60, 20])[0]
                npc_realm = max(0, min(state.realm + delta, 5))
        else:
            npc_realm = realm

        # Determine personality
        personality = random.choice(list(NPCPersonality)).value

        # Role tags
        role_tags = [role] if role else []

        # Generate NPC
        npc_id = f"npc_{uuid.uuid4().hex[:8]}"
        name = generate_name(gender)
        backstory = get_backstory(role_tags, personality)

        # NPC lifespan based on realm
        npc_max_age = REALM_MAX_AGE.get(Realm(npc_realm), 80)

        # Personality depth (random combination from pools)
        motivation = random.choice(MOTIVATION_POOL)
        secret = random.choice(SECRET_POOL)
        growth_arc = random.choice(GROWTH_ARC_POOL)
        # Betrayal threshold: personalities prone to betrayal
        betrayal_threshold = -1
        if personality in ("狡诈", "暴烈", "阴沉", "狠辣", "多疑") and random.random() < 0.35:
            betrayal_threshold = random.randint(15, 30)

        npc = NPC(
            npc_id=npc_id,
            name=name,
            gender=gender,
            realm=npc_realm,
            personality=personality,
            role_tags=role_tags,
            first_met_age=state.age,
            last_seen_age=state.age,
            appearance_count=1,
            backstory=backstory,
            max_age=npc_max_age,
            motivation=motivation,
            secret=secret,
            growth_arc=growth_arc,
            betrayal_threshold=betrayal_threshold,
            age_offset=random.randint(20, 50),  # Fixed age estimation offset (set once)
        )

        # Register in state
        state.npc_registry[npc_id] = npc.model_dump()

        # Create relationship
        rel_type = relation_type or RelationType.ACQUAINTANCE.value
        initial_sentiment = self._initial_sentiment(rel_type)

        rel = Relationship(
            npc_id=npc_id,
            relation_type=rel_type,
            sentiment=initial_sentiment,
            last_interaction_age=state.age,
            interaction_count=1,
        )
        state.relationships.append(rel.model_dump())

        # Initialize destiny line for key NPCs (master/lover/rival)
        if rel_type in ("师父", "道侣", "宿敌"):
            npc_dict = state.npc_registry[npc_id]
            # Use LLM dynamic generation if available, else fall back to template
            if self._destiny_generator:
                destiny_beats = self._destiny_generator.generate_destiny(
                    npc_dict, rel_type, state
                )
            else:
                destiny_beats = get_destiny_template(rel_type)
            npc_dict["destiny_beats"] = destiny_beats
            npc_dict["current_destiny_index"] = 0
            npc_dict["destiny_completed"] = False

        logger.debug("Generated NPC: %s (%s) - %s", name, personality, rel_type)
        return npc

    def generate_fellow_disciples(
        self, state: GameState, count: int = 2
    ) -> list[NPC]:
        """Batch generate fellow disciples when player joins a sect.

        Creates 2-3 同门 NPCs at the player's realm level to provide
        multi-instance rotation for fellow-related events.
        """
        generated = []
        for _ in range(count):
            npc = self.generate_npc(
                state, role="fellow_disciple", relation_type="同门"
            )
            if npc:
                generated.append(npc)
        if generated:
            names = ", ".join(n.name for n in generated)
            logger.info("Generated %d fellow disciples: %s", len(generated), names)
        return generated

    def get_or_create_for_event(
        self, state: GameState, event: dict
    ) -> Optional[NPC]:
        """Decide whether to reuse an existing NPC or create a new one.

        Logic:
        1. If event has NPC-related tags (师父/同门), find existing NPC with matching role
        2. If high-sentiment NPC hasn't appeared in 30+ years, trigger reunion
        3. Otherwise create new NPC if limit not reached
        """
        event_tags = set(event.get("tags", []))
        event_text = event.get("text", "")

        # Check for role-specific reuse
        role_mapping = {
            "master_event": RelationType.MASTER.value,
            "fellow_event": RelationType.FELLOW.value,
            "lover_event": RelationType.LOVER.value,
            "rival_event": RelationType.RIVAL.value,
        }

        for tag, rel_type in role_mapping.items():
            if tag in event_tags or self._text_implies_role(event_text, rel_type):
                existing = self._find_npc_by_relation(state, rel_type)
                if existing:
                    self._record_appearance(state, existing.npc_id)
                    return existing

        # Check for reunion opportunity
        reunion_npc = self._check_reunion_candidate(state)
        if reunion_npc and random.random() < 0.3:
            self._record_appearance(state, reunion_npc.npc_id)
            return reunion_npc

        # Determine role for new NPC based on event context
        role = self._infer_role_from_event(event)
        rel_type = self._infer_relation_from_event(event)

        return self.generate_npc(state, role=role, relation_type=rel_type)

    def update_relationship(
        self,
        state: GameState,
        npc_id: str,
        delta_sentiment: int,
        interaction_type: str = "",
        key_memory: Optional[str] = None,
        event_text: str = "",
        consequence: str = "",
    ) -> None:
        """Update an NPC's relationship with the player.

        Records a full NPCInteraction entry in the relationship's
        interaction history, enabling cause-effect tracking.
        """
        for i, rel_dict in enumerate(state.relationships):
            if rel_dict.get("npc_id") == npc_id:
                rel_dict["sentiment"] = max(-100, min(100,
                    rel_dict.get("sentiment", 0) + delta_sentiment
                ))
                rel_dict["last_interaction_age"] = state.age
                rel_dict["interaction_count"] = rel_dict.get("interaction_count", 0) + 1
                if key_memory:
                    rel_dict["key_memory"] = key_memory

                # Record interaction in history
                interaction = NPCInteraction(
                    age=state.age,
                    event_text=(event_text or key_memory or interaction_type)[:60],
                    sentiment_delta=delta_sentiment,
                    consequence=consequence,
                    resolved=(not consequence),
                ).model_dump()

                if "interactions" not in rel_dict:
                    rel_dict["interactions"] = []
                rel_dict["interactions"].append(interaction)

                # Keep interaction history bounded (max 20 entries)
                if len(rel_dict["interactions"]) > 20:
                    rel_dict["interactions"] = rel_dict["interactions"][-20:]

                # Check for relationship evolution
                self._check_relationship_evolution(state, rel_dict, i)

                state.relationships[i] = rel_dict
                break

    def _check_relationship_evolution(self, state: GameState, rel_dict: dict, rel_index: int) -> None:
        """Check if a relationship should be upgraded or downgraded.

        Evolution rules (sentiment range: -100 ~ 100, 0=neutral):
        - 泛泛之交 → 挚友: sentiment≥60 and interaction_count≥5
        - 挚友/泛泛之交 → 道侣: sentiment≥80 and interaction_count≥8
          (only if no existing 道侣 and opposite/any gender)
        - Any non-宿敌 → 宿敌: sentiment≤-40 and interaction_count≥3
        """
        current_type = rel_dict.get("relation_type", "")
        sentiment = rel_dict.get("sentiment", 0)
        interactions = rel_dict.get("interaction_count", 0)
        npc_id = rel_dict.get("npc_id", "")
        npc_dict = state.npc_registry.get(npc_id, {})
        npc_name = npc_dict.get("name", "某人")

        new_type = None

        # Upgrade: 泛泛之交 → 挚友
        if current_type == RelationType.ACQUAINTANCE.value:
            if sentiment >= 60 and interactions >= 5:
                new_type = RelationType.FRIEND.value

        # Upgrade: 挚友/泛泛之交 → 道侣 (only if no existing 道侣)
        if current_type in (RelationType.ACQUAINTANCE.value, RelationType.FRIEND.value):
            if sentiment >= 80 and interactions >= 8:
                has_lover = any(
                    r.get("relation_type") == RelationType.LOVER.value
                    for r in state.relationships
                )
                if not has_lover:
                    new_type = RelationType.LOVER.value

        # Downgrade: 任何非宿敌 → 宿敌 (on extreme negative sentiment)
        if current_type not in (RelationType.RIVAL.value, RelationType.MASTER.value):
            if sentiment <= -40 and interactions >= 3:
                new_type = RelationType.RIVAL.value

        if new_type and new_type != current_type:
            old_type = current_type
            rel_dict["relation_type"] = new_type

            # Record the evolution as an interaction
            evolution_text = f"与{npc_name}的关系从{old_type}变为{new_type}"
            evolution_interaction = NPCInteraction(
                age=state.age,
                event_text=evolution_text[:60],
                sentiment_delta=0,
                consequence="",
                resolved=True,
            ).model_dump()

            if "interactions" not in rel_dict:
                rel_dict["interactions"] = []
            rel_dict["interactions"].append(evolution_interaction)

            logger.info(
                "Relationship evolution: %s (%s) %s → %s",
                npc_name, npc_id, old_type, new_type
            )

    def check_npc_events(self, state: GameState) -> list:
        """Check if any NPC-driven events should fire this year.

        Returns a list of event dicts generated by NPC interactions.
        """
        events = []

        for rel_dict in state.relationships:
            npc_dict = state.npc_registry.get(rel_dict.get("npc_id", ""))
            if not npc_dict or not npc_dict.get("is_alive", True):
                continue
            # Skip dispersed NPCs (e.g. sect destroyed, lost contact)
            if npc_dict.get("status") == "dispersed":
                continue

            npc_id = rel_dict["npc_id"]
            rel_type = rel_dict.get("relation_type", "")
            last_age = rel_dict.get("last_interaction_age", 0)
            years_since = state.age - last_age

            # Master teaching events
            if rel_type == RelationType.MASTER.value:
                min_interval, max_interval = MASTER_EVENT_INTERVAL
                if years_since >= random.randint(min_interval, max_interval):
                    event = self._create_master_event(state, npc_dict, rel_dict)
                    if event:
                        events.append(event)
                        self._record_appearance(state, npc_id)
                        self.update_relationship(state, npc_id, 5, "teaching")

            # Lover interaction events
            elif rel_type == RelationType.LOVER.value:
                min_interval, max_interval = LOVER_EVENT_INTERVAL
                if years_since >= random.randint(min_interval, max_interval):
                    event = self._create_lover_event(state, npc_dict, rel_dict)
                    if event:
                        events.append(event)
                        self._record_appearance(state, npc_id)
                        self.update_relationship(state, npc_id, 3, "companionship")

            # Rival confrontation events
            elif rel_type == RelationType.RIVAL.value:
                min_interval, max_interval = RIVAL_EVENT_INTERVAL
                if years_since >= random.randint(min_interval, max_interval):
                    event = self._create_rival_event(state, npc_dict, rel_dict)
                    if event:
                        events.append(event)
                        self._record_appearance(state, npc_id)
                        self.update_relationship(state, npc_id, -5, "confrontation")

            # Old friend reunion
            elif rel_dict.get("sentiment", 0) >= REUNION_SENTIMENT_THRESHOLD:
                if years_since >= REUNION_MIN_ABSENCE and random.random() < 0.15:
                    event = self._create_reunion_event(state, npc_dict, rel_dict)
                    if event:
                        events.append(event)
                        self._record_appearance(state, npc_id)
                        self.update_relationship(state, npc_id, 10, "reunion")

        # Limit to 1-2 NPC events per year to avoid overwhelming
        if len(events) > 2:
            events = random.sample(events, 2)

        return events

    def age_npcs(self, state: GameState) -> None:
        """Age all NPCs by one year. Handle death for mortals/low-realm NPCs.

        Death probability uses a sigmoid curve that ramps up gradually
        after exceeding max_age, rather than a flat 30% chance.
        """
        dead_npcs = []

        for npc_id, npc_dict in state.npc_registry.items():
            if not npc_dict.get("is_alive", True):
                continue

            # Use fixed age_offset (set at generation time) for stable estimation
            first_met = npc_dict.get("first_met_age", 0)
            age_offset = npc_dict.get("age_offset", 30)
            estimated_npc_age = state.age - first_met + age_offset

            max_age = npc_dict.get("max_age", 80)
            if estimated_npc_age > max_age:
                # Sigmoid death curve: probability ramps from ~5% at max_age
                # to ~50% at max_age+20, to ~90% at max_age+40
                years_over = estimated_npc_age - max_age
                # sigmoid: 1 / (1 + exp(-(x-20)/8)) → midpoint at 20 years over
                death_chance = 1.0 / (1.0 + math.exp(-(years_over - 20) / 8.0))
                death_chance = max(0.05, min(0.95, death_chance))
                if random.random() < death_chance:
                    npc_dict["is_alive"] = False
                    dead_npcs.append(npc_id)

            # Small chance of NPC breakthrough (realm up)
            npc_realm = npc_dict.get("realm", 0)
            if npc_realm < 5 and random.random() < 0.005:
                npc_dict["realm"] = npc_realm + 1
                npc_dict["max_age"] = REALM_MAX_AGE.get(
                    Realm(npc_dict["realm"]), max_age
                )

        # Log deaths and archive dead NPC relationships
        for npc_id in dead_npcs:
            npc_name = state.npc_registry[npc_id].get("name", "unknown")
            logger.debug("NPC %s (%s) has died", npc_name, npc_id)

        # Move dead NPC relationships out of the active list to prevent
        # unbounded growth of state.relationships over long games.
        if dead_npcs:
            dead_set = set(dead_npcs)
            surviving = []
            for rel in state.relationships:
                if rel.get("npc_id", "") in dead_set:
                    # Keep a lightweight tombstone so LLM can still reference
                    # the deceased NPC in narrative context ("故人已逝")
                    rel["is_dead"] = True
                surviving.append(rel)
            state.relationships = surviving

    def advance_npc_destiny(self, state: GameState) -> list[dict]:
        """Check and advance NPC destiny beats. Returns destiny-driven events."""
        events = []

        for rel_dict in state.relationships:
            npc_id = rel_dict.get("npc_id", "")
            npc_dict = state.npc_registry.get(npc_id)
            if not npc_dict or not npc_dict.get("is_alive", True):
                continue
            # Skip dispersed NPCs (lost contact after sect destruction etc.)
            if npc_dict.get("status") == "dispersed":
                continue

            destiny_beats = npc_dict.get("destiny_beats", [])
            if not destiny_beats or npc_dict.get("destiny_completed", False):
                continue

            idx = npc_dict.get("current_destiny_index", 0)
            if idx >= len(destiny_beats):
                npc_dict["destiny_completed"] = True
                continue

            beat = destiny_beats[idx]
            trigger = beat.get("trigger", {})

            if not self._check_destiny_trigger(state, npc_dict, rel_dict, trigger):
                continue

            # Trigger the beat
            name = npc_dict.get("name", "某人")
            event = self._create_destiny_event(state, npc_dict, rel_dict, beat, name)
            if event:
                events.append(event)
                npc_dict["current_destiny_index"] = idx + 1
                if idx + 1 >= len(destiny_beats):
                    npc_dict["destiny_completed"] = True
                self._record_appearance(state, npc_id)
                logger.info(
                    "NPC destiny beat: %s - %s (%d/%d)",
                    name, beat.get("description", ""), idx + 1, len(destiny_beats)
                )

        # Limit to 1 destiny event per turn
        if len(events) > 1:
            events = [random.choice(events)]

        return events

    @staticmethod
    def _check_destiny_trigger(
        state: GameState, npc_dict: dict, rel_dict: dict, trigger: dict
    ) -> bool:
        """Check if destiny beat trigger conditions are met."""
        first_met = npc_dict.get("first_met_age", 0)
        years_since_met = state.age - first_met

        if trigger.get("min_years_since_met") and years_since_met < trigger["min_years_since_met"]:
            return False
        if trigger.get("min_sentiment") and rel_dict.get("sentiment", 0) < trigger["min_sentiment"]:
            return False
        if trigger.get("max_sentiment") and rel_dict.get("sentiment", 0) > trigger["max_sentiment"]:
            return False
        if trigger.get("min_tension") and state.tension < trigger["min_tension"]:
            return False

        # Probability check
        prob = trigger.get("probability", 0.3)
        if random.random() > prob:
            return False

        return True

    def _create_destiny_event(
        self, state: GameState, npc_dict: dict, rel_dict: dict, beat: dict, name: str
    ) -> dict:
        """Create a game event dict from a destiny beat."""
        text = beat.get("text_template", "").replace("{name}", name)
        expanded = beat.get("expanded_template", "").replace("{name}", name)

        # Special: master beat 4 — random outcome (breakthrough or fall)
        if "{outcome}" in text:
            outcome = random.choice(["突破成功，修为大进", "力竭陨落，化道而去"])
            text = text.replace("{outcome}", outcome)
            if "陨落" in outcome:
                npc_dict["is_alive"] = False
                expanded = (
                    f"一股浩然气机从{name}闭关的洞府中冲天而起，随即消散殆尽。"
                    f"你跪倒在地，泪流满面。师父{name}，终究没能跨过那道天堑。"
                    f"但你知道，师父的道，将由你来延续。"
                )
            else:
                expanded = (
                    f"天地震荡，{name}闭关的洞府中传来龙吟虎啸之声。"
                    f"数日后，石门轰然打开，{name}踏步而出，周身灵光流转。"
                    f"「为师终于突破了。」你喜极而泣，跪地叩首。"
                )

        # Auto-detect NPC death from beat effects or text keywords
        # This ensures narrative death always syncs with state
        _DEATH_KEYWORDS = ("陨落", "身亡", "殒命", "战死", "身死", "化道", "坐化", "魂飞魄散")
        if beat.get("effects", {}).get("npc_death"):
            npc_dict["is_alive"] = False
        elif not npc_dict.get("is_alive", True):
            pass  # Already marked dead above (e.g. {outcome} path)
        else:
            combined_text = text + expanded
            if any(kw in combined_text for kw in _DEATH_KEYWORDS):
                npc_dict["is_alive"] = False

        return {
            "id": f"npc_destiny_{state.age}_{uuid.uuid4().hex[:4]}",
            "text": text,
            "expanded_text": expanded or text,
            "category": "social",
            "event_type": beat.get("event_type", "important"),
            "tags": ["npc_destiny", "npc_interaction"],
            "effects": beat.get("effects", {}),
            "involved_npc": name,
            "involved_npc_id": npc_dict.get("npc_id", ""),
        }

    def get_npc_context_string(self, state: GameState) -> str:
        """Build a string summarizing all NPC relationships for AI prompts.

        Includes personality depth fields (motivation/secret hint) for richer context.
        """
        lines = []
        for rel_dict in state.relationships:
            npc_dict = state.npc_registry.get(rel_dict.get("npc_id", ""))
            if not npc_dict:
                continue
            name = npc_dict.get("name", "???")
            alive = "在世" if npc_dict.get("is_alive", True) else "已故"
            rel_type = rel_dict.get("relation_type", "泛泛之交")
            sentiment = rel_dict.get("sentiment", 0)
            realm_name = REALM_NAMES.get(Realm(npc_dict.get("realm", 0)), "凡人")
            motivation = npc_dict.get("motivation", "")
            # Only reveal secret hint if sentiment >= 80 (close relationship)
            secret_hint = ""
            if sentiment >= 80 and npc_dict.get("secret"):
                secret_hint = f", 似乎有隱情"

            line = f"{rel_type}: {name}({realm_name}, {alive}, 好感{sentiment}"
            if motivation:
                line += f", 志向:{motivation}"
            line += f"{secret_hint})"
            lines.append(line)

        return " / ".join(lines) if lines else "暂无已知人际关系"

    def get_npc_interaction_history(self, state: GameState, npc_id: str, max_entries: int = 10) -> str:
        """Build a chronological interaction history string for a specific NPC.

        Used by the narrative system to give LLM full context about
        the player's history with this NPC.
        """
        npc_dict = state.npc_registry.get(npc_id)
        if not npc_dict:
            return ""

        name = npc_dict.get("name", "???")
        rel_dict = None
        for r in state.relationships:
            if r.get("npc_id") == npc_id:
                rel_dict = r
                break

        if not rel_dict:
            return ""

        interactions = rel_dict.get("interactions", [])
        if not interactions:
            return f"与{name}的交往尚无记录"

        # Take last max_entries
        recent = interactions[-max_entries:]
        lines = [f"与{name}({rel_dict.get('relation_type', '泛泛之交')})的交往史:"]
        for entry in recent:
            age = entry.get("age", "?")
            text = entry.get("event_text", "")[:50]
            delta = entry.get("sentiment_delta", 0)
            sign = "+" if delta > 0 else ""
            consequence = entry.get("consequence", "")
            resolved = entry.get("resolved", True)

            line = f"  {age}岁: {text}"
            if delta != 0:
                line += f" (好感{sign}{delta})"
            if consequence and not resolved:
                line += f" [未了: {consequence}]"
            lines.append(line)

        return "\n".join(lines)

    def find_故人_candidates(self, state: GameState, min_absence_years: int = 20) -> list:
        """Find NPCs that qualify as '故人' (people from the past).

        A '故人' is someone the player has met at least twice,
        hasn't seen in a long time, and is still alive.
        """
        candidates = []
        for rel_dict in state.relationships:
            npc_dict = state.npc_registry.get(rel_dict.get("npc_id", ""))
            if not npc_dict or not npc_dict.get("is_alive", True):
                continue
            if rel_dict.get("interaction_count", 0) < 2:
                continue
            years_since = state.age - rel_dict.get("last_interaction_age", 0)
            if years_since < min_absence_years:
                continue
            candidates.append({
                "npc_dict": npc_dict,
                "rel_dict": rel_dict,
                "years_absent": years_since,
                "sentiment": rel_dict.get("sentiment", 0),
            })

        # Sort by absence duration (longest first)
        candidates.sort(key=lambda x: -x["years_absent"])
        return candidates

    # ── Private helpers ───────────────────────────────────────────────

    @staticmethod
    def _initial_sentiment(relation_type: str) -> int:
        """Determine initial sentiment based on relationship type.

        Range: -100 ~ 100 (0 = neutral)
        Differentiated by intimacy level:
        - 师父/道侣: high bond (50-70)
        - 徒弟/挚友: medium bond (35-55)
        - 同门/恩人: just met, mild positive (15-35)
        - 宿敌/仇人: hostile (-70 to -40)
        - Others: neutral (0)
        """
        high_bond = {"师父", "道侣"}
        medium_bond = {"徒弟", "挚友"}
        low_bond = {"同门", "恩人"}
        negative = {"宿敌", "仇人"}
        if relation_type in high_bond:
            return random.randint(50, 70)
        elif relation_type in medium_bond:
            return random.randint(35, 55)
        elif relation_type in low_bond:
            return random.randint(15, 35)
        elif relation_type in negative:
            return random.randint(-70, -40)
        return 0

    @staticmethod
    def _text_implies_role(text: str, rel_type: str) -> bool:
        """Check if event text implies a specific relationship role."""
        role_keywords = {
            "师父": ["师父", "师尊", "传授", "指点"],
            "同门": ["同门", "师兄", "师弟", "师姐", "师妹"],
            "道侣": ["道侣", "伴侣", "相伴"],
            "宿敌": ["宿敌", "死对头", "仇家"],
        }
        keywords = role_keywords.get(rel_type, [])
        return any(kw in text for kw in keywords)

    def _find_npc_by_relation(self, state: GameState, rel_type: str) -> Optional[NPC]:
        """Find an existing alive NPC with the given relationship type."""
        for rel_dict in state.relationships:
            if rel_dict.get("relation_type") == rel_type:
                npc_dict = state.npc_registry.get(rel_dict.get("npc_id", ""))
                if npc_dict and npc_dict.get("is_alive", True):
                    return NPC(**npc_dict)
        return None

    def _check_reunion_candidate(self, state: GameState) -> Optional[NPC]:
        """Find an NPC that qualifies for a reunion event."""
        candidates = []
        for rel_dict in state.relationships:
            if rel_dict.get("sentiment", 0) < REUNION_SENTIMENT_THRESHOLD:
                continue
            years_since = state.age - rel_dict.get("last_interaction_age", 0)
            if years_since < REUNION_MIN_ABSENCE:
                continue
            npc_dict = state.npc_registry.get(rel_dict.get("npc_id", ""))
            if npc_dict and npc_dict.get("is_alive", True):
                candidates.append(NPC(**npc_dict))

        return random.choice(candidates) if candidates else None

    def _record_appearance(self, state: GameState, npc_id: str) -> None:
        """Update NPC's last_seen_age and appearance_count."""
        npc_dict = state.npc_registry.get(npc_id)
        if npc_dict:
            npc_dict["last_seen_age"] = state.age
            npc_dict["appearance_count"] = npc_dict.get("appearance_count", 0) + 1

    @staticmethod
    def _infer_role_from_event(event: dict) -> Optional[str]:
        """Infer an NPC role from event tags/category."""
        tags = set(event.get("tags", []))
        category = event.get("category", "")

        if "sword" in category or "sword_path" in tags:
            return "sword_master"
        if "alchemy" in category or "alchemy_path" in tags:
            return "alchemy_elder"
        if "social" in category:
            return "wanderer"
        return None

    @staticmethod
    def _infer_relation_from_event(event: dict) -> Optional[str]:
        """Infer relationship type from event text/tags."""
        text = event.get("text", "")
        if any(kw in text for kw in ["师父", "拜师", "传授"]):
            return RelationType.MASTER.value
        if any(kw in text for kw in ["同门", "师兄", "师弟"]):
            return RelationType.FELLOW.value
        if any(kw in text for kw in ["道侣", "心仪", "情投意合"]):
            return RelationType.LOVER.value
        if any(kw in text for kw in ["宿敌", "结仇", "死敌"]):
            return RelationType.RIVAL.value
        return RelationType.ACQUAINTANCE.value

    def _create_master_event(self, state: GameState, npc_dict: dict, rel_dict: dict) -> Optional[dict]:
        """Create a master-teaching event."""
        name = npc_dict.get("name", "师尊")
        realm_name = REALM_NAMES.get(Realm(npc_dict.get("realm", 0)), "")

        templates = [
            {
                "text": f"{name}将你唤至静室，传授了一门新的功法心得",
                "expanded": (
                    f"{name}的表情难得柔和了几分。「这门功法，为师当年悠了三十年才惟透。」"
                    f"你接过玉简，只觉入手温热，其中灵力流转如河。"
                    f"师父的毛笔字迹苍劲有力，每一笔都蔚含着多年修行的感悟。"
                ),
            },
            {
                "text": f"{name}指点你修炼中的瓶颈，令你茅塞顿开",
                "expanded": (
                    f"你困于经脉运转的难题已有数月。{name}只轻轻抬手，"
                    f"一股灵力注入你丹田，如春风过境，那堵塞的关隗瞬间豁然开朗。"
                    f"「不过是一层窗户纸而已。」师父淡然一笑，你却感激不已。"
                ),
            },
            {
                "text": f"{name}带你进入秘境历练，亲身指导战斗技巧",
                "expanded": (
                    f"秘境之中灵气浓郁得化为了雾。{name}走在前头，偶尔回头指点一二。"
                    f"「记住，实战中不要总想着用大招。灵气运转自如时，一招一式皆是杀招。」"
                    f"你一边应战秘境中的异兽，一边哀叹师父标准太高。"
                ),
            },
            {
                "text": f"{name}赐你一枚丹药，助你巩固修为根基",
                "expanded": (
                    f"一枚散发着淡金色光芒的丹药被{name}随手抛来。"
                    f"「吃了吧，最近修炼赶得太紧，根基有些浮。」师父语气淡然，"
                    f"但你知道这枚丹药的珍贵。入口化为温热灵流，经脉中每一处暗伤都被温柔修复。"
                ),
            },
            {
                "text": f"{name}讲述自身突破时的经验，对你启发良多",
                "expanded": (
                    f"夜色渐深，{name}难得打开话匣讲述当年的往事。"
                    f"「那时候为师也跟你一样，觉得这辈子突破无望了。」师父目光清澈，"
                    f"「但道心不灭，终有转机。」你默默记下每一个字。"
                ),
            },
        ]

        chosen = random.choice(templates)
        return {
            "id": f"npc_master_{state.age}_{uuid.uuid4().hex[:4]}",
            "text": chosen["text"],
            "expanded_text": chosen["expanded"],
            "category": "social",
            "event_type": "normal",
            "tags": ["master_event", "npc_interaction"],
            "effects": {"cultivation": random.randint(5, 15), "comprehension": random.choice([0, 0, 1])},
            "involved_npc": name,
            "involved_npc_id": npc_dict.get("npc_id", ""),
        }

    def _create_lover_event(self, state: GameState, npc_dict: dict, rel_dict: dict) -> Optional[dict]:
        """Create a lover interaction event."""
        name = npc_dict.get("name", "道侣")

        templates = [
            {
                "text": f"你与{name}并肩修炼，双修之下灵气运转更为顺畅",
                "expanded": (
                    f"灵气在你与{name}之间形成了奇妙的循环，一阴一阳，相互补益。"
                    f"当灵光散去，你们相视一笑——从此修行不再是一个人的事。"
                ),
            },
            {
                "text": f"{name}为你炼制了一炉辅助修炼的丹药",
                "expanded": (
                    f"丹房中药香弥漫，{name}终于从丹炉前站起，额头渗出细汗。"
                    f"「给你的，别浪费了。」语气尽管淡然，你却看见对方眼中的关切。"
                    f"三天三夜的细心的炼制，全在这一炉丹药之中。"
                ),
            },
            {
                "text": f"你与{name}携手探索了一处新发现的灵脉",
                "expanded": (
                    f"灵脉深处寒气逼人，{name}情不自禁地靠近了几分。"
                    f"你们并肩深入，在尽头发现了一汪灵泉。月光从石缝中洒落，"
                    f"映在{name}脸上，你觉得这一刻比任何机缘都珍贵。"
                ),
            },
            {
                "text": f"{name}在你闭关时默默守护，使你心无旁骛",
                "expanded": (
                    f"闭关出定时，你看见洞府外{name}静静坐在石上，周身落叶堆积。"
                    f"「醒了？」对方笑得云淡风轻，仿佛等待不过是寻常事。"
                    f"你心中一暖，知道这世间有人在等你的感觉，真好。"
                ),
            },
            {
                "text": f"月下与{name}论道，彼此心境皆有所提升",
                "expanded": (
                    f"月色如水，你与{name}在山崖边对坐。话题从功法运转聊到大道感悟，"
                    f"最后却只剩下沉默和风声。你们不需要太多言语，"
                    f"彼此心意相通就是最好的修行。"
                ),
            },
        ]

        chosen = random.choice(templates)
        return {
            "id": f"npc_lover_{state.age}_{uuid.uuid4().hex[:4]}",
            "text": chosen["text"],
            "expanded_text": chosen["expanded"],
            "category": "social",
            "event_type": "normal",
            "tags": ["lover_event", "npc_interaction"],
            "effects": {"cultivation": random.randint(3, 8), "willpower": random.choice([0, 1])},
            "involved_npc": name,
            "involved_npc_id": npc_dict.get("npc_id", ""),
        }

    def _create_rival_event(self, state: GameState, npc_dict: dict, rel_dict: dict) -> Optional[dict]:
        """Create a rival confrontation event."""
        name = npc_dict.get("name", "宿敌")

        templates = [
            {
                "text": f"{name}再次找上门来挑衅，一场激斗不可避免",
                "expanded": (
                    f"{name}的声音从云端传来：「上次的账，今天算清。」"
                    f"你拔剑而起，灵力在剑身上燃烧。既然躺不开，那便堂堂正正地一战。"
                ),
            },
            {
                "text": f"你在秘境中与{name}狭路相逢，剑拔弩张",
                "expanded": (
                    f"秘境深处，{name}的身影出现在转角。两人同时停下脚步，"
                    f"气息瞄间碰撞。「又是你。」{name}咕角上扬，「这处机缘，"
                    f"我不会让的。」"
                ),
            },
            {
                "text": f"{name}暗中使绊子，企图破坏你的修炼",
                "expanded": (
                    f"你的丹田忽然传来一阵刺痛——有人在你的修炼之地动了手脚。"
                    f"灵气中残留的气息你再熟悉不过——{name}。"
                    f"你咆哮一声站起，拳头捧紧。这笔账，早晚要算。"
                ),
            },
            {
                "text": f"听闻{name}实力大进，你暗自警醒加紧修炼",
                "expanded": (
                    f"来自各处的消息都指向同一个事实——{name}正在以惊人的速度变强。"
                    f"你心中涨起一股紧迫感。对方不会停下脚步，你也不能。"
                    f"寒夜中你将修炼时间又延长了一个时辰。"
                ),
            },
            {
                "text": f"与{name}在坊市偶遇，对方冷笑着留下挑战之约",
                "expanded": (
                    f"坊市人流如织，你却一眼认出了{name}的背影。"
                    f"对方似也感应到了你，转过身来，咕角勾起一抹冷笑。"
                    f"「三个月后，断魂崖。敢来吗？」你没有回答，但你们都知道答案。"
                ),
            },
        ]

        chosen = random.choice(templates)

        # Rival events can be dangerous or motivating
        effects = {"willpower": random.choice([0, 1, 1])}
        if random.random() < 0.3:
            effects["constitution"] = -1  # Injury from fight
        else:
            effects["cultivation"] = random.randint(2, 5)  # Motivation boost

        return {
            "id": f"npc_rival_{state.age}_{uuid.uuid4().hex[:4]}",
            "text": chosen["text"],
            "expanded_text": chosen["expanded"],
            "category": "social",
            "event_type": "danger",
            "tags": ["rival_event", "npc_interaction"],
            "effects": effects,
            "involved_npc": name,
            "involved_npc_id": npc_dict.get("npc_id", ""),
        }

    def check_destiny_pivots(self, state: GameState, events: list) -> None:
        """Check if any dramatic event should trigger NPC destiny rewrites.

        Called at end-of-year after main destiny advancement.
        """
        if not self._destiny_generator:
            return

        for event in events:
            for rel_dict in state.relationships:
                npc_id = rel_dict.get("npc_id", "")
                npc_dict = state.npc_registry.get(npc_id)
                if not npc_dict or not npc_dict.get("is_alive", True):
                    continue
                if npc_dict.get("destiny_completed", False):
                    continue
                if not npc_dict.get("destiny_beats"):
                    continue

                # Use prev_sentiment from interactions history to detect swings
                prev_sentiment = self._get_prev_sentiment(rel_dict)

                if self._destiny_generator.should_pivot(
                    npc_dict, rel_dict, event, prev_sentiment,
                    current_age=state.age,
                ):
                    success = self._destiny_generator.pivot_destiny(
                        npc_dict, rel_dict, event, state
                    )
                    if success:
                        npc_dict["_last_pivot_age"] = state.age
                        logger.info(
                            "Destiny pivoted for NPC %s due to event: %s",
                            npc_dict.get("name", "?"),
                            event.get("text", "")[:40],
                        )
                    # Only pivot once per NPC per turn
                    break

    @staticmethod
    def _get_prev_sentiment(rel_dict: dict) -> Optional[int]:
        """Get the previous sentiment value from interaction history."""
        interactions = rel_dict.get("interactions", [])
        if len(interactions) >= 2:
            # The second-to-last entry reflects the state before this turn
            prev_delta = interactions[-1].get("sentiment_delta", 0)
            current = rel_dict.get("sentiment", 0)
            return current - prev_delta
        return None

    def _create_reunion_event(self, state: GameState, npc_dict: dict, rel_dict: dict) -> Optional[dict]:
        """Create a reunion event for a long-absent friend."""
        name = npc_dict.get("name", "故人")

        templates = [
            {
                "text": f"多年未见的故人{name}突然造访，你们彻夜长谈",
                "expanded": (
                    f"山门外传来一阵熟悉的灵力波动。你推开门，{name}站在月光下，"
                    f"笑容与记忆中别无二致。「好久不见。」你们相对而坐，"
                    f"从当年往事聊到各自近况，不觉天已大亮。"
                ),
            },
            {
                "text": f"在坊市意外重逢{name}，对方变化颇大但情谊依旧",
                "expanded": (
                    f"坊市人潮中，一个熟悉的身影让你停下了脚步。{name}比当年成熟了不少，"
                    f"但看到你时眼中仍亮起了当年的光。「老朋友，喝一杯？」"
                ),
            },
            {
                "text": f"{name}寄来飞剑传书，邀你前往一叙旧情",
                "expanded": (
                    f"一柄灵剑突破禁制飞入洞府，剑身上绑着一片玉简。"
                    f"是{name}的笔迹：「多年未见，思念得紧。山南灵峰处，望一聚。」"
                    f"你咕角微微上扬，收好玉简，开始收拾行囊。"
                ),
            },
            {
                "text": f"听闻{name}在附近历练，你主动前去相会",
                "expanded": (
                    f"过路修士无意间提到了{name}的名字，你心中一动。"
                    f"新斋沐浴后，你往那个方向御剑而去。多年未见，"
                    f"不知对方还认不认得你这个老朋友。"
                ),
            },
        ]

        chosen = random.choice(templates)
        return {
            "id": f"npc_reunion_{state.age}_{uuid.uuid4().hex[:4]}",
            "text": chosen["text"],
            "expanded_text": chosen["expanded"],
            "category": "social",
            "event_type": "fortune",
            "tags": ["reunion_event", "npc_interaction"],
            "effects": {"fortune": random.choice([0, 1]), "willpower": random.choice([0, 1])},
            "involved_npc": name,
            "involved_npc_id": npc_dict.get("npc_id", ""),
        }
