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
    """dict + attribute access (JSON-serializable)"""
    __getattr__ = dict.get


# -------------------------------------------------
# Paths
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_FILE = PROJECT_ROOT / "data" / "observer" / "observer_input_variants.jsonl"


# -------------------------------------------------
# Snapshot factory (variant-based)
# -------------------------------------------------
def make_snapshot(variant: str):
    base_meta = AttrDict({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timestamp_ms": 123,
        "session_id": "variant_test",
        "run_id": f"run_{variant}",
        "mode": "DEV",
        "observer_version": "v1.0.0",
    })

    base_context = AttrDict({
        "source": "market",
        "stage": "raw",
        "symbol": "TEST",
        "market": "SIM",
    })

    if variant == "empty_inputs":
        observation = AttrDict({
            "inputs": {},
            "computed": {},
            "state": {},
        })

    elif variant == "missing_volume":
        observation = AttrDict({
            "inputs": {"price": 100.0},
            "computed": {},
            "state": {},
        })

    elif variant == "extra_noise":
        observation = AttrDict({
            "inputs": {"price": 100.0, "volume": 10, "noise": "XYZ"},
            "computed": {"weird": [1, 2, 3]},
            "state": {"flag": True},
        })

    elif variant == "wrong_type":
        observation = AttrDict({
            "inputs": {"price": "100", "volume": "10"},
            "computed": {},
            "state": {},
        })

    else:
        raise ValueError("Unknown variant")

    return ObservationSnapshot(
        meta=base_meta,
        context=base_context,
        observation=observation,
    )


# -------------------------------------------------
# Main
# -------------------------------------------------
def main():
    if OUT_FILE.exists():
        OUT_FILE.unlink()

    sink = JsonlFileSink(str(OUT_FILE))
    bus = EventBus(sinks=[sink])

    observer = Observer(
        session_id="variant_test",
        mode="DEV",
        event_bus=bus,
        enricher=None,  # DefaultEnricher always on
    )

    observer.start()

    variants = [
        "empty_inputs",
        "missing_volume",
        "extra_noise",
        "wrong_type",
    ]

    for v in variants:
        observer.on_snapshot(make_snapshot(v))

    observer.stop()

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------
    with OUT_FILE.open(encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    assert len(records) == len(variants)

    for rec in records:
        md = rec.get("metadata", {})
        assert "_schema" in md
        assert "_quality" in md
        assert "_interpretation" in md

    print("[PASS] Phase 4 is stable against input variants")


if __name__ == "__main__":
    main()
