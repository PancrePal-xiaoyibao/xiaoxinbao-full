from __future__ import annotations

import json

import httpx

from xiaoxinbao.modules.llm.openai_compatible import OpenAICompatibleGateway
from xiaoxinbao.modules.wechat.client import HttpGewechatDeliveryClient


async def test_openai_compatible_gateway_posts_expected_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["json"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )

    gateway = OpenAICompatibleGateway(
        api_base="https://llm.example/v1",
        api_key="secret",
        default_model="demo-model",
        transport=httpx.MockTransport(handler),
    )

    result = await gateway.chat([{"role": "user", "content": "hello"}])

    assert result == "ok"
    assert captured["url"] == "https://llm.example/v1/chat/completions"
    assert captured["json"] == {
        "model": "demo-model",
        "messages": [{"role": "user", "content": "hello"}],
    }
    assert captured["headers"]["authorization"] == "Bearer secret"


async def test_gewechat_delivery_client_posts_expected_payload() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["json"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={"ret": 200, "msg": "success"})

    client = HttpGewechatDeliveryClient(
        api_base="https://gewechat.example/v2/api",
        token="gewe-secret",
        transport=httpx.MockTransport(handler),
    )

    result = await client.send_text(
        app_id="app-001",
        receiver_id="room_123@chatroom",
        content="@张三 你好",
        ats=["wxid_user"],
    )

    assert result.success is True
    assert captured["url"] == "https://gewechat.example/v2/api/message/postText"
    assert captured["json"] == {
        "appId": "app-001",
        "toWxid": "room_123@chatroom",
        "content": "@张三 你好",
        "ats": "wxid_user",
    }
    assert captured["headers"]["x-gewe-token"] == "gewe-secret"
