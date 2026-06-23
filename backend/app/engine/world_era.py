"""World Era System — rule-driven historical epochs of the cultivation world.

The cultivation world has its own historical progression. Players' fates are
embedded in the grand era. Pure rule-driven, zero LLM cost.

Key design:
- Era pool: ~20 predefined eras with effects on event selection
- Trigger: Age-based milestones (every 100-200 years)
- Effects: category_boost (event weight ×2), tension_mod (decay rate modifier)
- Context injection: 【天地大势】section in EventDirector prompt
"""
from __future__ import annotations

import random
import logging
import uuid
from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from ..models import GameState

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────

ERA_CHECK_INTERVAL = (80, 180)  # Years between era checks
ERA_DURATION_RANGE = (50, 200)  # Era lasts 50-200 years


# ── Data Model ──────────────────────────────────────────────────────────

class WorldEra(BaseModel):
    """A historical epoch in the cultivation world."""
    era_id: str
    name: str
    description: str
    start_age: int = 0
    duration: int = 100
    effects: dict = {}  # {category_boost: str, tension_mod: float, event_tags: [...]}
    is_active: bool = True


# ── Era Pool (predefined, randomly drawn) ──────────────────────────────

ERA_POOL = [
    {
        "name": "灵气潮汐",
        "description": "天地灵气涌动异常，修炼速度大增，但也暗藏危机",
        "effects": {"category_boost": "cultivation", "tension_mod": -2.0},
    },
    {
        "name": "宗门大战",
        "description": "各大宗门争夺资源，战火纷飞，修士命如草芥",
        "effects": {"category_boost": "social", "tension_mod": 5.0},
    },
    {
        "name": "秘境开启",
        "description": "远古秘境重现世间，无数修士前往探索，机缘与危险并存",
        "effects": {"category_boost": "fortune", "tension_mod": 3.0},
    },
    {
        "name": "天劫周期",
        "description": "天劫频繁降临，高阶修士纷纷渡劫，天地间雷鸣不断",
        "effects": {"category_boost": "danger", "tension_mod": 4.0},
    },
    {
        "name": "太平盛世",
        "description": "修仙界难得的和平时期，各方修士安心修炼，坊市繁荣",
        "effects": {"category_boost": "normal", "tension_mod": -3.0},
    },
    {
        "name": "妖兽暴动",
        "description": "深山妖兽大规模出没，威胁修士安全，各宗门联手应对",
        "effects": {"category_boost": "danger", "tension_mod": 5.0},
    },
    {
        "name": "丹道复兴",
        "description": "古老丹方重见天日，丹道修士地位大涨，各方争夺丹材",
        "effects": {"category_boost": "alchemy", "tension_mod": 0.0},
    },
    {
        "name": "魔道入侵",
        "description": "魔修势力蠢蠢欲动，正魔之争一触即发",
        "effects": {"category_boost": "danger", "tension_mod": 6.0},
    },
    {
        "name": "仙人传法",
        "description": "上界仙人降下传承，天下修士争相参悟，悟性高者获益匪浅",
        "effects": {"category_boost": "cultivation", "tension_mod": -1.0},
    },
    {
        "name": "灵脉枯竭",
        "description": "部分灵脉逐渐枯竭，修炼资源紧缺，弱肉强食更为残酷",
        "effects": {"category_boost": "social", "tension_mod": 4.0},
    },
    {
        "name": "天材地宝现世",
        "description": "稀世珍材纷纷现世，引来各方势力觊觎",
        "effects": {"category_boost": "fortune", "tension_mod": 3.0},
    },
    {
        "name": "禁术流传",
        "description": "上古禁术流入修仙界，使用者实力暴涨但代价惨重",
        "effects": {"category_boost": "danger", "tension_mod": 5.0},
    },
    {
        "name": "宗门联盟",
        "description": "数大宗门缔结联盟，共同抵御外患，修仙界格局重塑",
        "effects": {"category_boost": "social", "tension_mod": -2.0},
    },
    {
        "name": "星辰异变",
        "description": "天象异变，星辰运行偏移，占卜之术大兴，命运走向莫测",
        "effects": {"category_boost": "normal", "tension_mod": 2.0},
    },
    {
        "name": "上古遗迹",
        "description": "上古修士遗迹被发现，内有惊世传承与致命陷阱",
        "effects": {"category_boost": "fortune", "tension_mod": 4.0},
    },
    {
        "name": "天地封禁",
        "description": "一股神秘力量封锁天地，飞升之路暂断，修士人心惶惶",
        "effects": {"category_boost": "normal", "tension_mod": 3.0},
    },
    {
        "name": "百年论道",
        "description": "修仙界百年一度的论道大会来临，各路英才齐聚",
        "effects": {"category_boost": "social", "tension_mod": 1.0},
    },
    {
        "name": "瘟疫横行",
        "description": "一种怪异瘟疫蔓延修仙界，低阶修士尤为脆弱",
        "effects": {"category_boost": "danger", "tension_mod": 4.0},
    },
]


# ── WorldEraManager ──────────────────────────────────────────────────────

class WorldEraManager:
    """Manages world eras — triggers, effects, and transitions."""

    def initialize(self, state: "GameState") -> None:
        """Set the first era check age (after spiritual awakening)."""
        if state.next_era_check_age == 0:
            state.next_era_check_age = random.randint(80, 150)

    def check_era_transition(self, state: "GameState") -> Optional[dict]:
        """Check if a new era should start or the current era should end.

        Returns an era transition event dict, or None.
        """
        # End current era if expired
        if state.active_era:
            era = state.active_era
            elapsed = state.age - era.get("start_age", 0)
            duration = era.get("duration", 100)
            if elapsed >= duration:
                return self._end_era(state)

        # Check if we should trigger a new era
        if state.age >= state.next_era_check_age and state.active_era is None:
            return self._start_new_era(state)

        return None

    def _start_new_era(self, state: "GameState") -> Optional[dict]:
        """Randomly select and start a new world era."""
        # Avoid repeating recent eras
        recent_era_names = {e.get("name") for e in state.world_eras[-3:]}
        available = [e for e in ERA_POOL if e["name"] not in recent_era_names]
        if not available:
            available = ERA_POOL

        chosen = random.choice(available)
        duration = random.randint(*ERA_DURATION_RANGE)

        era = WorldEra(
            era_id=f"era_{uuid.uuid4().hex[:6]}",
            name=chosen["name"],
            description=chosen["description"],
            start_age=state.age,
            duration=duration,
            effects=chosen["effects"],
            is_active=True,
        ).model_dump()

        state.active_era = era
        state.world_eras.append(era)
        # Schedule next era check after this one ends + gap
        state.next_era_check_age = state.age + duration + random.randint(20, 80)

        logger.info("World era started: %s (duration=%d years)", chosen["name"], duration)

        # Generate notification event
        return {
            "id": f"era_start_{state.age}_{uuid.uuid4().hex[:4]}",
            "text": f"天地大势——{chosen['name']}：{chosen['description']}",
            "expanded_text": f"天地大势——{chosen['name']}：{chosen['description']}",
            "category": "common",
            "event_type": "important",
            "tags": ["world_era", "era_start"],
            "effects": {},
        }

    def _end_era(self, state: "GameState") -> Optional[dict]:
        """End the current active era."""
        era = state.active_era
        if not era:
            return None

        era_name = era.get("name", "未知纪元")
        era["is_active"] = False
        state.active_era = None

        # Schedule next era check
        state.next_era_check_age = state.age + random.randint(20, 80)

        logger.info("World era ended: %s at age %d", era_name, state.age)

        return {
            "id": f"era_end_{state.age}_{uuid.uuid4().hex[:4]}",
            "text": f"天地大势——{era_name}时期落幕，修仙界重归平静",
            "expanded_text": f"天地大势——{era_name}时期落幕，修仙界重归平静",
            "category": "common",
            "event_type": "normal",
            "tags": ["world_era", "era_end"],
            "effects": {},
        }

    def get_era_weight_adjustments(self, state: "GameState") -> dict[str, float]:
        """Get event category weight multipliers from active era.

        Returns: dict mapping category names to weight multipliers.
        """
        if not state.active_era:
            return {}

        effects = state.active_era.get("effects", {})
        category_boost = effects.get("category_boost", "")
        if not category_boost:
            return {}

        # Boost the target category ×2
        return {category_boost: 2.0}

    def get_tension_modifier(self, state: "GameState") -> float:
        """Get tension decay modifier from active era.

        Returns: float to add to tension per turn (can be negative for calm eras).
        """
        if not state.active_era:
            return 0.0

        effects = state.active_era.get("effects", {})
        return effects.get("tension_mod", 0.0)

    def get_era_context_for_ai(self, state: "GameState") -> str:
        """Build context string about active world era for AI prompts."""
        if not state.active_era:
            return ""

        era = state.active_era
        name = era.get("name", "")
        desc = era.get("description", "")
        elapsed = state.age - era.get("start_age", 0)
        duration = era.get("duration", 100)
        remaining = max(0, duration - elapsed)

        if remaining < 20:
            phase_hint = "（即将落幕）"
        elif elapsed < 20:
            phase_hint = "（方才开启）"
        else:
            phase_hint = ""

        return f"当前为「{name}」时期{phase_hint}: {desc}"
