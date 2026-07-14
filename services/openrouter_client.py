"""OpenRouter chat + Exa web search. Chinese models for reasoning; Exa for grounding."""

import json
import logging
import os
import re
from typing import Any

import requests

logger = logging.getLogger(__name__)

OPENROUTER_BASE = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
WEB_SEARCH_ENGINE = os.getenv("CMA_WEB_SEARCH_ENGINE", "exa")
_DSML_MARKERS = ("DSML", "tool_calls", "openrouter_web_search", "<|")


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


def _content_unusable(content: str) -> bool:
    text = (content or "").strip()
    if not text:
        return True
    if text.startswith("{") or text.startswith("["):
        return False
    # DeepSeek sometimes emits tool-call markup instead of final JSON.
    return any(marker in text for marker in _DSML_MARKERS)


def _citations_digest(citations: list[dict], *, limit: int = 18) -> str:
    chunks: list[str] = []
    for index, citation in enumerate(citations[:limit], start=1):
        title = citation.get("title") or ""
        url = citation.get("url") or ""
        body = (citation.get("content") or "")[:1200]
        chunks.append(f"[{index}] {title}\nURL: {url}\n{body}")
    return "\n\n".join(chunks)


def _synthesize_json_from_citations(
    *,
    model: str,
    system_prompt: str,
    user_prompt: str,
    citations: list[dict],
    reasoning: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """Second pass: force JSON from search citations when the tool call left content empty."""
    digest = _citations_digest(citations)
    if not digest.strip():
        return ""

    recovery_system = (
        system_prompt
        + "\n\nYou are given web-search citations. Return ONLY valid JSON matching the "
        "requested schema. Do not invent prices or addresses not supported by the citations."
    )
    recovery_user = (
        f"{user_prompt}\n\n"
        f"MODEL REASONING NOTES:\n{(reasoning or '')[:1500]}\n\n"
        f"WEB SEARCH CITATIONS:\n{digest}\n\n"
        "Return the final JSON object now."
    )
    return chat_completion(
        model=model,
        system_prompt=recovery_system,
        user_prompt=recovery_user,
        temperature=temperature,
        max_tokens=max_tokens,
        json_mode=True,
    )


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
    If the model returns empty/DSML content but useful citations, synthesize JSON
    from those citations in a follow-up completion.
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
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    citations = _extract_citations(data)

    if _content_unusable(content):
        logger.warning(
            "Web-search content unusable (len=%s); synthesizing from %s citations",
            len(content or ""),
            len(citations),
        )
        synthesized = _synthesize_json_from_citations(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            citations=citations,
            reasoning=message.get("reasoning") or "",
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if synthesized.strip():
            content = synthesized

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
    data = response.json()
    content = data["choices"][0]["message"].get("content")
    return content if isinstance(content, str) else ""


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

        for url in re.findall(r"https?://[^\s\"'<>]+", raw_str):
            if any(
                domain in url
                for domain in (
                    "zillow",
                    "redfin",
                    "realtor",
                    "homes.com",
                    "coldwellbanker",
                    "nj.com",
                    "gov",
                    "fred",
                )
            ):
                citations.append({"url": url, "title": "", "content": ""})

    return citations
