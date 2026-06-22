"""NPC Manager — generation, lifecycle, relationship graph, and NPC-driven events.

Manages persistent NPCs across a game session. NPCs can recur,
evolve relationships, age, die, and trigger their own events.
"""
from __future__ import annotations

import random
import uuid
import logging
from typing import Optional

from ...models import GameState, REALM_NAMES, REALM_MAX_AGE, Realm
from .models import NPC, Relationship, RelationType, NPCPersonality, NPCInteraction
from .npc_templates import generate_name, get_backstory
from .npc_destiny import get_destiny_template

logger = logging.getLogger(__name__)

# Maximum persistent NPCs per game (avoid memory bloat)
MAX_NPCS = 20

# NPC event cooldowns (in years)
MASTER_EVENT_INTERVAL = (5, 10)
LOVER_EVENT_INTERVAL = (3, 5)
RIVAL_EVENT_INTERVAL = (10, 20)
REUNION_MIN_ABSENCE = 30
REUNION_SENTIMENT_THRESHOLD = 70


class NPCManager:
    """Manages NPC entities and their relationships with the player."""

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
        if rel_type in ("\u5e08\u7236", "\u9053\u4fa3", "\u5bbf\u654c"):
            destiny_beats = get_destiny_template(rel_type)
            npc_dict = state.npc_registry[npc_id]
            npc_dict["destiny_beats"] = destiny_beats
            npc_dict["current_destiny_index"] = 0
            npc_dict["destiny_completed"] = False

        logger.debug("Generated NPC: %s (%s) - %s", name, personality, rel_type)
        return npc

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
                rel_dict["sentiment"] = max(0, min(100,
                    rel_dict.get("sentiment", 50) + delta_sentiment
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

        Evolution rules:
        - 泛泛之交 → 挚友: sentiment≥80 and interaction_count≥5
        - 挚友/泛泛之交 → 道侣: sentiment≥90 and interaction_count≥8
          (only if no existing 道侣 and opposite/any gender)
        - Any non-宿敌 → 宿敌: sentiment≤20 and interaction_count≥3
        """
        current_type = rel_dict.get("relation_type", "")
        sentiment = rel_dict.get("sentiment", 50)
        interactions = rel_dict.get("interaction_count", 0)
        npc_id = rel_dict.get("npc_id", "")
        npc_dict = state.npc_registry.get(npc_id, {})
        npc_name = npc_dict.get("name", "某人")

        new_type = None

        # Upgrade: 泛泛之交 → 挚友
        if current_type == RelationType.ACQUAINTANCE.value:
            if sentiment >= 80 and interactions >= 5:
                new_type = RelationType.FRIEND.value

        # Upgrade: 挚友/泛泛之交 → 道侣 (only if no existing 道侣)
        if current_type in (RelationType.ACQUAINTANCE.value, RelationType.FRIEND.value):
            if sentiment >= 90 and interactions >= 8:
                has_lover = any(
                    r.get("relation_type") == RelationType.LOVER.value
                    for r in state.relationships
                )
                if not has_lover:
                    new_type = RelationType.LOVER.value

        # Downgrade: 任何非宿敌 → 宿敌 (on extreme negative sentiment)
        if current_type not in (RelationType.RIVAL.value, RelationType.MASTER.value):
            if sentiment <= 20 and interactions >= 3:
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
            elif rel_dict.get("sentiment", 50) >= REUNION_SENTIMENT_THRESHOLD:
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
        """Age all NPCs by one year. Handle death for mortals/low-realm NPCs."""
        dead_npcs = []

        for npc_id, npc_dict in state.npc_registry.items():
            if not npc_dict.get("is_alive", True):
                continue

            # Simplified NPC aging: estimate their current age
            first_met = npc_dict.get("first_met_age", 0)
            # Assume NPC was a similar age when first met (rough estimation)
            estimated_npc_age = state.age - first_met + random.randint(20, 50)

            max_age = npc_dict.get("max_age", 80)
            if estimated_npc_age > max_age:
                # NPC dies of old age
                if random.random() < 0.3:  # 30% chance per year past max age
                    npc_dict["is_alive"] = False
                    dead_npcs.append(npc_id)

            # Small chance of NPC breakthrough (realm up)
            npc_realm = npc_dict.get("realm", 0)
            if npc_realm < 5 and random.random() < 0.005:
                npc_dict["realm"] = npc_realm + 1
                npc_dict["max_age"] = REALM_MAX_AGE.get(
                    Realm(npc_dict["realm"]), max_age
                )

        # Log deaths
        for npc_id in dead_npcs:
            npc_name = state.npc_registry[npc_id].get("name", "unknown")
            logger.debug("NPC %s (%s) has died", npc_name, npc_id)

    def advance_npc_destiny(self, state: GameState) -> list[dict]:
        """Check and advance NPC destiny beats. Returns destiny-driven events."""
        events = []

        for rel_dict in state.relationships:
            npc_id = rel_dict.get("npc_id", "")
            npc_dict = state.npc_registry.get(npc_id)
            if not npc_dict or not npc_dict.get("is_alive", True):
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
            name = npc_dict.get("name", "\u67d0\u4eba")
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
        if trigger.get("min_sentiment") and rel_dict.get("sentiment", 50) < trigger["min_sentiment"]:
            return False
        if trigger.get("max_sentiment") and rel_dict.get("sentiment", 50) > trigger["max_sentiment"]:
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
            outcome = random.choice(["\u7a81\u7834\u6210\u529f\uff0c\u4fee\u4e3a\u5927\u8fdb", "\u529b\u7aed\u965e\u843d\uff0c\u5316\u9053\u800c\u53bb"])
            text = text.replace("{outcome}", outcome)
            if "\u965e\u843d" in outcome:
                npc_dict["is_alive"] = False
                expanded = (
                    f"\u4e00\u80a1\u6d69\u7136\u6c14\u673a\u4ece{name}\u95ed\u5173\u7684\u6d1e\u5e9c\u4e2d\u51b2\u5929\u800c\u8d77\uff0c\u968f\u5373\u6d88\u6563\u6b86\u5c3d\u3002"
                    f"\u4f60\u8dea\u5012\u5728\u5730\uff0c\u6cea\u6d41\u6ee1\u9762\u3002\u5e08\u7236{name}\uff0c\u7ec8\u7a76\u6ca1\u80fd\u8de8\u8fc7\u90a3\u9053\u5929\u5811\u3002"
                    f"\u4f46\u4f60\u77e5\u9053\uff0c\u5e08\u7236\u7684\u9053\uff0c\u5c06\u7531\u4f60\u6765\u5ef6\u7eed\u3002"
                )
            else:
                expanded = (
                    f"\u5929\u5730\u9707\u8361\uff0c{name}\u95ed\u5173\u7684\u6d1e\u5e9c\u4e2d\u4f20\u6765\u9f99\u541f\u864e\u5578\u4e4b\u58f0\u3002"
                    f"\u6570\u65e5\u540e\uff0c\u77f3\u95e8\u8f70\u7136\u6253\u5f00\uff0c{name}\u8e0f\u6b65\u800c\u51fa\uff0c\u5468\u8eab\u7075\u5149\u6d41\u8f6c\u3002"
                    f"\u300c\u4e3a\u5e08\u7ec8\u4e8e\u7a81\u7834\u4e86\u3002\u300d\u4f60\u559c\u6781\u800c\u6ce3\uff0c\u8dea\u5730\u53e9\u9996\u3002"
                )

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
        """Build a string summarizing all NPC relationships for AI prompts."""
        lines = []
        for rel_dict in state.relationships:
            npc_dict = state.npc_registry.get(rel_dict.get("npc_id", ""))
            if not npc_dict:
                continue
            name = npc_dict.get("name", "???")
            alive = "在世" if npc_dict.get("is_alive", True) else "已故"
            rel_type = rel_dict.get("relation_type", "泛泛之交")
            sentiment = rel_dict.get("sentiment", 50)
            realm_name = REALM_NAMES.get(Realm(npc_dict.get("realm", 0)), "凡人")
            lines.append(f"{rel_type}: {name}({realm_name}, {alive}, 好感{sentiment})")

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
                "sentiment": rel_dict.get("sentiment", 50),
            })

        # Sort by absence duration (longest first)
        candidates.sort(key=lambda x: -x["years_absent"])
        return candidates

    # ── Private helpers ───────────────────────────────────────────────

    @staticmethod
    def _initial_sentiment(relation_type: str) -> int:
        """Determine initial sentiment based on relationship type."""
        positive = {"师父", "徒弟", "同门", "挚友", "道侣", "恩人"}
        negative = {"宿敌", "仇人"}
        if relation_type in positive:
            return random.randint(60, 80)
        elif relation_type in negative:
            return random.randint(10, 30)
        return 50

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
            if rel_dict.get("sentiment", 50) < REUNION_SENTIMENT_THRESHOLD:
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
            f"{name}将你唤至静室，传授了一门新的功法心得",
            f"{name}指点你修炼中的瓶颈，令你茅塞顿开",
            f"{name}带你进入秘境历练，亲身指导战斗技巧",
            f"{name}赐你一枚丹药，助你巩固修为根基",
            f"{name}讲述自身突破时的经验，对你启发良多",
        ]

        return {
            "id": f"npc_master_{state.age}_{uuid.uuid4().hex[:4]}",
            "text": random.choice(templates),
            "expanded_text": random.choice(templates),
            "category": "social",
            "event_type": "normal",
            "tags": ["master_event", "npc_interaction"],
            "effects": {"cultivation": random.randint(5, 15), "comprehension": random.choice([0, 0, 1])},
            "involved_npc": name,
        }

    def _create_lover_event(self, state: GameState, npc_dict: dict, rel_dict: dict) -> Optional[dict]:
        """Create a lover interaction event."""
        name = npc_dict.get("name", "道侣")

        templates = [
            f"你与{name}并肩修炼，双修之下灵气运转更为顺畅",
            f"{name}为你炼制了一炉辅助修炼的丹药",
            f"你与{name}携手探索了一处新发现的灵脉",
            f"{name}在你闭关时默默守护，使你心无旁骛",
            f"月下与{name}论道，彼此心境皆有所提升",
        ]

        return {
            "id": f"npc_lover_{state.age}_{uuid.uuid4().hex[:4]}",
            "text": random.choice(templates),
            "expanded_text": random.choice(templates),
            "category": "social",
            "event_type": "normal",
            "tags": ["lover_event", "npc_interaction"],
            "effects": {"cultivation": random.randint(3, 8), "willpower": random.choice([0, 1])},
            "involved_npc": name,
        }

    def _create_rival_event(self, state: GameState, npc_dict: dict, rel_dict: dict) -> Optional[dict]:
        """Create a rival confrontation event."""
        name = npc_dict.get("name", "宿敌")

        templates = [
            f"{name}再次找上门来挑衅，一场激斗不可避免",
            f"你在秘境中与{name}狭路相逢，剑拔弩张",
            f"{name}暗中使绊子，企图破坏你的修炼",
            f"听闻{name}实力大进，你暗自警醒加紧修炼",
            f"与{name}在坊市偶遇，对方冷笑着留下挑战之约",
        ]

        # Rival events can be dangerous or motivating
        effects = {"willpower": random.choice([0, 1, 1])}
        if random.random() < 0.3:
            effects["constitution"] = -1  # Injury from fight
        else:
            effects["cultivation"] = random.randint(2, 5)  # Motivation boost

        return {
            "id": f"npc_rival_{state.age}_{uuid.uuid4().hex[:4]}",
            "text": random.choice(templates),
            "expanded_text": random.choice(templates),
            "category": "social",
            "event_type": "danger",
            "tags": ["rival_event", "npc_interaction"],
            "effects": effects,
            "involved_npc": name,
        }

    def _create_reunion_event(self, state: GameState, npc_dict: dict, rel_dict: dict) -> Optional[dict]:
        """Create a reunion event for a long-absent friend."""
        name = npc_dict.get("name", "故人")
        rel_type = rel_dict.get("relation_type", "故人")

        templates = [
            f"多年未见的{rel_type}{name}突然造访，你们彻夜长谈",
            f"在坊市意外重逢{name}，对方变化颇大但情谊依旧",
            f"{name}寄来飞剑传书，邀你前往一叙旧情",
            f"听闻{name}在附近历练，你主动前去相会",
        ]

        return {
            "id": f"npc_reunion_{state.age}_{uuid.uuid4().hex[:4]}",
            "text": random.choice(templates),
            "expanded_text": random.choice(templates),
            "category": "social",
            "event_type": "fortune",
            "tags": ["reunion_event", "npc_interaction"],
            "effects": {"fortune": random.choice([0, 1]), "willpower": random.choice([0, 1])},
            "involved_npc": name,
        }
