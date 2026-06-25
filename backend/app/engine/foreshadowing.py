"""Foreshadowing System — predictive narrative hints for LLM prompt injection.

Assembles forward-looking narrative cues from three sources:
1. Next destiny beat (骨骼前瞻): the upcoming storyline milestone
2. Active causal chains (因果预兆): unresolved threads with expected resolution
3. Active Saga direction hints (Saga暗涌): long-term narrative momentum

These hints are injected into the LLM prompt as 「伏笔暗线」, instructing
the AI to weave subtle foreshadowing into its narrative without directly
revealing future events.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import GameState


def build_foreshadowing_context(state: "GameState") -> str:
    """Assemble predictive foreshadowing hints from destiny, causal chains, and sagas.

    Returns a compact multi-line string (max 3 hints) for prompt injection.
    Returns empty string if no hints available.
    """
    hints: list[str] = []

    # ── Source A: Next destiny beat (命运暗涌) ────────────────────────────
    _add_destiny_hint(state, hints)

    # ── Source B: Unresolved causal chains (因果未了) ─────────────────────
    _add_causal_hints(state, hints)

    # ── Source C: Active Saga direction (长线隐伏) ────────────────────────
    _add_saga_hint(state, hints)

    # ── Source D: Saga omens (预兆暗涌) ─────────────────────────────────
    _add_omen_hint(state, hints)

    if not hints:
        return ""

    return "\n".join(hints[:3])  # Cap at 3 hints to avoid prompt bloat


def _add_destiny_hint(state: "GameState", hints: list[str]) -> None:
    """Extract the next unfulfilled destiny beat as a foreshadowing hint."""
    storyline = getattr(state, "main_storyline", None)
    if not storyline or storyline.get("is_completed"):
        return

    beats = storyline.get("destiny_beats", [])
    idx = storyline.get("current_beat_index", 0)

    # We want the NEXT beat (idx+1), since current beat is already being pursued
    next_idx = idx + 1
    if next_idx >= len(beats):
        return

    next_beat = beats[next_idx]
    desc = next_beat.get("description", "")
    if not desc:
        return

    # Truncate to 30 chars
    hint = f"- 命运暗涌：{desc[:30]}"
    keywords = next_beat.get("keywords", [])
    if keywords:
        hint += f"（{'/'.join(keywords[:3])}）"
    hints.append(hint)


def _add_causal_hints(state: "GameState", hints: list[str]) -> None:
    """Extract unresolved causal chains' expected resolutions as hints.

    Picks the oldest 2 unresolved chains (most overdue = most dramatic tension).
    """
    chains = getattr(state, "causal_chains", None)
    if not chains:
        return

    active = [c for c in chains if not c.get("is_resolved")]
    if not active:
        return

    # Sort by created_age ascending (oldest first = most overdue)
    active.sort(key=lambda c: c.get("created_age", 0))

    for chain in active[:2]:
        resolution = chain.get("expected_resolution", "")
        if not resolution:
            continue
        npc = chain.get("npc_name", "")
        hint = f"- 因果未了：{resolution[:30]}"
        if npc:
            hint += f"（与{npc}相关）"
        hints.append(hint)


def _add_saga_hint(state: "GameState", hints: list[str]) -> None:
    """Extract the highest-momentum active Saga's direction hint."""
    sagas = getattr(state, "sagas", None)
    if not sagas:
        return

    active = [s for s in sagas if s.get("is_active")]
    if not active:
        return

    # Pick highest momentum saga
    top_saga = max(active, key=lambda s: s.get("momentum", 0))
    direction = top_saga.get("direction_hint", "")
    if not direction:
        return

    hints.append(f"- 长线隐伏：{direction[:30]}")


def _add_omen_hint(state: "GameState", hints: list[str]) -> None:
    """Extract hints from persisted saga omens (pre-formation foreshadowing)."""
    omens = getattr(state, "saga_omens", None)
    if not omens:
        return

    # Pick the most recent omen
    latest = omens[-1]
    theme = latest.get("theme", "")
    npcs = latest.get("involved_npcs", [])
    if not theme:
        return

    hint = f"- 预兆暗涌：围绕「{theme}」的因果正在惄然汇聚"
    if npcs:
        hint += f"（似与{'、'.join(npcs[:2])}有关）"
    hints.append(hint)


def get_causal_chain_keywords(state: "GameState") -> list[str]:
    """Extract resolution keywords from active causal chains for event weight boost.

    These keywords are merged into arc_keywords to give ×2.5 boost (Layer 6)
    to events that might resolve pending causal threads.

    Returns: flat list of keywords (deduplicated, max 8).
    """
    chains = getattr(state, "causal_chains", None)
    if not chains:
        return []

    keywords: list[str] = []
    seen: set[str] = set()

    # Prioritize by urgency (higher urgency = keywords matter more)
    active = [c for c in chains if not c.get("is_resolved")]
    active.sort(key=lambda c: c.get("urgency", 1.0), reverse=True)

    for chain in active[:3]:  # Top 3 most urgent chains
        for kw in chain.get("resolution_keywords", []):
            if kw and kw not in seen:
                seen.add(kw)
                keywords.append(kw)

    return keywords[:8]  # Cap total


def build_emotional_tokens_context(state: "GameState") -> str:
    """Build prompt context for emotional tokens (随身之物).

    These are small, emotionally significant items (gifts, keepsakes, relics)
    that should be naturally referenced in narrative when contextually relevant.
    """
    tokens = getattr(state, "emotional_tokens", None)
    if not tokens:
        return ""

    lines = []
    for t in tokens[-10:]:  # Max 10 items
        name = t.get("name", "")
        desc = t.get("description", "")
        npc = t.get("source_npc", "")
        if not name:
            continue
        line = f"- {name}：{desc}"
        if npc:
            line += f"（{npc}所赠）"
        lines.append(line)

    return "\n".join(lines) if lines else ""


def build_repertoire_context(state: "GameState") -> str:
    """Build prompt context for combat repertoire (修行积累).

    Lists the player's acquired techniques and treasures so LLM can
    reference them in combat narratives.
    """
    items = getattr(state, "combat_repertoire", None)
    if not items:
        return ""

    tech_names = []
    treasure_names = []
    for item in items:
        name = item.get("name", "")
        if not name:
            continue
        if item.get("category") == "technique":
            tech_names.append(name)
        else:
            treasure_names.append(name)

    parts = []
    if tech_names:
        parts.append("\u529f\u6cd5: " + "\u3001".join(tech_names))
    if treasure_names:
        parts.append("\u6cd5\u5b9d: " + "\u3001".join(treasure_names))

    return "\n".join(parts) if parts else ""
