from datetime import datetime, timezone
from types import SimpleNamespace

from ops.observer.observer import Observer
from ops.observer.snapshot import ObservationSnapshot


class DummyBus:
    """
    dispatch가 호출되면 안 되는 테스트용 버스.
    호출되면 즉시 실패시킨다.
    """
    def dispatch(self, record):
        raise AssertionError("dispatch() should NOT be called for blocked snapshot")


def main():
    bus = DummyBus()

    observer = Observer(
        session_id="test_block",
        mode="DEV",
        event_bus=bus,
    )

    observer.start()

    # --------------------------------------------------
    # Validation에서 차단되어야 하는 snapshot
    # (Contract 최소 충족 형태)
    # --------------------------------------------------
    snapshot = ObservationSnapshot(
        meta=SimpleNamespace(
            timestamp=datetime.now(timezone.utc).isoformat(),
            timestamp_ms=0,
            session_id="test_block",
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

    observer.on_snapshot(snapshot)
    observer.stop()

    print("[PASS] Blocked snapshot did not reach Phase 4 / EventBus")


if __name__ == "__main__":
    main()
