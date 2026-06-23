"""DeepSeek LLM client — unified API access with timeout fallback.

Uses the OpenAI SDK with custom base_url pointing to DeepSeek.
When API key is missing or call times out, returns None to trigger
JSON fallback narratives.

Dual-model strategy:
- deepseek-v4-flash (default): high-frequency narrative tasks
- deepseek-v4-pro (on-demand): critical planning & high-tension moments

Integrates LLMCache: low-temperature calls (< 0.8) are automatically cached.
"""
from __future__ import annotations

import os
import time
import logging
from typing import Optional, Generator

from .llm_cache import get_llm_cache

# ── Model constants ──────────────────────────────────────────────────────
MODEL_FLASH = "deepseek-v4-flash"
MODEL_PRO = "deepseek-v4-pro"

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))
except ImportError:
    pass

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin wrapper around DeepSeek API via OpenAI SDK.

    Features:
    - Graceful degradation: returns None when unavailable
    - Timeout: 8s hard limit per call (DeepSeek Flash is fast)
    - Dual-model: default Flash, override with model param per call
    """

    def __init__(self, model: str = MODEL_FLASH, timeout: float = 8.0):
        self.model = model
        self.timeout = timeout
        self._client: Optional[OpenAI] = None
        self._available = False

        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if api_key and HAS_OPENAI:
            try:
                self._client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com",
                    timeout=timeout,
                )
                self._available = True
                logger.info("LLMClient initialized with model=%s", self.model)
            except Exception as e:
                logger.warning("Failed to initialize OpenAI client: %s", e)
        else:
            if not HAS_OPENAI:
                logger.info("openai package not installed, LLM disabled")
            elif not api_key:
                logger.info("DEEPSEEK_API_KEY not set, LLM disabled")

    @property
    def available(self) -> bool:
        """Whether the LLM client is properly configured."""
        return self._available

    def generate_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.8,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """Synchronous generation. Returns None on any failure.

        This is the primary method for the game engine (not async).
        On timeout or API error, returns None so the caller can
        fall back to JSON text.

        Args:
            model: Override model for this call. None = use default (Flash).
                   Pass MODEL_PRO for critical planning tasks.

        Low-temperature calls (< 0.8) are automatically cached.
        """
        if not self._available:
            return None

        use_model = model or self.model

        # Check cache for low-temperature (deterministic) calls
        use_cache = temperature < 0.8
        if use_cache:
            cache = get_llm_cache()
            cached = cache.get(system_prompt, user_prompt)
            if cached is not None:
                return cached

        try:
            t0 = time.time()
            response = self._client.chat.completions.create(
                model=use_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,
            )
            content = response.choices[0].message.content
            result = content.strip() if content else None
            elapsed = time.time() - t0
            logger.debug("LLM %s sync: %.2fs, %d tokens", use_model, elapsed, max_tokens)

            # Store in cache if applicable
            if result and use_cache:
                cache.put(system_prompt, user_prompt, result)

            return result
        except Exception as e:
            logger.warning("LLM generation failed (%s): %s", use_model, e)
            return None

    def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.8,
        model: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Streaming generation. Yields text chunks.

        Used by the streaming EventDirector for real-time narrative output.
        Returns empty generator on any failure.

        Args:
            model: Override model for this call. None = use default (Flash).
        """
        if not self._available:
            return

        use_model = model or self.model

        try:
            response = self._client.chat.completions.create(
                model=use_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.warning("LLM stream failed (%s): %s", use_model, e)

    def generate_with_thinking(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        reasoning_effort: str = "low",
        model: Optional[str] = None,
    ) -> Optional[str]:
        """Generation with reasoning/thinking enabled (for complex tasks).

        Uses DeepSeek's thinking mode for memory compression etc.
        Returns None on failure.

        Args:
            model: Override model for this call. None = use default.
        """
        if not self._available:
            return None

        use_model = model or self.model

        try:
            response = self._client.chat.completions.create(
                model=use_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                stream=False,
                extra_body={"thinking": {"type": "enabled"}},
            )
            content = response.choices[0].message.content
            return content.strip() if content else None
        except Exception as e:
            logger.warning("LLM thinking generation failed (%s): %s", use_model, e)
            return None
