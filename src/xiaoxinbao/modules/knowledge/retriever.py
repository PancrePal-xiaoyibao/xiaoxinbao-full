from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel


class KnowledgeHit(BaseModel):
    title: str
    source: str
    excerpt: str
    score: int


class _KnowledgeDocument(BaseModel):
    title: str
    source: str
    content: str


class KnowledgeRetriever:
    def __init__(self, knowledge_dir: Path) -> None:
        self._knowledge_dir = knowledge_dir
        self._documents = self._load_documents()

    def search(self, query: str, limit: int = 3) -> list[KnowledgeHit]:
        tokens = self._tokenize(query)
        if not tokens:
            return []

        scored: list[KnowledgeHit] = []
        for document in self._documents:
            content_lower = document.content.lower()
            score = sum(content_lower.count(token.lower()) for token in tokens)
            if query.lower() in content_lower:
                score += 3
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
                )
            )
        return documents

    @staticmethod
    def _tokenize(query: str) -> list[str]:
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
