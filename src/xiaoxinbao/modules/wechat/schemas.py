from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DeliveryResultData(BaseModel):
    attempted: bool
    success: bool = False
    receiver_id: str | None = None
    ats: list[str] = Field(default_factory=list)
    content: str | None = None
    provider_response: dict[str, object] | None = None
    error: str | None = None


class NormalizedInboundMessage(BaseModel):
    message_id: str
    chat_type: Literal["direct", "group"]
    conversation_id: str
    sender_id: str
    sender_name: str
    room_id: str | None = None
    room_name: str | None = None
    mentioned: bool = False
    content: str
    created_at: int


class CallbackProcessResult(BaseModel):
    accepted: bool
    reason: str
    conversation_id: str | None = None
    reply: str | None = None
    normalized_message: NormalizedInboundMessage | None = None
    delivery: DeliveryResultData | None = None
