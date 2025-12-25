from datetime import datetime, timezone
import json
from pathlib import Path

from ops.observer.observer import Observer
from ops.observer.snapshot import ObservationSnapshot
from ops.observer.event_bus import EventBus, JsonlFileSink


# -------------------------------------------------
# Test-only helper
# -------------------------------------------------
class AttrDict(dict):
    """
    dict + attribute access
    JSON serializable & Observer contract compatible
    """
    __getattr__ = dict.get


# -------------------------------------------------
# Paths
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_FILE = PROJECT_ROOT / "data" / "observer" / "observer_toggle_test.jsonl"


# -------------------------------------------------
# Snapshot factory
# -------------------------------------------------
def make_snapshot():
    return ObservationSnapshot(
        meta=AttrDict({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "timestamp_ms": 123,
            "session_id": "toggle_test",
            "run_id": "run_toggle",
            "mode": "DEV",
            "observer_version": "v1.0.0",
        }),
        context=AttrDict({
            "source": "market",
            "stage": "raw",
            "symbol": "TEST",
            "market": "SIM",
        }),
        observation=AttrDict({
            "inputs": {"price": 100.0, "volume": 10},
            "computed": {},
            "state": {},
        }),
    )


# -------------------------------------------------
# Single test run
# -------------------------------------------------
def run_case(label):
    if OUT_FILE.exists():
        OUT_FILE.unlink()

    sink = JsonlFileSink(str(OUT_FILE))
    bus = EventBus(sinks=[sink])

    # NOTE:
    # enricher=None → DefaultEnricher 자동 적용 (설계 확정 사항)
    observer = Observer(
        session_id="toggle_test",
        mode="DEV",
        event_bus=bus,
        enricher=None,
    )

    observer.start()
    observer.on_snapshot(make_snapshot())
    observer.stop()

    with OUT_FILE.open(encoding="utf-8") as f:
        record = json.loads(next(f))

    metadata = record.get("metadata", {})
    print(f"[{label}] metadata keys:", list(metadata.keys()))

    return metadata


# -------------------------------------------------
# Main
# -------------------------------------------------
def main():
    # ---------------------------------------------
    # Phase 4 DefaultEnricher 항상 활성 검증
    # ---------------------------------------------
    md = run_case(label="DEFAULT ENRICHER (ALWAYS ON)")

    assert "_schema" in md
    assert "_quality" in md
    assert "_interpretation" in md

    print("[PASS] Phase 4 DefaultEnricher is always applied")


if __name__ == "__main__":
    main()
