from __future__ import annotations

from fastapi.testclient import TestClient

from xiaoxinbao.app import create_app


def test_chat_reply_endpoint_returns_mock_response() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/chat/reply",
        json={
            "message": "我今天心情不好",
            "conversation_id": "debug-001",
            "sender_name": "小明",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["conversation_id"] == "debug-001"
    assert "小馨宝回应" in payload["data"]["reply"]
    assert "basic support" in payload["data"]["citations"]
