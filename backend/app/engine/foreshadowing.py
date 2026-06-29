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
        parts.append("功法: " + "、".join(tech_names))
    if treasure_names:
        parts.append("法宝: " + "、".join(treasure_names))

    return "\n".join(parts) if parts else ""


# ── Emotional State Context (Layer 2 + Layer 3: 情感锚点 + 背景NPC) ───────

_LONGING_THRESHOLD_YEARS = 5  # 距离上次提及超过X年则触发思念提示


def build_emotional_state_context(state: "GameState") -> str:
    """Build emotional state context for LLM prompt injection.

    Combines two sources:
    1. Emotional anchors (Layer 2): explicit emotional state tracking
       - Active emotions (longing, attachment, guilt, gratitude)
       - Decayed emotions (faded but still present)
    2. Background NPCs (Layer 3): lightweight characters with emotional bonds
       - Parents, childhood friends, village elders etc.
       - Generates "longing hints" when too long since last mention

    Output is injected as 【情感状态】 in the LLM prompt.
    """
    lines = []

    # ── Part 1: Emotional anchors ──
    anchors = getattr(state, "emotional_anchors", None) or []
    if anchors:
        # Sort by intensity (strongest first), show top 5
        active_anchors = sorted(
            anchors, key=lambda a: a.get("intensity", 0), reverse=True
        )[:5]
        for anchor in active_anchors:
            target = anchor.get("target", "")
            relation = anchor.get("relation", "")
            emotion_state = anchor.get("state", "")
            intensity = anchor.get("intensity", 5)
            if not target or not emotion_state:
                continue
            # Intensity description
            if intensity >= 8:
                strength = "强烈"
            elif intensity >= 5:
                strength = "淡淡"
            else:
                strength = "微弱"
            line = f"- 对{target}({relation})：{strength}的{emotion_state}"
            lines.append(line)

    # ── Part 2: Background NPC longing hints ──
    bg_npcs = getattr(state, "background_npcs", None) or []
    current_age = state.age
    for npc in bg_npcs:
        name = npc.get("name", "")
        relation = npc.get("relation", "")
        bond = npc.get("bond", 50)
        status = npc.get("status", "alive")
        last_mentioned = npc.get("last_mentioned_age", 0)
        if not name or status == "dead":
            continue

        years_since = current_age - last_mentioned
        # Generate longing hint based on time since last mention and bond strength
        if years_since >= _LONGING_THRESHOLD_YEARS and bond >= 40:
            if years_since >= 20:
                hint = f"- 已有{years_since}年未见{relation}{name}，心底有一块地方始终留给了这个名字"
            elif years_since >= 10:
                hint = f"- 离开{relation}{name}已{years_since}年，偶尔梦中会想起对方的脸"
            else:
                hint = f"- 近来偶尔会想起{relation}{name}"
            # Adjust based on bond intensity
            if bond >= 80:
                hint += "（情感纽带极深）"
            lines.append(hint)

        # If background NPC is "unknown" status (lost contact), add uncertainty
        if status == "unknown" and years_since >= 10:
            lines.append(f"- {relation}{name}生死未卜，心中始终放不下")

    return "\n".join(lines) if lines else "无特别情感波动"


def record_emotional_anchor(
    state: "GameState",
    target: str,
    relation: str,
    emotion_state: str,
    intensity: int = 7,
    decay_rate: str = "slow",
) -> None:
    """Record or update an emotional anchor in game state.

    If an anchor for the same target already exists, update it.
    Otherwise create a new one. Max 10 anchors.

    Args:
        state: Current game state
        target: Name of the emotional target (e.g., "父亲", "师父王青云")
        relation: Relationship type (e.g., "父亲", "师父", "童年好友")
        emotion_state: Emotional state (e.g., "思念", "依恋", "愧疚", "感恩")
        intensity: Emotional intensity 1-10
        decay_rate: "fast"/"slow"/"none" (how quickly emotion fades)
    """
    anchors = state.emotional_anchors

    # Check if anchor for same target exists
    for i, anchor in enumerate(anchors):
        if anchor.get("target") == target:
            # Update existing
            anchors[i] = {
                "target": target,
                "relation": relation,
                "state": emotion_state,
                "intensity": min(10, intensity),
                "source_age": state.age,
                "decay_rate": decay_rate,
            }
            return

    # Create new
    anchors.append({
        "target": target,
        "relation": relation,
        "state": emotion_state,
        "intensity": min(10, intensity),
        "source_age": state.age,
        "decay_rate": decay_rate,
    })

    # Cap at 10
    if len(anchors) > 10:
        # Remove lowest intensity
        anchors.sort(key=lambda a: a.get("intensity", 0))
        state.emotional_anchors = anchors[1:]  # Remove weakest


def decay_emotional_anchors(state: "GameState") -> None:
    """Apply time-based decay to emotional anchors.

    Called once per turn. Decay rates:
    - fast: -2 intensity per turn (temp emotions like anger, surprise)
    - slow: -0.5 intensity per turn (deep bonds like parental love, first love)
    - none: no decay (permanent bonds)

    Anchors dropping below intensity 1 are removed.
    """
    anchors = state.emotional_anchors
    if not anchors:
        return

    decay_map = {"fast": 2.0, "slow": 0.5, "none": 0.0}
    surviving = []
    for anchor in anchors:
        rate = decay_map.get(anchor.get("decay_rate", "slow"), 0.5)
        new_intensity = anchor.get("intensity", 5) - rate
        if new_intensity >= 1:
            anchor["intensity"] = new_intensity
            surviving.append(anchor)

    state.emotional_anchors = surviving


def register_background_npc(
    state: "GameState",
    name: str,
    relation: str,
    bond: int = 80,
    status: str = "alive",
    key_memories: list = None,
) -> None:
    """Register a lightweight background NPC for emotional tracking.

    Background NPCs don't occupy MAX_NPCS slots and don't have
    destiny beats. They exist purely for emotional continuity tracking.

    Args:
        state: Current game state
        name: NPC name (e.g., "陈父", "小花")
        relation: Relation label (e.g., "父亲", "母亲", "童年玩伴")
        bond: Emotional bond strength 0-100
        status: "alive" / "dead" / "unknown"
        key_memories: List of short memory strings
    """
    bg_npcs = state.background_npcs

    # Don't duplicate
    for existing in bg_npcs:
        if existing.get("name") == name:
            # Update instead of duplicate
            existing["bond"] = bond
            existing["status"] = status
            if key_memories:
                existing.setdefault("key_memories", []).extend(key_memories)
            return

    bg_npcs.append({
        "name": name,
        "relation": relation,
        "bond": bond,
        "status": status,
        "last_mentioned_age": state.age,
        "key_memories": key_memories or [],
    })


def update_background_npc_mention(state: "GameState", name: str) -> None:
    """Update last_mentioned_age when a background NPC is referenced in narrative.

    Called after LLM generates text that mentions a background NPC.
    """
    for npc in state.background_npcs:
        if npc.get("name") == name:
            npc["last_mentioned_age"] = state.age
            break
