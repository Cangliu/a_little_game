"""Game state management — LRU+TTL store with per-game locking.

Replaces the old plain dict with a managed store that:
- Automatically evicts states not accessed within TTL (2 hours)
- Enforces a maximum capacity (LRU eviction)
- Provides per-game asyncio.Lock for concurrency safety
- Delays cleanup of finished games (60s grace for summary fetch)
"""
import asyncio
import random
import time
import uuid
import logging
from typing import Optional
from collections import OrderedDict

from ..models import GameState, Attributes

logger = logging.getLogger(__name__)


# ── GameStateStore — LRU + TTL + Locking ─────────────────────────────────

class GameStateStore:
    """Thread-safe game state store with LRU eviction, TTL expiry, and per-game locks."""

    def __init__(self, max_size: int = 100, ttl_seconds: float = 7200):
        self._max_size = max_size
        self._ttl = ttl_seconds
        # OrderedDict for LRU: most recently accessed at the end
        self._store: OrderedDict[str, tuple[GameState, float]] = OrderedDict()
        # Per-game locks (also LRU-managed)
        self._locks: OrderedDict[str, asyncio.Lock] = OrderedDict()
        self._max_locks = 200
        # Finished games pending cleanup: {game_id: cleanup_time}
        self._pending_cleanup: dict[str, float] = {}

    def get(self, game_id: str) -> Optional[GameState]:
        """Retrieve a game state. Returns None if not found or expired."""
        # First, run lazy cleanup
        self._lazy_cleanup()

        item = self._store.get(game_id)
        if item is None:
            return None

        state, last_access = item
        now = time.time()

        # Check TTL
        if (now - last_access) > self._ttl:
            del self._store[game_id]
            logger.debug("Game %s expired (TTL), removed", game_id)
            return None

        # Refresh access time and move to end (most recently used)
        self._store[game_id] = (state, now)
        self._store.move_to_end(game_id)
        return state

    def set(self, game_id: str, state: GameState) -> None:
        """Store a game state. Triggers LRU eviction if at capacity."""
        now = time.time()

        if game_id in self._store:
            # Update existing
            self._store[game_id] = (state, now)
            self._store.move_to_end(game_id)
        else:
            # Evict if at capacity
            while len(self._store) >= self._max_size:
                evicted_id, _ = self._store.popitem(last=False)
                logger.info("LRU eviction: game %s removed (capacity %d)", evicted_id, self._max_size)
            self._store[game_id] = (state, now)

    def mark_finished(self, game_id: str) -> None:
        """Mark a game as finished. It will be cleaned up after 60s grace period."""
        self._pending_cleanup[game_id] = time.time() + 60.0
        logger.debug("Game %s marked finished, cleanup in 60s", game_id)

    def lock(self, game_id: str) -> asyncio.Lock:
        """Get or create a lock for a specific game_id."""
        if game_id in self._locks:
            self._locks.move_to_end(game_id)
            return self._locks[game_id]

        # Evict old locks if too many
        while len(self._locks) >= self._max_locks:
            self._locks.popitem(last=False)

        lk = asyncio.Lock()
        self._locks[game_id] = lk
        return lk

    def _lazy_cleanup(self) -> None:
        """Remove finished games past their grace period."""
        if not self._pending_cleanup:
            return

        now = time.time()
        to_remove = [gid for gid, t in self._pending_cleanup.items() if now >= t]
        for gid in to_remove:
            del self._pending_cleanup[gid]
            if gid in self._store:
                del self._store[gid]
                logger.debug("Cleaned up finished game %s", gid)

    @property
    def size(self) -> int:
        return len(self._store)


# ── Module-level singleton ────────────────────────────────────────────────

GAME_STATE_STORE = GameStateStore(max_size=100, ttl_seconds=7200)

# Legacy alias for backward compatibility (used by game_engine.py)
# New code should use GAME_STATE_STORE directly
GAME_STATES = GAME_STATE_STORE


# ── Anti-streak gender history ────────────────────────────────────────────

_gender_history: list[str] = []


def _pick_gender() -> str:
    """Pick gender with anti-streak bias."""
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


# ── Public API (unchanged interface) ─────────────────────────────────────

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

    GAME_STATE_STORE.set(game_id, state)
    return state


def get_state(game_id: str) -> Optional[GameState]:
    """Retrieve a game state by ID, or None if not found/expired."""
    return GAME_STATE_STORE.get(game_id)
