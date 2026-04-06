from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SessionTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
