from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ConversationMetadata(BaseModel):
    chat_type: Literal["direct", "group"] = "direct"
    sender_id: str | None = None
    sender_name: str | None = None
    room_id: str | None = None
    room_name: str | None = None
    mentioned: bool = False
