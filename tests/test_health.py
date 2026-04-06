from __future__ import annotations

from fastapi.testclient import TestClient

from xiaoxinbao.app import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["status"] == "ok"
