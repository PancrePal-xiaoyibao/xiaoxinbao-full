from __future__ import annotations

from pydantic import BaseModel, Field

from xiaoxinbao.modules.knowledge.retriever import RetrievalStrategy


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=10)
    strategy: RetrievalStrategy | None = None


class KnowledgeHitData(BaseModel):
    title: str
    source: str
    excerpt: str
    score: float
