from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from xiaoxinbao.settings import Settings


@dataclass(slots=True)
class GewechatDeliveryResult:
    success: bool
    payload: dict[str, Any]
    response_data: dict[str, Any]


class GewechatDeliveryClient(Protocol):
    async def send_text(
        self,
        *,
        app_id: str,
        receiver_id: str,
        content: str,
        ats: list[str] | None = None,
    ) -> GewechatDeliveryResult: ...


class HttpGewechatDeliveryClient:
    def __init__(
        self,
        *,
        api_base: str,
        token: str,
        send_text_path: str = "/message/postText",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_base = api_base.rstrip("/")
        self._token = token
        self._send_text_path = send_text_path
        self._transport = transport

    async def send_text(
        self,
        *,
        app_id: str,
        receiver_id: str,
        content: str,
        ats: list[str] | None = None,
    ) -> GewechatDeliveryResult:
        payload = {
            "appId": app_id,
            "toWxid": receiver_id,
            "content": content,
            "ats": ",".join(ats or []),
        }
        headers = {
            "Content-Type": "application/json",
            "X-GEWE-TOKEN": self._token,
        }
        async with httpx.AsyncClient(
            timeout=30.0,
            transport=self._transport,
        ) as client:
            response = await client.post(
                f"{self._api_base}{self._send_text_path}",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        data = response.json()
        success = int(data.get("ret", 0)) == 200
        return GewechatDeliveryResult(
            success=success,
            payload=payload,
            response_data=data,
        )


def build_gewechat_client(settings: Settings) -> GewechatDeliveryClient | None:
    if not settings.gewechat_send_enabled:
        return None
    if not settings.gewechat_api_base or not settings.gewechat_token:
        return None
    return HttpGewechatDeliveryClient(
        api_base=settings.gewechat_api_base,
        token=settings.gewechat_token,
        send_text_path=settings.gewechat_send_text_path,
    )
