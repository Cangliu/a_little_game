"""Background NPC Proactive Events — LLM-driven dynamic event generation.

Gives background NPCs (parents, childhood friends, village elders) the ability
to proactively generate game events based on trigger conditions. These events
are injected as Phase 6.1 priority events, ensuring emotional continuity.

Event types:
- letter: 家书/消息 — NPC sends word, life updates
- visit: 故人来访 — NPC appears at player's cultivation location
- illness: 病重 — NPC falls seriously ill
- death: 去世 — NPC passes away
- milestone: 故人喜事 — NPC life milestone (marriage, children, etc.)
"""
from __future__ import annotations

import json
import logging
import random
import uuid
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...models import GameState
    from ..ai.llm_client import LLMClient

logger = logging.getLogger(__name__)

# ── Trigger configuration ─────────────────────────────────────────────────

# Event type → (min_bond, min_years_since_mention, base_probability, cooldown_years)
_TRIGGER_CONFIG = {
    "letter": (40, 8, 0.15, 15),
    "visit": (60, 15, 0.12, 25),
    "illness": (0, 0, 0.08, 9999),   # One-time event, special logic
    "death": (0, 0, 0.05, 9999),     # One-time event, special logic
    "milestone": (50, 12, 0.10, 20),
}

# Minimum player age for life-stage events
_ILLNESS_MIN_AGE = 30
_DEATH_MIN_AGE = 50
_DEATH_MIN_REALM = 3  # OR condition: realm≥3 means enough time has passed

# ── Fallback templates (when LLM unavailable) ─────────────────────────────

_FALLBACK_TEMPLATES = {
    "letter": [
        "一只灵鹤衔来一封家书。{relation}{name}在信中说，家中一切安好，只是偶尔想起你时会坐在门口发呆。信的末尾歪歪扭扭写着：平安就好。",
        "途经坊市时，一位行商递给你一封信。{relation}{name}托人捎来的——信纸已经泛黄，想必辗转了许久才到你手中。",
    ],
    "visit": [
        "修行之处的山门外，一个苍老但熟悉的身影正朝山上张望。你定睛一看——竟是{relation}{name}。对方见到你，浑浊的眼中瞬间亮了起来。",
        "你正在打坐，忽然感应到一股熟悉的气息。推开洞府石门，{relation}{name}正站在门外，风尘仆仆，面带微笑。",
    ],
    "illness": [
        "一封急信传来：{relation}{name}病重卧床，药石罔效。你握着信纸，手指微微发颤——修行路上走得太远，竟忘了凡人的生老病死来得如此迅疾。",
        "梦中隐约看见{relation}{name}苍白的面容。你猛然惊醒，心中莫名不安。次日便收到消息——{name}病了，而且不轻。",
    ],
    "death": [
        "那个消息还是来了。{relation}{name}走了，走得很安详。据说临终前还念叨着你的名字。你站在原地良久，忽然觉得天地间少了什么。",
        "你正在修炼时，胸口忽然一阵刺痛。莫名地，你知道{relation}{name}已经不在了。那根看不见的线，断了。",
    ],
    "milestone": [
        "偶然得到消息，{relation}{name}家中添了新丁，日子过得红火。你心中欣慰——至少你牵挂的人，在好好活着。",
        "有人带来{relation}{name}的口信：家里盖了新房，日子比从前好了许多。末了还加了一句：什么时候回来看看。",
    ],
}

# ── Effects by event type ──────────────────────────────────────────────────

_EVENT_EFFECTS = {
    "letter": {"charisma": 1},
    "visit": {"charisma": 1, "willpower": 1},
    "illness": {"willpower": 1},
    "death": {"willpower": 2},
    "milestone": {"fortune": 1},
}

_EVENT_TYPES = {
    "letter": "normal",
    "visit": "fortune",
    "illness": "important",
    "death": "important",
    "milestone": "normal",
}


class BackgroundNPCEventSystem:
    """Background NPC proactive event system — LLM-driven dynamic generation."""

    def __init__(self, llm_client: "LLMClient"):
        self.llm_client = llm_client

    def check_background_events(self, state: "GameState") -> list[dict]:
        """Check all background NPCs for trigger conditions each turn.

        Returns at most 1 event per turn to avoid overwhelming the narrative.
        """
        bg_npcs = getattr(state, "background_npcs", None) or []
        if not bg_npcs:
            return []

        triggered: list[dict] = []

        for npc in bg_npcs:
            if npc.get("status") == "dead":
                continue

            event_type = self._should_trigger(npc, state)
            if event_type:
                event = self._generate_event(npc, event_type, state)
                if event:
                    self._apply_post_effects(npc, event_type, state)
                    triggered.append(event)

        # Limit to 1 per turn
        if len(triggered) > 1:
            triggered = [random.choice(triggered)]

        return triggered

    def _should_trigger(self, npc: dict, state: "GameState") -> Optional[str]:
        """Determine if a background NPC should trigger an event.

        Returns the event type string or None.
        Priority order: death > illness > visit > letter > milestone
        """
        name = npc.get("name", "")
        bond = npc.get("bond", 50)
        status = npc.get("status", "alive")
        last_mentioned = npc.get("last_mentioned_age", 0)
        last_event_age = npc.get("last_event_age", 0)
        triggered_events = npc.get("triggered_events", [])
        years_since_mention = state.age - last_mentioned
        years_since_event = state.age - last_event_age

        # ── Death check (highest priority, one-time) ──
        if status in ("alive", "ill") and "death" not in triggered_events:
            can_die = (state.age >= _DEATH_MIN_AGE or state.realm >= _DEATH_MIN_REALM)
            # Higher chance if already ill
            death_prob = 0.12 if status == "ill" else 0.05
            if can_die and random.random() < death_prob:
                return "death"

        # ── Illness check (one-time, requires alive status) ──
        if status == "alive" and "illness" not in triggered_events:
            if state.age >= _ILLNESS_MIN_AGE and random.random() < 0.08:
                return "illness"

        # ── Regular events (cooldown-gated) ──
        for event_type in ("visit", "letter", "milestone"):
            min_bond, min_years, prob, cooldown = _TRIGGER_CONFIG[event_type]

            if bond < min_bond:
                continue
            if years_since_mention < min_years:
                continue
            if years_since_event < cooldown:
                continue
            # visit requires realm >= 1
            if event_type == "visit" and state.realm < 1:
                continue
            if random.random() < prob:
                return event_type

        return None

    def _generate_event(
        self, npc: dict, event_type: str, state: "GameState"
    ) -> Optional[dict]:
        """Generate an event using LLM or fallback templates."""
        name = npc.get("name", "")
        relation = npc.get("relation", "")

        # Try LLM generation
        narrative = self._llm_generate(npc, event_type, state)

        # Fallback to templates
        if not narrative:
            templates = _FALLBACK_TEMPLATES.get(event_type, [])
            if templates:
                narrative = random.choice(templates).format(
                    name=name, relation=relation
                )
            else:
                narrative = f"{relation}{name}的消息传来。"

        effects = _EVENT_EFFECTS.get(event_type, {})
        etype = _EVENT_TYPES.get(event_type, "normal")

        event = {
            "id": f"bg_npc_{event_type}_{state.age}_{uuid.uuid4().hex[:4]}",
            "text": f"{relation}{name}{'病重的消息传来' if event_type == 'illness' else '去世的消息传来' if event_type == 'death' else '有消息传来'}。",
            "expanded_text": narrative,
            "category": "social",
            "event_type": etype,
            "tags": ["background_npc", f"bg_{event_type}"],
            "effects": effects,
            "involved_npc": name,
        }

        return event

    def _llm_generate(
        self, npc: dict, event_type: str, state: "GameState"
    ) -> Optional[str]:
        """Call LLM to generate event narrative. Returns None on failure."""
        if not self.llm_client or not self.llm_client.available:
            return None

        from ..ai.prompt_templates import BG_NPC_EVENT_SYSTEM, BG_NPC_EVENT_USER
        from ...models import REALM_NAMES, Realm

        realm_name = REALM_NAMES.get(Realm(state.realm), "凡人")
        years_ago = state.age - npc.get("last_mentioned_age", 0)
        key_memories = "、".join(npc.get("key_memories", [])[:3]) or "无特别记忆"
        personality = npc.get("personality_hint", "朴实")

        # Event type guidance
        type_guidance = {
            "letter": "家书或口信，传递生活近况和对主角的牵挂。信的内容要有生活细节。",
            "visit": "故人意外出现在主角修行之处。重逢描写要有情感厚度和时间沉淀感。",
            "illness": "收到故人病重的消息或产生感应。要有紧迫感和牵挂，但不过度煽情。",
            "death": "故人离世。以景写情，有留白，不直接写'你很伤心'。克制但有力量。",
            "milestone": "故人生活中的喜事（成亲/添丁/新居等）。温暖、欣慰的基调。",
        }

        user_prompt = BG_NPC_EVENT_USER.format(
            event_type=event_type,
            type_guidance=type_guidance.get(event_type, ""),
            npc_relation=npc.get("relation", ""),
            npc_name=npc.get("name", "某人"),
            bond=npc.get("bond", 50),
            years_ago=years_ago,
            key_memories=key_memories,
            personality=personality,
            realm_name=realm_name,
            age=state.age,
        )

        result = self.llm_client.generate_sync(
            system_prompt=BG_NPC_EVENT_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=300,
            temperature=0.85,
        )

        if not result:
            return None

        # Parse JSON response
        try:
            text = result.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                text = text.strip()
            data = json.loads(text)
            return data.get("narrative", "")
        except (json.JSONDecodeError, AttributeError):
            # If LLM returned plain text instead of JSON, use it directly
            if len(result.strip()) > 20 and len(result.strip()) < 300:
                return result.strip()
            logger.debug("Failed to parse BG NPC event LLM response: %s...", result[:80])
            return None

    def _apply_post_effects(
        self, npc: dict, event_type: str, state: "GameState"
    ) -> None:
        """Apply post-event state changes to the background NPC."""
        from ..foreshadowing import record_emotional_anchor

        name = npc.get("name", "")
        relation = npc.get("relation", "")

        # Update mention tracking
        npc["last_mentioned_age"] = state.age
        npc["last_event_age"] = state.age

        # Record one-time events
        if event_type in ("illness", "death"):
            triggered = npc.setdefault("triggered_events", [])
            if event_type not in triggered:
                triggered.append(event_type)

        # Status transitions
        if event_type == "illness":
            npc["status"] = "ill"
            record_emotional_anchor(
                state,
                target=name,
                relation=relation,
                emotion_state="牵挂",
                intensity=8,
                decay_rate="slow",
                last_imagery="病榻上的面容",
            )
        elif event_type == "death":
            npc["status"] = "dead"
            record_emotional_anchor(
                state,
                target=name,
                relation=relation,
                emotion_state="哀恸",
                intensity=9,
                decay_rate="slow",
                last_imagery="空荡荡的旧居",
            )
        elif event_type == "visit":
            record_emotional_anchor(
                state,
                target=name,
                relation=relation,
                emotion_state="温暖",
                intensity=7,
                decay_rate="fast",
                last_imagery="重逢时的笑容",
            )
        elif event_type == "letter":
            record_emotional_anchor(
                state,
                target=name,
                relation=relation,
                emotion_state="思念",
                intensity=6,
                decay_rate="fast",
                last_imagery="泛黄的信纸",
            )
