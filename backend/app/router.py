"""API routes for the cultivation life simulator."""
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from .engine import GameDirector
from .models import Realm, REALM_NAMES, ChoiceRequest
from .engine.state import get_state

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


@router.post("/next-year-stream")
def next_year_stream(data: dict):
    """Streaming variant: SSE for real-time narrative."""
    game_id = data.get("game_id")
    if not game_id:
        raise HTTPException(status_code=400, detail="Missing game_id")

    def event_generator():
        try:
            for event in _director.advance_year_stream(game_id):
                event_type = event["event"]
                event_data = event["data"]
                yield f"event: {event_type}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"
        except ValueError as e:
            yield f"event: error\ndata: {json.dumps({'detail': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/summary/{game_id}")
def get_summary(game_id: str):
    """Get life summary after game ends."""
    try:
        summary = _director.get_life_summary(game_id)
        return summary.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/choose")
def choose(req: ChoiceRequest):
    """Make a choice for a pending branch event."""
    try:
        result = _director.make_choice(req.game_id, req.event_id, req.choice_index)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/state/{game_id}")
def get_game_state(game_id: str):
    """Get full game state (NPC/sect/choice history)."""
    state = get_state(game_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

    sect_info = None
    if state.sect_membership:
        mem = state.sect_membership
        sects = state.sect_world.get("sects", {})
        sect = sects.get(mem.get("sect_id", ""), {})
        if sect:
            sect_info = {
                "name": sect.get("name", ""),
                "rank": mem.get("rank", ""),
                "contribution": mem.get("contribution", 0),
                "sect_type": sect.get("sect_type", ""),
                "reputation_in_sect": mem.get("reputation_in_sect", 50),
                "missions_completed": mem.get("missions_completed", 0),
            }

    npc_rels = []
    for rel in state.relationships[:10]:
        npc_id = rel.get("npc_id", "")
        npc = state.npc_registry.get(npc_id, {})
        if npc:
            npc_rels.append({
                "name": npc.get("name", "\u672a\u77e5"),
                "relation_type": rel.get("relation_type", ""),
                "sentiment": rel.get("sentiment", 50),
                "is_alive": npc.get("is_alive", True),
            })

    return {
        "game_id": game_id,
        "age": state.age,
        "realm": state.realm,
        "tension": state.tension,
        "sect_info": sect_info,
        "npc_relationships": npc_rels,
        "choice_history": state.choice_history[-20:],
    }


@router.get("/sect-world/{game_id}")
def get_sect_world(game_id: str):
    """Get sect world information (sect list + relations)."""
    state = get_state(game_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

    sects = state.sect_world.get("sects", {})
    relations = state.sect_world.get("relations", [])

    active_sects = [
        {
            "sect_id": s.get("sect_id"),
            "name": s.get("name"),
            "sect_type": s.get("sect_type"),
            "tier": s.get("tier"),
            "reputation": s.get("reputation"),
            "disciples_count": s.get("disciples_count"),
            "sect_master_name": s.get("sect_master_name"),
        }
        for s in sects.values()
        if not s.get("is_destroyed")
    ]

    return {
        "sects": active_sects,
        "relations": relations,
        "player_sect_id": state.sect_membership.get("sect_id") if state.sect_membership else None,
    }
