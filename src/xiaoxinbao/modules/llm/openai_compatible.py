from __future__ import annotations

from typing import Any

import httpx

from xiaoxinbao.modules.llm.base import LLMGateway, LLMMessage


class OpenAICompatibleGateway(LLMGateway):
    def __init__(
        self,
        api_base: str,
        api_key: str | None,
        default_model: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_base = api_base.rstrip("/")
        self._api_key = api_key
        self._default_model = default_model
        self._transport = transport

    async def chat(self, messages: list[LLMMessage], model: str | None = None) -> str:
        payload = {
            "model": model or self._default_model,
            "messages": messages,
        }
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        async with httpx.AsyncClient(timeout=30.0, transport=self._transport) as client:
            response = await client.post(
                f"{self._api_base}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        data: dict[str, Any] = response.json()
        return str(data["choices"][0]["message"]["content"])
