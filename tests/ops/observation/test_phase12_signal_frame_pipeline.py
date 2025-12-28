from __future__ import annotations

from src.ops.observer.analysis.signal_frame.pipeline import SignalFrameConfig, build_signal_bundles


def test_phase12_signal_frame_pipeline_is_deterministic():
    records = [
        {"timestamp": 1000, "pattern": "A", "value": 10.0},
        {"timestamp": 1005, "pattern": "A", "value": 10.5},
        {"timestamp": 1010, "pattern": "B", "value": 10.6},
    ]

    cfg = SignalFrameConfig(
        window_n=2,
        value_change_exceeds_x=0.01,
        event_frequency_exceeds_n=2,
        consecutive_events_ge_n=2,
        pattern_reappeared_within_t=60.0,
    )

    out1 = build_signal_bundles(records, config=cfg)
    out2 = build_signal_bundles(records, config=cfg)

    assert [b.to_dict() for b in out1] == [b.to_dict() for b in out2]
    assert len(out1) == 3
    assert all(isinstance(v, bool) for b in out1 for v in b.conditions.values())
