from __future__ import annotations

from typing import Protocol, TypedDict


class LLMMessage(TypedDict):
    role: str
    content: str


class LLMGateway(Protocol):
    async def chat(self, messages: list[LLMMessage], model: str | None = None) -> str: ...
