"""
Solacia - API Routes

FastAPI routes for:
- Chat Completions (OpenAI-compatible)
- Models listing
- Mood Diary CRUD + emotion stats
"""

import json
import logging
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from solacia.agent.conversation import ConversationEngine
from solacia.memory.diary import DiaryService

logger = logging.getLogger(__name__)

router = APIRouter()

# Conversation engine cache (keyed by session_id)
conversation_engines: dict[str, ConversationEngine] = {}

# Diary service (shared instance)
diary_service = DiaryService()


# ==================== Data Models ====================


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "solacia"
    messages: List[ChatMessage]
    stream: bool = False
    session_id: Optional[str] = None


class DiaryCreateRequest(BaseModel):
    emotions: List[str]
    summary: Optional[str] = None
    message_count: Optional[int] = 0


# ==================== Chat Completions ====================


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """
    OpenAI-compatible Chat Completions endpoint.

    Supports both streaming and non-streaming modes.
    """
    session_id = request.session_id or str(uuid.uuid4())

    if session_id not in conversation_engines:
        conversation_engines[session_id] = ConversationEngine()

    engine = conversation_engines[session_id]

    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")

    user_input = user_messages[-1].content

    if request.stream:
        return StreamingResponse(
            stream_response(engine, user_input, request.model),
            media_type="text/event-stream",
        )
    else:
        reply = await engine.achat(user_input)

        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": reply,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        }


async def stream_response(engine: ConversationEngine, user_input: str, model: str):
    """Generate streaming SSE response chunks."""
    async for chunk in engine.achat_stream(user_input):
        data = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion.chunk",
            "created": int(datetime.now().timestamp()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": chunk},
                    "finish_reason": None,
                }
            ],
        }
        yield f"data: {json.dumps(data)}\n\n"

    # End-of-stream marker
    data = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion.chunk",
        "created": int(datetime.now().timestamp()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {},
                "finish_reason": "stop",
            }
        ],
    }
    yield f"data: {json.dumps(data)}\n\n"
    yield "data: [DONE]\n\n"


# ==================== Models ====================


@router.get("/v1/models")
async def list_models():
    """List available models."""
    return {
        "data": [
            {
                "id": "solacia",
                "object": "model",
                "owned_by": "solacia",
            }
        ]
    }


# ==================== Mood Diary ====================


@router.post("/v1/diary")
async def create_diary_entry(request: DiaryCreateRequest):
    """Create a new mood diary entry."""
    entry = diary_service.create_entry(
        emotions=request.emotions,
        summary=request.summary,
        message_count=request.message_count,
    )
    return entry


@router.get("/v1/diary")
async def get_diary_entries(limit: int = 20):
    """Get mood diary entries."""
    entries = diary_service.get_entries(limit=limit)
    return {"entries": entries}


@router.get("/v1/diary/{entry_id}")
async def get_diary_entry(entry_id: int):
    """Get a single diary entry by ID."""
    entry = diary_service.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Diary entry not found")
    return entry


@router.get("/v1/diary/stats/emotions")
async def get_emotion_stats(days: int = 7):
    """Get emotion statistics over a time period."""
    stats = diary_service.get_emotion_stats(days=days)
    return {"days": days, "emotions": stats}
