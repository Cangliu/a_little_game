"""DeepSeek LLM client — unified API access with timeout fallback.

Uses the OpenAI SDK with custom base_url pointing to DeepSeek.
When API key is missing or call times out, returns None to trigger
JSON fallback narratives.
"""
from __future__ import annotations

import os
import logging
from typing import Optional

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
    - Model: deepseek-v4-0324 (Flash, low cost)
    """

    def __init__(self, model: str = "deepseek-v4-0324", timeout: float = 8.0):
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
    ) -> Optional[str]:
        """Synchronous generation. Returns None on any failure.

        This is the primary method for the game engine (not async).
        On timeout or API error, returns None so the caller can
        fall back to JSON text.
        """
        if not self._available:
            return None

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,
            )
            content = response.choices[0].message.content
            return content.strip() if content else None
        except Exception as e:
            logger.warning("LLM generation failed: %s", e)
            return None

    def generate_with_thinking(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        reasoning_effort: str = "low",
    ) -> Optional[str]:
        """Generation with reasoning/thinking enabled (for complex tasks).

        Uses DeepSeek's thinking mode for memory compression etc.
        Returns None on failure.
        """
        if not self._available:
            return None

        try:
            response = self._client.chat.completions.create(
                model=self.model,
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
            logger.warning("LLM thinking generation failed: %s", e)
            return None
