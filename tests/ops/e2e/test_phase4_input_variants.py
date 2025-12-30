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
    """dict + attribute access (JSON-serializable)"""
    __getattr__ = dict.get


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
# Internal runner
# -------------------------------------------------
def _run_variants():
    filename = "observer_input_variants.jsonl"
    out_path = observer_asset_file(filename)

    # 테스트 재실행 안정성 보장
    if out_path.exists():
        out_path.unlink()

    sink = JsonlFileSink(filename)
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

    with out_path.open(encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    return variants, records


# -------------------------------------------------
# Pytest test
# -------------------------------------------------
def test_phase4_input_variants_are_stable():
    """
    Phase 4:
    Observer + DefaultEnricher must be stable
    against various input shape / type variants.
    """
    variants, records = _run_variants()

    assert len(records) == len(variants)

    for rec in records:
        md = rec.get("metadata", {})
        assert "_schema" in md
        assert "_quality" in md
        assert "_interpretation" in md
