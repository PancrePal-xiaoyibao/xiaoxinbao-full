from __future__ import annotations

from fastapi.testclient import TestClient

from xiaoxinbao.app import create_app


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
