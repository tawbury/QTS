# QTS/tests/ops/e2e/test_phase5_time_axis.py

from pathlib import Path
import pytest

from ops.observer.analysis.loader import load_pattern_records
from ops.observer.analysis.time_axis import (
    TimeAxisConfig,
    normalize_time_axis,
    Phase5TimeAxisError,
)

# ---------------------------------------------------------------------
# Test data path
# ---------------------------------------------------------------------

# FIX:
# tests/ops/e2e/test_*.py
# parents[3] -> QTS/
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "observer"
TEST_FILE = DATA_DIR / "observer_test.jsonl"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _load_records(max_records=20):
    result = load_pattern_records(
        TEST_FILE,
        strict=True,
        max_records=max_records,
    )
    return result.records


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_time_axis_basic_normalization():
    """
    Time axis should bucket records deterministically.
    """
    records = _load_records(max_records=20)

    ts_view = normalize_time_axis(
        records,
        config=TimeAxisConfig(bucket_seconds=1.0),
    )

    assert ts_view.total_records == len(records)
    assert ts_view.total_buckets >= 1
    assert isinstance(ts_view.buckets, list)

    # All bucket indices must be unique
    bucket_indices = [b.bucket_index for b in ts_view.buckets]
    assert len(bucket_indices) == len(set(bucket_indices))


def test_time_axis_determinism():
    """
    Same input -> same bucket structure.
    """
    records = _load_records(max_records=30)

    ts_view_1 = normalize_time_axis(records)
    ts_view_2 = normalize_time_axis(records)

    assert ts_view_1.total_buckets == ts_view_2.total_buckets
    assert ts_view_1.gaps == ts_view_2.gaps

    for b1, b2 in zip(ts_view_1.buckets, ts_view_2.buckets):
        assert b1.bucket_index == b2.bucket_index
        assert len(b1.records) == len(b2.records)


def test_time_axis_bucket_seconds_effect():
    """
    Different bucket_seconds should change bucket distribution.
    """
    records = _load_records(max_records=50)

    ts_view_1s = normalize_time_axis(
        records,
        config=TimeAxisConfig(bucket_seconds=1.0),
    )
    ts_view_5s = normalize_time_axis(
        records,
        config=TimeAxisConfig(bucket_seconds=5.0),
    )

    # Coarser bucket -> fewer or equal buckets
    assert ts_view_5s.total_buckets <= ts_view_1s.total_buckets


def test_time_axis_unbucketed_allowed():
    """
    Records without timestamp should go to unbucketed when allowed.
    """
    records = _load_records(max_records=10)

    # Force one record to have no timestamp
    mutated = records.copy()
    mutated[0] = mutated[0].__class__(
        session_id=mutated[0].session_id,
        generated_at=mutated[0].generated_at,
        observation={},  # timestamp missing
        schema=mutated[0].schema,
        quality=mutated[0].quality,
        interpretation=mutated[0].interpretation,
    )

    ts_view = normalize_time_axis(
        mutated,
        config=TimeAxisConfig(
            bucket_seconds=1.0,
            allow_missing_timestamps=True,
        ),
    )

    assert len(ts_view.unbucketed) == 1
    assert ts_view.total_records == len(mutated)


def test_time_axis_unbucketed_disallowed():
    """
    Missing timestamp should raise error when not allowed.
    """
    records = _load_records(max_records=10)

    mutated = records.copy()
    mutated[0] = mutated[0].__class__(
        session_id=mutated[0].session_id,
        generated_at=mutated[0].generated_at,
        observation={},  # timestamp missing
        schema=mutated[0].schema,
        quality=mutated[0].quality,
        interpretation=mutated[0].interpretation,
    )

    with pytest.raises(Phase5TimeAxisError):
        normalize_time_axis(
            mutated,
            config=TimeAxisConfig(
                bucket_seconds=1.0,
                allow_missing_timestamps=False,
            ),
        )


def test_time_axis_gap_detection():
    """
    Gaps between bucket indices should be detected.
    """
    records = _load_records(max_records=30)

    ts_view = normalize_time_axis(
        records,
        config=TimeAxisConfig(bucket_seconds=10.0),
    )

    # gaps may or may not exist, but structure must be valid
    for start, end in ts_view.gaps:
        assert start <= end
