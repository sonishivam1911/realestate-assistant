from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str | None = None
    subject_address: str | None = None
    radius_miles: float = Field(default=5.0, ge=1, le=25)
    user_email: str | None = None


class ConversationUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    user_email: str | None = None


class ConversationOut(BaseModel):
    id: UUID
    title: str | None
    subject_address: str | None
    user_email: str | None = None
    radius_miles: float | None
    status: str
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ConversationListResponse(BaseModel):
    conversations: list[ConversationOut]


class MessageListResponse(BaseModel):
    messages: list[MessageOut]
