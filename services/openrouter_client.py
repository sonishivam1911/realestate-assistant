"""OpenRouter chat + Exa web search. Chinese models for reasoning; Exa for grounding."""

import json
import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

OPENROUTER_BASE = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
WEB_SEARCH_ENGINE = os.getenv("CMA_WEB_SEARCH_ENGINE", "exa")


def _headers() -> dict[str, str]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://realestate-assistant.local"),
        "X-Title": os.getenv("OPENROUTER_APP_TITLE", "Real Estate CMA Assistant"),
    }


def chat_with_web_search(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    search_engine: str | None = None,
) -> dict[str, Any]:
    """
    Call OpenRouter with web_search tool (Exa by default).
    Returns {content, citations, raw}.
    """
    engine = search_engine or WEB_SEARCH_ENGINE
    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "tools": [
            {
                "type": "web_search",
                "web_search": {"engine": engine},
            }
        ],
    }

    response = requests.post(
        f"{OPENROUTER_BASE}/chat/completions",
        headers=_headers(),
        json=payload,
        timeout=float(os.getenv("LLM_REQUEST_TIMEOUT", "240")),
    )
    response.raise_for_status()
    data = response.json()

    message = data["choices"][0]["message"]
    content = message.get("content") or ""
    citations = _extract_citations(data)
    return {"content": content, "citations": citations, "raw": data}


def chat_completion(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 8192,
    json_mode: bool = False,
) -> str:
    """Plain completion without web search (synthesis node)."""
    payload: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    response = requests.post(
        f"{OPENROUTER_BASE}/chat/completions",
        headers=_headers(),
        json=payload,
        timeout=float(os.getenv("LLM_REQUEST_TIMEOUT", "240")),
    )
    response.raise_for_status()
    return response["choices"][0]["message"]["content"]


def _extract_citations(data: dict) -> list[dict]:
    citations: list[dict] = []
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})

    for ann in message.get("annotations") or []:
        if ann.get("type") == "url_citation":
            cite = ann.get("url_citation") or ann
            citations.append(
                {
                    "url": cite.get("url", ""),
                    "title": cite.get("title", ""),
                    "content": cite.get("content", ""),
                }
            )

    # Fallback: scan raw JSON for url fields
    if not citations:
        raw_str = json.dumps(data)
        import re

        for url in re.findall(r"https?://[^\s\"'<>]+", raw_str):
            if any(d in url for d in ("zillow", "redfin", "realtor", "gov", "fred")):
                citations.append({"url": url, "title": "", "content": ""})

    return citations
