"""Game state management — in-memory store, creation, retrieval."""
import random
import uuid
from typing import Optional

from ..models import GameState, Attributes


# ── In-memory game state store ────────────────────────────────────────────
GAME_STATES: dict[str, GameState] = {}

# Anti-streak gender history (module-level, tracks recent gender picks)
_gender_history: list[str] = []


def _pick_gender() -> str:
    """Pick gender with anti-streak bias.

    Pure 50/50 when no streak; after 2+ consecutive same gender,
    progressively favor the other to avoid frustrating runs.
    """
    streak = 0
    if _gender_history:
        last = _gender_history[-1]
        for g in reversed(_gender_history):
            if g == last:
                streak += 1
            else:
                break

    if streak >= 3:
        gender = _gender_history[-1]
        opposite = "female" if gender == "male" else "male"
        pick = random.choices([opposite, gender], weights=[80, 20])[0]
    elif streak >= 2:
        gender = _gender_history[-1]
        opposite = "female" if gender == "male" else "male"
        pick = random.choices([opposite, gender], weights=[65, 35])[0]
    else:
        pick = random.choice(["male", "female"])

    _gender_history.append(pick)
    if len(_gender_history) > 10:
        _gender_history.pop(0)
    return pick


def create_game() -> GameState:
    """Create a new game with random attributes."""
    game_id = str(uuid.uuid4())[:8]
    gender = _pick_gender()

    attributes = Attributes(
        lifespan=random.randint(2, 6),
        constitution=random.randint(2, 6),
        comprehension=random.randint(2, 6),
        fortune=random.randint(2, 6),
        charisma=random.randint(2, 6),
        willpower=random.randint(2, 6),
    )

    state = GameState(
        game_id=game_id,
        age=0,
        realm=0,
        cultivation=0,
        gender=gender,
        attributes=attributes,
        talents=[],
        tags=[],
        events_log=[],
        mortal_max_age=random.randint(50, 80),
        is_dead=False,
        is_ascended=False,
        tribulation_attempted=False,
        space_node_found=False,
        life_phase=0,
        breakthrough_failures={},
    )

    GAME_STATES[game_id] = state
    return state


def get_state(game_id: str) -> Optional[GameState]:
    """Retrieve a game state by ID, or None if not found."""
    return GAME_STATES.get(game_id)
