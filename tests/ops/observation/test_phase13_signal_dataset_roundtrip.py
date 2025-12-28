from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.observer.analysis.signal_frame.contracts.signal_bundle import SignalBundle
from src.ops.observer.analysis.persistence.signal_dataset_builder import SignalDatasetBuilder
from src.ops.observer.analysis.persistence.signal_dataset_loader import SignalDatasetLoader


def make_sample_signal_bundles() -> list[SignalBundle]:
    return [
        SignalBundle(
            schema_version="signal_bundle.v1",
            record_key="idx:0",
            meta={"source": "test"},
            features={
                "delta_t_prev": 0.0,
                "event_count_last_n": 1,
            },
            conditions={
                "value_change_exceeds_x": False,
                "consecutive_events_ge_n": False,
            },
        ),
        SignalBundle(
            schema_version="signal_bundle.v1",
            record_key="idx:1",
            meta={"source": "test"},
            features={
                "delta_t_prev": 5.0,
                "event_count_last_n": 2,
            },
            conditions={
                "value_change_exceeds_x": True,
                "consecutive_events_ge_n": True,
            },
        ),
    ]


def test_phase13_signal_dataset_builder_loader_roundtrip(tmp_path: Path):
    """
    Phase 13 contract test:

    SignalBundle list
        -> JSONL (builder)
        -> SignalBundle iterable (loader)

    Assertions:
    - record count preserved
    - content preserved (lossless)
    - ordering preserved
    """

    dataset_path = tmp_path / "signal_dataset.jsonl"

    bundles = make_sample_signal_bundles()

    # build (write)
    builder = SignalDatasetBuilder(dataset_path)
    builder.build(bundles)

    assert dataset_path.exists()

    # sanity check: JSONL line count
    lines = dataset_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == len(bundles)

    # load (read)
    loader = SignalDatasetLoader(dataset_path)
    loaded = list(loader.load())

    assert len(loaded) == len(bundles)

    # strict roundtrip equality
    original_dicts = [b.to_dict() for b in bundles]
    loaded_dicts = [b.to_dict() for b in loaded]

    assert original_dicts == loaded_dicts
