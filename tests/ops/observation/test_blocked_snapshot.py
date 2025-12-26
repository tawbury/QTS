# tests/ops/observation/test_blocked_snapshot.py

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from ops.observer.observer import Observer
from ops.observer.snapshot import ObservationSnapshot


class DummyBus:
    """
    EventBus 대체 객체.
    dispatch가 호출되면 안 되는 테스트용 버스.
    """
    def dispatch(self, record):
        raise AssertionError(
            "dispatch() should NOT be called for blocked snapshot"
        )


def _build_blocked_snapshot(session_id: str) -> ObservationSnapshot:
    """
    Validation 단계에서 차단되어야 하는 최소 snapshot 생성.
    """
    return ObservationSnapshot(
        meta=SimpleNamespace(
            timestamp=datetime.now(timezone.utc).isoformat(),
            timestamp_ms=0,
            session_id=session_id,
            run_id="run_nan",
            mode="DEV",
            observer_version="v1.0.0",
        ),
        context=SimpleNamespace(
            source="market",
            stage="raw",
            symbol="TEST",
            market="SIM",
        ),
        observation=SimpleNamespace(
            inputs={"price": float("nan")},  # Validation 차단 유도
            computed={},
            state={},
        ),
    )


def test_blocked_snapshot_does_not_reach_event_bus():
    """
    Validation에서 차단된 snapshot은
    EventBus.dispatch로 절대 전달되지 않아야 한다.
    """
    bus = DummyBus()

    observer = Observer(
        session_id="test_block",
        mode="DEV",
        event_bus=bus,
    )

    observer.start()

    snapshot = _build_blocked_snapshot(session_id="test_block")

    # dispatch가 호출되면 DummyBus에서 AssertionError 발생
    observer.on_snapshot(snapshot)

    observer.stop()
