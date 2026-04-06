from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from xiaoxinbao.app import create_app
from xiaoxinbao.modules.knowledge.retriever import KnowledgeRetriever


def test_vector_retrieval_prefers_relevant_document() -> None:
    with TemporaryDirectory() as tmp_dir:
        knowledge_dir = Path(tmp_dir) / "knowledge"
        knowledge_dir.mkdir()
        (knowledge_dir / "stress_support.md").write_text(
            "压力管理与情绪疏导需要先识别情绪，再做呼吸放松。",
            encoding="utf-8",
        )
        (knowledge_dir / "finance.md").write_text(
            "资产配置和基金定投是投资领域的基础话题。",
            encoding="utf-8",
        )

        retriever = KnowledgeRetriever(knowledge_dir=knowledge_dir, default_strategy="vector")
        hits = retriever.search("我最近压力很大，想做情绪疏导", strategy="vector")

        assert hits
        assert hits[0].title == "stress support"


def test_knowledge_search_api_returns_hits() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/knowledge/search",
        json={
            "query": "我今天心情不好，压力也大",
            "strategy": "vector",
            "limit": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["strategy"] == "vector"
    assert payload["hits"]
    assert payload["hits"][0]["title"] == "basic support"
