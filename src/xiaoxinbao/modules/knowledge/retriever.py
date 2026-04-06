from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

RetrievalStrategy = Literal["keyword", "vector"]


class KnowledgeHit(BaseModel):
    title: str
    source: str
    excerpt: str
    score: float


class _KnowledgeDocument(BaseModel):
    title: str
    source: str
    content: str
    tokens: list[str]


class KnowledgeRetriever:
    def __init__(
        self,
        knowledge_dir: Path,
        default_strategy: RetrievalStrategy = "keyword",
    ) -> None:
        self._knowledge_dir = knowledge_dir
        self._default_strategy = default_strategy
        self._documents = self._load_documents()

    def search(
        self,
        query: str,
        limit: int = 3,
        strategy: RetrievalStrategy | None = None,
    ) -> list[KnowledgeHit]:
        tokens = self._tokenize(query)
        if not tokens:
            return []
        resolved_strategy = strategy or self._default_strategy
        if resolved_strategy == "vector":
            return self._vector_search(query=query, tokens=tokens, limit=limit)
        return self._keyword_search(query=query, tokens=tokens, limit=limit)

    def _keyword_search(self, query: str, tokens: list[str], limit: int) -> list[KnowledgeHit]:
        scored: list[KnowledgeHit] = []
        for document in self._documents:
            content_lower = document.content.lower()
            score = float(sum(content_lower.count(token.lower()) for token in tokens))
            if query.lower() in content_lower:
                score += 3.0
            if score <= 0:
                continue
            excerpt = self._build_excerpt(document.content, tokens)
            scored.append(
                KnowledgeHit(
                    title=document.title,
                    source=document.source,
                    excerpt=excerpt,
                    score=score,
                )
            )
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]

    def _vector_search(self, query: str, tokens: list[str], limit: int) -> list[KnowledgeHit]:
        query_counter = Counter(tokens)
        query_norm = self._counter_norm(query_counter)
        if query_norm == 0:
            return []

        scored: list[KnowledgeHit] = []
        for document in self._documents:
            document_counter = Counter(document.tokens)
            document_norm = self._counter_norm(document_counter)
            if document_norm == 0:
                continue
            intersection = set(query_counter) & set(document_counter)
            numerator = sum(
                query_counter[token] * document_counter[token]
                for token in intersection
            )
            score = numerator / (query_norm * document_norm)
            if score <= 0:
                continue
            scored.append(
                KnowledgeHit(
                    title=document.title,
                    source=document.source,
                    excerpt=self._build_excerpt(document.content, tokens),
                    score=round(score, 6),
                )
            )
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]

    def _load_documents(self) -> list[_KnowledgeDocument]:
        if not self._knowledge_dir.exists():
            return []

        documents: list[_KnowledgeDocument] = []
        for path in sorted(self._knowledge_dir.rglob("*.md")):
            content = path.read_text(encoding="utf-8")
            title = path.stem.replace("_", " ")
            documents.append(
                _KnowledgeDocument(
                    title=title,
                    source=path.as_posix(),
                    content=content,
                    tokens=self._tokenize(content),
                )
            )
        return documents

    @classmethod
    def _tokenize(cls, query: str) -> list[str]:
        tokens: list[str] = []
        for raw_token in re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]{2,}", query):
            if not raw_token:
                continue
            if re.fullmatch(r"[\u4e00-\u9fff]{4,}", raw_token):
                tokens.extend(raw_token[index : index + 2] for index in range(len(raw_token) - 1))
            tokens.append(raw_token)
        return list(dict.fromkeys(tokens))

    @staticmethod
    def _build_excerpt(content: str, tokens: list[str]) -> str:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            if any(token.lower() in line.lower() for token in tokens):
                return line[:200]
        return lines[0][:200] if lines else ""

    @staticmethod
    def _counter_norm(counter: Counter[str]) -> float:
        return math.sqrt(sum(value * value for value in counter.values()))
