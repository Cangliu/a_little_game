"""API routes for the cultivation life simulator."""
from fastapi import APIRouter, HTTPException
from .engine import GameDirector
from .models import Realm, REALM_NAMES

router = APIRouter(prefix="/api/game", tags=["game"])

# Single GameDirector instance shared across requests
_director = GameDirector()


@router.post("/start")
def start_game():
    """Start a new game with random attributes (simplified - pure fun)."""
    state = _director.start_game()

    return {
        "game_id": state.game_id,
        "age": state.age,
        "realm": state.realm,
        "realm_name": REALM_NAMES.get(Realm(state.realm), "凡人"),
        "gender": state.gender,
    }


@router.post("/next-year")
def next_year(data: dict):
    """Advance the game by one year."""
    game_id = data.get("game_id")
    if not game_id:
        raise HTTPException(status_code=400, detail="Missing game_id")

    try:
        result = _director.advance_year(game_id)
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/summary/{game_id}")
def get_summary(game_id: str):
    """Get life summary after game ends."""
    try:
        summary = _director.get_life_summary(game_id)
        return summary.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
