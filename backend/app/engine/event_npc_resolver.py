"""Event NPC Resolver — runtime placeholder replacement and NPC slot binding.

At runtime, when an event with npc_slot is selected:
1. Find or create the appropriate NPC for that slot
2. Replace {master}/{rival}/{lover}/etc. placeholders with actual NPC name
3. Track which NPC is involved for memory and narrative systems

Design principle: Same slot maps to the same NPC throughout a game session.
e.g., all "master" events always reference the same master NPC until that NPC dies.
"""
from __future__ import annotations

import re
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import GameState
    from .npc.npc_manager import NPCManager
    from .npc.models import NPC

logger = logging.getLogger(__name__)

# Mapping from npc_slot values to RelationType values
SLOT_TO_RELATION = {
    "master": "师父",
    "lover": "道侣",
    "rival": "宿敌",
    "fellow": "同门",
    "friend": "挚友",
    "elder": "泛泛之交",  # Elders start as acquaintances
    "any_known": None,  # Will pick from existing NPCs
}

# Placeholder patterns in event text
SLOT_PLACEHOLDERS = {
    "master": "{master}",
    "lover": "{lover}",
    "rival": "{rival}",
    "fellow": "{fellow}",
    "friend": "{friend}",
    "elder": "{elder}",
    "any_known": "{known_npc}",
}

# Fallback display names when no NPC exists yet
SLOT_FALLBACK_NAMES = {
    "master": "师父",
    "lover": "道侣",
    "rival": "宿敌",
    "fellow": "同门",
    "friend": "好友",
    "elder": "一位前辈",
    "any_known": "一位故人",
}


class EventNPCResolver:
    """Resolves NPC slots in events to actual NPC entities at runtime."""

    def __init__(self, npc_manager: "NPCManager"):
        self._npc_manager = npc_manager

    def resolve_event(self, event: dict, state: "GameState") -> dict:
        """Resolve NPC slot for an event, binding it to an actual NPC.

        Modifies the event dict in-place:
        - Replaces placeholder text with NPC name
        - Sets 'involved_npc' field with NPC name
        - Sets 'involved_npc_id' field with NPC ID

        Returns the modified event.
        """
        npc_slot = event.get("npc_slot")
        if not npc_slot:
            return event

        # Find or create appropriate NPC for this slot
        npc = self._get_npc_for_slot(state, npc_slot, event)

        if npc:
            npc_name = npc.name if hasattr(npc, 'name') else npc.get("name", "")
            npc_id = npc.npc_id if hasattr(npc, 'npc_id') else npc.get("npc_id", "")

            # Replace placeholders in text fields
            event["text"] = self._replace_placeholders(event.get("text", ""), npc_slot, npc_name)
            if event.get("expanded_text"):
                event["expanded_text"] = self._replace_placeholders(
                    event["expanded_text"], npc_slot, npc_name
                )

            # Set NPC tracking fields
            event["involved_npc"] = npc_name
            event["involved_npc_id"] = npc_id

            logger.debug("Resolved slot '%s' -> NPC '%s' (%s)", npc_slot, npc_name, npc_id)
        else:
            # No NPC available — use fallback name
            fallback = SLOT_FALLBACK_NAMES.get(npc_slot, "某人")
            event["text"] = self._replace_placeholders(event.get("text", ""), npc_slot, fallback)
            if event.get("expanded_text"):
                event["expanded_text"] = self._replace_placeholders(
                    event["expanded_text"], npc_slot, fallback
                )

        # Safety sweep: catch any unreplaced placeholders in all text fields
        self._sanitize_placeholders(event)

        return event

    @staticmethod
    def _sanitize_placeholders(event: dict) -> None:
        """Final safety sweep — replace any remaining {slot} placeholders with generic names."""
        pattern = re.compile(r'\{(master|lover|rival|fellow|friend|elder|known_npc)\}')
        for field in ("text", "expanded_text"):
            val = event.get(field, "")
            if val and pattern.search(val):
                event[field] = pattern.sub("某人", val)

    def _get_npc_for_slot(self, state: "GameState", slot: str, event: dict) -> Optional["NPC"]:
        """Find or create the appropriate NPC for a given slot.

        Core logic:
        - For specific roles (master/lover/rival/fellow): reuse existing NPC
          with that relation, or create new one if none exists.
        - For 'any_known': pick the best "故人" candidate (longest absent,
          positive sentiment, alive).
        - For 'elder': create a new NPC or reuse an existing acquaintance.
        """
        if slot == "any_known":
            return self._resolve_any_known(state)
        elif slot == "elder":
            return self._resolve_elder(state)
        else:
            return self._resolve_specific_role(state, slot, event)

    def _resolve_specific_role(self, state: "GameState", slot: str, event: dict) -> Optional["NPC"]:
        """Resolve a specific role slot (master/lover/rival/fellow/friend)."""
        from .npc.models import NPC

        rel_type = SLOT_TO_RELATION.get(slot)
        if not rel_type:
            return None

        # Try to find existing alive NPC with this relation
        for rel_dict in state.relationships:
            if rel_dict.get("relation_type") == rel_type:
                npc_dict = state.npc_registry.get(rel_dict.get("npc_id", ""))
                if npc_dict and npc_dict.get("is_alive", True):
                    # Record appearance
                    self._npc_manager._record_appearance(state, npc_dict.get("npc_id", rel_dict["npc_id"]))
                    return NPC(**npc_dict)

        # No existing NPC for this role — create one
        role = self._slot_to_role_tag(slot)
        npc = self._npc_manager.generate_npc(
            state, role=role, relation_type=rel_type
        )
        return npc

    def _resolve_any_known(self, state: "GameState") -> Optional["NPC"]:
        """Resolve 'any_known' slot — pick the best '故人' candidate.

        Priority: longest absent + positive sentiment + alive.
        """
        from .npc.models import NPC

        candidates = []
        for rel_dict in state.relationships:
            npc_dict = state.npc_registry.get(rel_dict.get("npc_id", ""))
            if not npc_dict or not npc_dict.get("is_alive", True):
                continue

            # Must have interacted at least once before
            if rel_dict.get("interaction_count", 0) < 1:
                continue

            years_since = state.age - rel_dict.get("last_interaction_age", 0)
            sentiment = rel_dict.get("sentiment", 0)

            # Score: prefer long-absent + positive sentiment
            score = years_since * 0.5 + sentiment * 0.3
            candidates.append((score, npc_dict, rel_dict))

        if not candidates:
            # No known NPCs — create a new acquaintance
            npc = self._npc_manager.generate_npc(state, relation_type="泛泛之交")
            return npc

        # Pick top candidate
        candidates.sort(key=lambda x: -x[0])
        best_npc_dict = candidates[0][1]
        self._npc_manager._record_appearance(state, best_npc_dict.get("npc_id", ""))
        return NPC(**best_npc_dict)

    def _resolve_elder(self, state: "GameState") -> Optional["NPC"]:
        """Resolve 'elder' slot — higher-realm NPC, can be new or existing."""
        from .npc.models import NPC
        import random

        # 40% chance to reuse existing higher-realm acquaintance
        if random.random() < 0.4:
            for rel_dict in state.relationships:
                npc_dict = state.npc_registry.get(rel_dict.get("npc_id", ""))
                if not npc_dict or not npc_dict.get("is_alive", True):
                    continue
                # Elder must be higher realm
                if npc_dict.get("realm", 0) > state.realm:
                    self._npc_manager._record_appearance(state, npc_dict.get("npc_id", ""))
                    return NPC(**npc_dict)

        # Create new elder NPC (realm = player+1, up to 5)
        elder_realm = min(state.realm + 1, 5)
        npc = self._npc_manager.generate_npc(
            state, role="elder", relation_type="泛泛之交", realm=elder_realm
        )
        return npc

    @staticmethod
    def _replace_placeholders(text: str, slot: str, npc_name: str) -> str:
        """Replace all slot placeholders in text with the NPC name.

        Also replaces ALL other known placeholders with the same name
        as a safety measure (some events might use multiple placeholder types).
        """
        # Replace the primary slot placeholder
        placeholder = SLOT_PLACEHOLDERS.get(slot, "")
        if placeholder and placeholder in text:
            text = text.replace(placeholder, npc_name)
        # Also replace any other known placeholders that remain
        for other_slot, other_ph in SLOT_PLACEHOLDERS.items():
            if other_slot != slot and other_ph in text:
                text = text.replace(other_ph, npc_name)
        return text

    @staticmethod
    def _slot_to_role_tag(slot: str) -> str:
        """Convert slot name to NPC role tag."""
        role_map = {
            "master": "sword_master",
            "lover": "companion",
            "rival": "antagonist",
            "fellow": "fellow_disciple",
            "friend": "wanderer",
        }
        return role_map.get(slot, "wanderer")
