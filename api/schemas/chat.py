from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Body from Vercel AI SDK useChat + DefaultChatTransport."""

    messages: list[dict[str, Any]] = Field(default_factory=list)
    id: str | None = None
    conversation_id: str | None = None
    radius_miles: float = Field(default=5.0, ge=1, le=25)
    user_email: str | None = None
    email_delivery_enabled: bool = True
