"""FastAPI app — CMA chat backend."""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.chat import router as chat_router
from api.routes.conversations import router as conversations_router

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Real Estate CMA Assistant",
    version="2.0.0",
    description="CMA chat API — OpenRouter + LangGraph fan-out + Postgres",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")


@app.on_event("startup")
def startup():
    if os.getenv("AUTO_MIGRATE", "true").lower() in ("1", "true", "yes"):
        try:
            from db.client import ensure_schema

            ensure_schema()
            logger.info("Postgres realestate schema ready")
        except Exception as e:
            logger.warning("Schema migration skipped: %s", e)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "cma-assistant",
        "stream": "vercel-ai-sdk",
        "endpoints": {
            "chat": "POST /api/chat",
            "conversations": "GET/POST /api/conversations",
            "messages": "GET /api/conversations/{id}/messages",
        },
    }
