from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from xiaoxinbao.app import create_app
from xiaoxinbao.bootstrap import ServiceContainer, get_container
from xiaoxinbao.modules.chat.service import AgentService
from xiaoxinbao.modules.knowledge.retriever import KnowledgeRetriever
from xiaoxinbao.modules.llm.mock import MockGateway
from xiaoxinbao.modules.sessions.store import SessionStore
from xiaoxinbao.modules.wechat.client import GewechatDeliveryResult
from xiaoxinbao.modules.wechat.normalizer import GewechatAdapter
from xiaoxinbao.modules.wechat.service import WechatService
from xiaoxinbao.settings import Settings


class FakeDeliveryClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

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
            "ats": ats or [],
        }
        self.calls.append(payload)
        return GewechatDeliveryResult(
            success=True,
            payload=payload,
            response_data={"ret": 200, "msg": "ok"},
        )


def build_delivery_enabled_client() -> tuple[TestClient, FakeDeliveryClient]:
    settings = Settings(
        llm_mode="mock",
        retrieval_mode="keyword",
        gewechat_send_enabled=True,
        gewechat_api_base="https://gewechat.example/v2/api",
        gewechat_token="token-001",
        gewechat_app_id="app-001",
        bot_names=["小馨宝"],
        group_trigger_keywords=["小馨宝", "心理", "求助"],
    )
    session_store = SessionStore(ttl_seconds=1800, max_turns=10)
    retriever = KnowledgeRetriever(knowledge_dir=Path("config/knowledge"))
    agent_service = AgentService(
        settings=settings,
        session_store=session_store,
        retriever=retriever,
        gateway=MockGateway(),
    )
    delivery_client = FakeDeliveryClient()
    wechat_service = WechatService(
        settings=settings,
        adapter=GewechatAdapter(bot_names=settings.bot_names),
        agent_service=agent_service,
        delivery_client=delivery_client,
    )
    container = ServiceContainer(
        settings=settings,
        session_store=session_store,
        retriever=retriever,
        agent_service=agent_service,
        wechat_service=wechat_service,
    )
    app = create_app()
    app.dependency_overrides[get_container] = lambda: container
    return TestClient(app), delivery_client


def test_gewechat_callback_processes_group_message() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/wechat/gewechat/callback",
        json={
            "Wxid": "wxid_bot",
            "Data": {
                "MsgId": "1001",
                "MsgType": 1,
                "CreateTime": 4102444800,
                "FromUserName": {"string": "room_123@chatroom"},
                "ToUserName": {"string": "wxid_bot"},
                "ChatroomId": "room_123@chatroom",
                "ChatroomName": "心理互助群",
                "ActualUserName": "张三",
                "Content": {"string": "wxid_user:\n@小馨宝 我今天压力大"},
                "MsgSource": (
                    "<msgsource><atuserlist><![CDATA[,wxid_bot,]]></atuserlist></msgsource>"
                ),
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["accepted"] is True
    assert payload["conversation_id"] == "wxid_user@@room_123@chatroom"
    assert payload["normalized_message"]["mentioned"] is True
    assert payload["normalized_message"]["content"] == "我今天压力大"
    assert payload["delivery"]["attempted"] is False


def test_gewechat_callback_ignores_non_user_messages() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/wechat/gewechat/callback",
        json={
            "Wxid": "wxid_bot",
            "Data": {
                "MsgId": "1002",
                "MsgType": 1,
                "CreateTime": 4102444800,
                "FromUserName": {"string": "gh_official"},
                "ToUserName": {"string": "wxid_bot"},
                "Content": {"string": "测试"},
                "SenderType": "non_user",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["accepted"] is False
    assert payload["reason"] == "non_user"


def test_gewechat_callback_skips_group_message_without_trigger() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/wechat/gewechat/callback",
        json={
            "Wxid": "wxid_bot",
            "Data": {
                "MsgId": "1003",
                "MsgType": 1,
                "CreateTime": 4102444800,
                "FromUserName": {"string": "room_123@chatroom"},
                "ToUserName": {"string": "wxid_bot"},
                "ChatroomId": "room_123@chatroom",
                "ChatroomName": "心理互助群",
                "ActualUserName": "李四",
                "Content": {"string": "wxid_user_2:\n普通聊天内容"},
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["accepted"] is False
    assert payload["reason"] == "group_not_triggered"


def test_gewechat_callback_delivers_reply_when_enabled() -> None:
    client, delivery_client = build_delivery_enabled_client()
    response = client.post(
        "/api/v1/wechat/gewechat/callback",
        json={
            "Wxid": "wxid_bot",
            "Data": {
                "MsgId": "1004",
                "MsgType": 1,
                "CreateTime": 4102444800,
                "FromUserName": {"string": "room_456@chatroom"},
                "ToUserName": {"string": "wxid_bot"},
                "ChatroomId": "room_456@chatroom",
                "ChatroomName": "支持群",
                "ActualUserName": "张三",
                "Content": {"string": "wxid_sender:\n@小馨宝 我需要帮助"},
                "MsgSource": (
                    "<msgsource><atuserlist><![CDATA[,wxid_bot,]]></atuserlist></msgsource>"
                ),
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["accepted"] is True
    assert payload["delivery"]["attempted"] is True
    assert payload["delivery"]["success"] is True
    assert payload["delivery"]["receiver_id"] == "room_456@chatroom"
    assert payload["delivery"]["ats"] == ["wxid_sender"]
    assert delivery_client.calls[0]["content"]
    assert str(delivery_client.calls[0]["content"]).startswith("@张三 ")
