import os
from typing import Any

from langchain_openai import ChatOpenAI


def request_timeout_seconds() -> float | None:
    raw = (os.getenv("LLM_REQUEST_TIMEOUT") or "").strip()
    if not raw:
        return 240.0
    if raw.lower() in ("0", "none", "off", "false"):
        return None
    return float(raw)


def get_chat_model(
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int | None = None,
    json_mode: bool = False,
    extra_body: dict | None = None,
) -> Any:
    model_kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    req_timeout = request_timeout_seconds()

    kwargs: dict = {
        "model": model or os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash"),
        "temperature": temperature,
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if req_timeout is not None:
        kwargs["request_timeout"] = req_timeout
    if model_kwargs:
        kwargs["model_kwargs"] = model_kwargs
    if extra_body:
        kwargs["extra_body"] = extra_body
    return ChatOpenAI(**kwargs)
