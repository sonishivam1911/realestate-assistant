"""Minimal Vercel AI SDK v5/v6 UIMessageStream encoder (no extra deps)."""

import json
import uuid
from typing import AsyncIterator


def _sse(payload: dict | str) -> str:
    if isinstance(payload, str):
        return f"data: {payload}\n\n"
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"


STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "x-vercel-ai-ui-message-stream": "v1",
}


class UiMessageStream:
    """Emit start / reasoning / text / source / finish events for useChat."""

    def __init__(self) -> None:
        self.message_id = f"msg_{uuid.uuid4().hex}"
        self._text_id: str | None = None
        self._reasoning_id: str | None = None

    async def start(self) -> AsyncIterator[str]:
        yield _sse({"type": "start", "messageId": self.message_id})

    async def reasoning(self, text: str) -> AsyncIterator[str]:
        if self._reasoning_id is None:
            self._reasoning_id = f"reasoning_{uuid.uuid4().hex}"
            yield _sse({"type": "reasoning-start", "id": self._reasoning_id})
        yield _sse({"type": "reasoning-delta", "id": self._reasoning_id, "delta": text})
        if text and not text.endswith("\n"):
            yield _sse({"type": "reasoning-delta", "id": self._reasoning_id, "delta": "\n"})

    async def end_reasoning(self) -> AsyncIterator[str]:
        if self._reasoning_id:
            yield _sse({"type": "reasoning-end", "id": self._reasoning_id})
            self._reasoning_id = None

    async def text(self, delta: str) -> AsyncIterator[str]:
        if self._text_id is None:
            self._text_id = f"text_{uuid.uuid4().hex}"
            yield _sse({"type": "text-start", "id": self._text_id})
        yield _sse({"type": "text-delta", "id": self._text_id, "delta": delta})

    async def end_text(self) -> AsyncIterator[str]:
        if self._text_id:
            yield _sse({"type": "text-end", "id": self._text_id})
            self._text_id = None

    async def source(self, url: str, title: str = "") -> AsyncIterator[str]:
        yield _sse(
            {
                "type": "source-url",
                "sourceId": url,
                "url": url,
                "title": title or url,
            }
        )

    async def finish(self) -> AsyncIterator[str]:
        if self._reasoning_id:
            async for chunk in self.end_reasoning():
                yield chunk
        if self._text_id:
            async for chunk in self.end_text():
                yield chunk
        yield _sse({"type": "finish"})
        yield _sse("[DONE]")

    async def error(self, message: str) -> AsyncIterator[str]:
        yield _sse({"type": "error", "errorText": message})
        async for chunk in self.finish():
            yield chunk
