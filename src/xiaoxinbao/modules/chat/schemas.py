from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str = "debug-session"
    sender_name: str | None = None
    room_name: str | None = None
    mentioned: bool = False


class ChatReplyData(BaseModel):
    conversation_id: str
    reply: str
    citations: list[str]
