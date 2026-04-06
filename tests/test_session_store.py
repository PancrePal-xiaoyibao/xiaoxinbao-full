from __future__ import annotations

from datetime import UTC, datetime, timedelta

from xiaoxinbao.modules.sessions.store import SessionStore


class FakeClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 4, 6, tzinfo=UTC)

    def now(self) -> datetime:
        return self.current

    def advance(self, seconds: int) -> None:
        self.current += timedelta(seconds=seconds)


def test_session_store_expires_records() -> None:
    clock = FakeClock()
    store = SessionStore(ttl_seconds=10, max_turns=10, now_fn=clock.now)

    store.append_turn("conv-1", "user", "hello")
    assert len(store.get_turns("conv-1")) == 1

    clock.advance(11)
    assert store.get_turns("conv-1") == []


def test_session_store_keeps_last_turns_only() -> None:
    clock = FakeClock()
    store = SessionStore(ttl_seconds=30, max_turns=2, now_fn=clock.now)

    store.append_turn("conv-2", "user", "1")
    store.append_turn("conv-2", "assistant", "2")
    store.append_turn("conv-2", "user", "3")

    turns = store.get_turns("conv-2")
    assert [turn.content for turn in turns] == ["2", "3"]
