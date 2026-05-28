# launchkit/backend/app/core/openai_client.py
"""
Direct OpenAI REST client via httpx.
No SDK — avoids Windows SSL/proxy issues.
Same pattern as AgentDesk and StackBridge.
"""
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Cost per 1M tokens (gpt-4o-mini as of 2024)
_COST_PER_1M = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 5.00, "output": 15.00},
}


def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Returns cost in USD for a given model + token counts."""
    rates = _COST_PER_1M.get(model, {"input": 0.15, "output": 0.60})
    return (tokens_in * rates["input"] + tokens_out * rates["output"]) / 1_000_000


async def chat_completion(
    *,
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 1000,
    response_format: dict | None = None,
) -> dict[str, Any]:
    """
    Makes a single OpenAI chat completion request.
    Returns the full API response dict.
    Raises httpx.HTTPStatusError on non-2xx.
    """
    model = model or settings.OPENAI_DEFAULT_MODEL

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()

    return resp.json()


def extract_text(response: dict) -> str:
    """Extracts the assistant message text from a completion response."""
    return response["choices"][0]["message"]["content"]


def extract_usage(response: dict) -> tuple[int, int]:
    """Returns (tokens_in, tokens_out) from a completion response."""
    usage = response.get("usage", {})
    return usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)