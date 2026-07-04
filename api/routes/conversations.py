"""Conversation CRUD — chat thread persistence."""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from api.schemas.conversations import (
    ConversationCreate,
    ConversationListResponse,
    ConversationOut,
    ConversationUpdate,
    MessageListResponse,
    MessageOut,
)
from db import client as db

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _db_unavailable(exc: Exception) -> HTTPException:
    return HTTPException(503, f"Database unavailable: {exc}")


@router.get("", response_model=ConversationListResponse)
def list_conversations(limit: int = 50):
    try:
        rows = db.list_conversations(limit=limit)
        return ConversationListResponse(
            conversations=[ConversationOut(**_serialize_row(r)) for r in rows]
        )
    except Exception as e:
        raise _db_unavailable(e) from e


@router.post("", response_model=ConversationOut, status_code=201)
def create_conversation(body: ConversationCreate):
    try:
        cid = db.create_conversation(
            title=body.title,
            subject_address=body.subject_address,
            radius_miles=body.radius_miles,
            user_email=body.user_email,
        )
        row = db.get_conversation(cid)
        return ConversationOut(**_serialize_row(row))
    except Exception as e:
        raise _db_unavailable(e) from e


@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: UUID):
    try:
        row = db.get_conversation(str(conversation_id))
        if not row:
            raise HTTPException(404, "Conversation not found")
        return ConversationOut(**_serialize_row(row))
    except HTTPException:
        raise
    except Exception as e:
        raise _db_unavailable(e) from e


@router.patch("/{conversation_id}", response_model=ConversationOut)
def update_conversation(conversation_id: UUID, body: ConversationUpdate):
    try:
        updated = db.update_conversation(
            str(conversation_id),
            title=body.title,
            status=body.status,
            user_email=body.user_email,
        )
        if not updated:
            raise HTTPException(404, "Conversation not found")
        return ConversationOut(**_serialize_row(updated))
    except HTTPException:
        raise
    except Exception as e:
        raise _db_unavailable(e) from e


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: UUID):
    try:
        if not db.delete_conversation(str(conversation_id)):
            raise HTTPException(404, "Conversation not found")
    except HTTPException:
        raise
    except Exception as e:
        raise _db_unavailable(e) from e


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
def get_messages(conversation_id: UUID):
    try:
        if not db.get_conversation(str(conversation_id)):
            raise HTTPException(404, "Conversation not found")
        rows = db.get_messages(str(conversation_id))
        return MessageListResponse(
            messages=[MessageOut(**_serialize_message(r)) for r in rows]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise _db_unavailable(e) from e


def _serialize_row(row: dict) -> dict:
    return {
        "id": row["id"],
        "title": row.get("title"),
        "subject_address": row.get("subject_address"),
        "user_email": row.get("user_email"),
        "radius_miles": float(row["radius_miles"]) if row.get("radius_miles") is not None else None,
        "status": row.get("status", "active"),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _serialize_message(row: dict) -> dict:
    meta = row.get("metadata") or {}
    if isinstance(meta, str):
        import json
        meta = json.loads(meta)
    return {
        "id": row["id"],
        "role": row["role"],
        "content": row["content"],
        "metadata": meta,
        "created_at": row["created_at"],
    }
