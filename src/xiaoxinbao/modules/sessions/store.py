from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Literal

from xiaoxinbao.modules.sessions.models import SessionTurn


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass
class SessionRecord:
    turns: list[SessionTurn] = field(default_factory=list)
    expires_at: datetime = field(default_factory=utc_now)


class SessionStore:
    def __init__(
        self,
        ttl_seconds: int,
        max_turns: int,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_turns = max_turns
        self._now_fn = now_fn or utc_now
        self._records: dict[str, SessionRecord] = {}
        self._lock = Lock()

    def append_turn(
        self,
        conversation_id: str,
        role: Literal["user", "assistant"],
        content: str,
    ) -> None:
        turn = SessionTurn(role=role, content=content, created_at=self._now_fn())
        with self._lock:
            self._purge_expired_locked()
            record = self._records.setdefault(
                conversation_id,
                SessionRecord(expires_at=self._now_fn() + timedelta(seconds=self._ttl_seconds)),
            )
            record.turns.append(turn)
            record.turns = record.turns[-self._max_turns :]
            record.expires_at = self._now_fn() + timedelta(seconds=self._ttl_seconds)

    def get_turns(self, conversation_id: str) -> list[SessionTurn]:
        with self._lock:
            self._purge_expired_locked()
            record = self._records.get(conversation_id)
            if record is None:
                return []
            return list(record.turns)

    def clear_expired(self) -> None:
        with self._lock:
            self._purge_expired_locked()

    def _purge_expired_locked(self) -> None:
        now = self._now_fn()
        expired_ids = [
            conversation_id
            for conversation_id, record in self._records.items()
            if record.expires_at <= now
        ]
        for conversation_id in expired_ids:
            self._records.pop(conversation_id, None)
