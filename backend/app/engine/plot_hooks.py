"""Plot Hooks — cause-effect chain system for narrative coherence.

Some events "plant" a hook (e.g., "master is injured"), and later events
can "resolve" that hook (e.g., "you avenge your master"). The system
ensures hooks eventually get resolved, creating narrative arcs without
requiring LLM intervention.

Key design:
- Hooks are pure-rule based, no LLM dependency
- Each hook has a max_wait_years to force resolution
- Unresolved hooks boost the selection weight of resolving events
- Hooks can be tied to specific NPCs for continuity
"""
from __future__ import annotations

import logging
from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from ..models import GameState

logger = logging.getLogger(__name__)


class PlotHook(BaseModel):
    """A narrative thread that needs resolution."""
    hook_id: str                        # Unique identifier (e.g., "avenge_master")
    description: str                    # Human-readable description
    created_age: int                    # Player age when hook was created
    npc_id: str = ""                    # Associated NPC (if any)
    npc_name: str = ""                  # NPC name for display
    resolution_tags: list = []          # Event tags that can resolve this hook
    max_wait_years: int = 100           # Force resolution after this many years
    is_resolved: bool = False
    resolved_age: int = 0               # Age when resolved (0 = unresolved)


class PlotHookManager:
    """Manages the lifecycle of plot hooks (cause-effect chains).

    Usage in the game loop:
    1. After applying an event, call process_event() to detect new hooks
    2. Before selecting events, call get_weight_adjustments() to boost
       resolution events
    3. Call check_expiring_hooks() to find hooks nearing expiration
    """

    def process_event(self, state: "GameState", event: dict) -> None:
        """Check if an event creates or resolves a plot hook.

        Called by director after each event is applied.
        """
        # Check if event creates a hook
        creates = event.get("creates_hook")
        if creates:
            self._create_hook(
                state,
                hook_id=creates.get("id", ""),
                description=creates.get("description", ""),
                max_wait=creates.get("max_wait", 100),
                npc_id=event.get("involved_npc_id", ""),
                npc_name=event.get("involved_npc", ""),
            )

        # Check if event resolves a hook
        resolves_id = event.get("resolves_hook")
        if resolves_id:
            self._resolve_hook(state, resolves_id)

    def _create_hook(
        self,
        state: "GameState",
        hook_id: str,
        description: str,
        max_wait: int = 100,
        npc_id: str = "",
        npc_name: str = "",
    ) -> None:
        """Plant a new plot hook."""
        # Don't duplicate existing hooks
        for hook in state.plot_hooks:
            if hook.get("hook_id") == hook_id:
                logger.debug("Hook '%s' already exists, skipping", hook_id)
                return

        hook = PlotHook(
            hook_id=hook_id,
            description=description,
            created_age=state.age,
            npc_id=npc_id,
            npc_name=npc_name,
            max_wait_years=max_wait,
        ).model_dump()

        state.plot_hooks.append(hook)
        logger.debug("Created hook: %s (%s) at age %d", hook_id, description, state.age)

    def _resolve_hook(self, state: "GameState", hook_id: str) -> None:
        """Resolve an existing plot hook."""
        for i, hook in enumerate(state.plot_hooks):
            if hook.get("hook_id") == hook_id and not hook.get("is_resolved"):
                hook["is_resolved"] = True
                hook["resolved_age"] = state.age

                # Move to resolved list
                state.resolved_hooks.append(hook)
                state.plot_hooks.pop(i)

                logger.debug(
                    "Resolved hook: %s at age %d (planted at age %d)",
                    hook_id, state.age, hook.get("created_age", 0)
                )

                # Also resolve any NPC-tied unresolved hooks in relationships
                npc_id = hook.get("npc_id", "")
                if npc_id:
                    for rel in state.relationships:
                        if rel.get("npc_id") == npc_id:
                            hooks = rel.get("unresolved_hooks", [])
                            if hook_id in hooks:
                                hooks.remove(hook_id)
                            break
                return

    def get_weight_adjustments(self, state: "GameState") -> dict:
        """Calculate weight multipliers for events that resolve active hooks.

        Returns: dict mapping resolves_hook_id -> weight_multiplier
        """
        adjustments = {}
        for hook in state.plot_hooks:
            if hook.get("is_resolved"):
                continue

            hook_id = hook.get("hook_id", "")
            created_age = hook.get("created_age", 0)
            max_wait = hook.get("max_wait_years", 100)
            years_elapsed = state.age - created_age
            years_remaining = max_wait - years_elapsed

            if years_remaining <= 0:
                # Expired — maximum urgency
                adjustments[hook_id] = 10.0
            elif years_remaining < 20:
                # Nearing expiration — high priority
                adjustments[hook_id] = 5.0
            else:
                # Normal priority boost
                adjustments[hook_id] = 3.0

        return adjustments

    def check_expiring_hooks(self, state: "GameState") -> List[dict]:
        """Find hooks that are about to expire (within 10 years).

        These should be force-resolved even if no matching event exists,
        by generating a generic resolution event.
        """
        expiring = []
        for hook in state.plot_hooks:
            if hook.get("is_resolved"):
                continue
            created_age = hook.get("created_age", 0)
            max_wait = hook.get("max_wait_years", 100)
            years_elapsed = state.age - created_age

            if years_elapsed >= max_wait:
                expiring.append(hook)

        return expiring

    def generate_forced_resolution(self, state: "GameState", hook: dict) -> Optional[dict]:
        """Generate a generic resolution event for an expired hook.

        Called when a hook has exceeded its max_wait_years and no
        matching event has been selected naturally.
        """
        import uuid

        hook_id = hook.get("hook_id", "unknown")
        description = hook.get("description", "一段往事")
        npc_name = hook.get("npc_name", "")

        # Generate appropriate resolution text based on hook type
        if npc_name:
            resolution_templates = [
                f"\u591a\u5e74\u6765\u7684\u6267\u5ff5\u7ec8\u4e8e\u6709\u4e86\u7ed3\u679c\u2014\u2014{description}\u7684\u56e0\u679c\uff0c\u5728\u4e0e{npc_name}\u7684\u4e00\u6b21\u91cd\u9022\u4e2d\u5316\u89e3",
                f"\u65f6\u8fc7\u5883\u8fc1\uff0c\u5f53\u5e74{description}\u4e4b\u4e8b\u7ec8\u4e8e\u5c18\u57c3\u843d\u5b9a",
                f"\u4f60\u4e0e{npc_name}\u7684\u8fd9\u6bb5\u7f18\u5206\uff0c\u5728\u5c81\u6708\u6d41\u8f6c\u4e2d\u6e10\u6e10\u6de1\u53bb",
            ]
        else:
            resolution_templates = [
                f"\u591a\u5e74\u524d{description}\u7684\u6267\u5ff5\uff0c\u5728\u4e00\u6b21\u9759\u4fee\u4e2d\u60a0\u7136\u91ca\u6000",
                f"\u65f6\u8fc7\u5883\u8fc1\uff0c{description}\u4e00\u4e8b\u7ec8\u4e8e\u6709\u4e86\u4ea4\u4ee3",
                f"\u4f60\u5728\u60df\u604b\u4e4b\u65f6\u56de\u5fc6\u8d77{description}\uff0c\u5fc3\u4e2d\u91ca\u7136",
            ]

        import random
        resolution_text = random.choice(resolution_templates)

        event = {
            "id": f"hook_resolve_{hook_id}_{uuid.uuid4().hex[:4]}",
            "text": resolution_text,
            "expanded_text": resolution_text,
            "category": "common",
            "event_type": "important",
            "tags": ["hook_resolution"],
            "effects": {"willpower": 1},
            "resolves_hook": hook_id,
        }

        # Carry over NPC info
        if hook.get("npc_id"):
            event["involved_npc_id"] = hook["npc_id"]
            event["involved_npc"] = npc_name

        return event

    def get_hooks_context_for_ai(self, state: "GameState") -> str:
        """Build a context string about active hooks for AI prompts."""
        if not state.plot_hooks:
            return ""

        lines = ["\u672a\u4e86\u4e4b\u4e8b:"]
        for hook in state.plot_hooks:
            if hook.get("is_resolved"):
                continue
            desc = hook.get("description", "")
            npc = hook.get("npc_name", "")
            created = hook.get("created_age", 0)
            years_ago = state.age - created

            line = f"  - {desc}"
            if npc:
                line += f" (\u4e0e{npc}\u76f8\u5173)"
            line += f" [{years_ago}\u5e74\u524d\u57cb\u4e0b]"
            lines.append(line)

        return "\n".join(lines) if len(lines) > 1 else ""
