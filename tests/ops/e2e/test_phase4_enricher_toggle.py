from datetime import datetime, timezone
import json

from ops.observer.observer import Observer
from ops.observer.snapshot import ObservationSnapshot
from ops.observer.event_bus import EventBus, JsonlFileSink
from paths import observer_asset_file


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
# Internal runner
# -------------------------------------------------
def _run_case():
    filename = "observer_toggle_test.jsonl"
    out_path = observer_asset_file(filename)

    # 테스트 재실행 안정성 보장
    if out_path.exists():
        out_path.unlink()

    sink = JsonlFileSink(filename)
    bus = EventBus(sinks=[sink])

    observer = Observer(
        session_id="toggle_test",
        mode="DEV",
        event_bus=bus,
        enricher=None,  # DefaultEnricher 자동 적용
    )

    observer.start()
    observer.on_snapshot(make_snapshot())
    observer.stop()

    with out_path.open(encoding="utf-8") as f:
        record = json.loads(next(f))

    return record.get("metadata", {})


# -------------------------------------------------
# Pytest test
# -------------------------------------------------
def test_phase4_default_enricher_always_on():
    """
    Phase 4:
    DefaultEnricher must always be applied when enricher=None.
    """
    metadata = _run_case()

    assert "_schema" in metadata
    assert "_quality" in metadata
    assert "_interpretation" in metadata
