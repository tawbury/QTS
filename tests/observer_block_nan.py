import math
import logging

from src.ops.observer.observer import Observer
from src.ops.observer.snapshot import build_snapshot
from src.ops.observer.event_bus import EventBus, JsonlFileSink

logging.basicConfig(level=logging.INFO)


def main():
    # ✅ EventBus는 sinks를 반드시 받고 생성해야 한다
    sink = JsonlFileSink("data/observer/observer_test.jsonl")
    bus = EventBus([sink])

    observer = Observer(
        session_id="test_session",
        mode="DEV",
        event_bus=bus,
    )

    observer.start()

    # 🔴 NaN 주입 (Validation BLOCK 기대)
    snapshot = build_snapshot(
        session_id="test_session",
        mode="DEV",
        source="market",
        stage="raw",
        inputs={"price": math.nan, "volume": 10},
        computed={},
        state={},
        symbol="TEST",
        market="SIM",
    )

    observer.on_snapshot(snapshot)
    observer.stop()


if __name__ == "__main__":
    main()
