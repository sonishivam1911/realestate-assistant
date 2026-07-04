"""Streaming chat — Vercel AI SDK UIMessageStream protocol."""

import logging

from ai_sdk_stream_python import StreamContext
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.schemas.chat import ChatRequest
from services.cma_stream import stream_cma_chat

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    ctx = StreamContext(collect=True)

    async def _work(c: StreamContext) -> None:
        await stream_cma_chat(
            messages=request.messages,
            conversation_id=request.conversation_id or request.id,
            radius_miles=request.radius_miles,
            user_email=request.user_email,
            email_delivery_enabled=request.email_delivery_enabled,
            ctx=c,
        )

    await ctx.run(_work)
    return StreamingResponse(
        ctx.stream(),
        media_type="text/event-stream",
        headers=ctx.response_headers,
    )
