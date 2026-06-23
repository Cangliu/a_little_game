"""LLM response cache — hash-based with TTL for deterministic calls.

Only caches low-temperature calls (< 0.8) where results are stable,
such as memory compression, biography updates, and arc planning.
High-temperature creative calls (EventDirector) are NOT cached.
"""
import hashlib
import time
import logging
from collections import OrderedDict
from typing import Optional

logger = logging.getLogger(__name__)


class LLMCache:
    """In-memory LRU cache for LLM responses with TTL expiry."""

    def __init__(self, max_size: int = 50, ttl_seconds: float = 300.0):
        self._max_size = max_size
        self._ttl = ttl_seconds
        # OrderedDict for LRU: {cache_key: (response, timestamp)}
        self._cache: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    @staticmethod
    def _make_key(system_prompt: str, user_prompt: str) -> str:
        """Create a hash key from prompt pair."""
        combined = f"{system_prompt}\x00{user_prompt}"
        return hashlib.md5(combined.encode("utf-8")).hexdigest()

    def get(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Retrieve cached response, or None if miss/expired."""
        key = self._make_key(system_prompt, user_prompt)
        item = self._cache.get(key)

        if item is None:
            self._misses += 1
            return None

        response, timestamp = item
        if (time.time() - timestamp) > self._ttl:
            # Expired
            del self._cache[key]
            self._misses += 1
            return None

        # Cache hit - move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1
        logger.debug("LLM cache hit (hits=%d, misses=%d)", self._hits, self._misses)
        return response

    def put(self, system_prompt: str, user_prompt: str, response: str) -> None:
        """Store a response in cache."""
        key = self._make_key(system_prompt, user_prompt)

        if key in self._cache:
            self._cache[key] = (response, time.time())
            self._cache.move_to_end(key)
        else:
            # Evict if at capacity
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = (response, time.time())

    @property
    def stats(self) -> dict:
        """Return cache statistics."""
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / max(self._hits + self._misses, 1),
        }


# Module-level singleton
_llm_cache = LLMCache(max_size=50, ttl_seconds=300)


def get_llm_cache() -> LLMCache:
    """Get the singleton LLM cache instance."""
    return _llm_cache
