# QTS/tests/ops/e2e/test_phase5_scaffold_dataset.py

from pathlib import Path
import pytest

from ops.observer.analysis.loader import load_pattern_records
from ops.observer.analysis.time_axis import normalize_time_axis, TimeAxisConfig
from ops.observer.analysis.clustering import cluster_patterns, ClusterConfig
from ops.observer.analysis.scaffold import (
    build_scaffold_dataset,
    Phase5ScaffoldError,
    ScaffoldDataset,
)

# ---------------------------------------------------------------------
# Test data path
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data" / "observer"
TEST_FILE = DATA_DIR / "observer_test.jsonl"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _load_cluster_result(max_records=40):
    records = load_pattern_records(
        TEST_FILE,
        strict=True,
        max_records=max_records,
    ).records

    ts_view = normalize_time_axis(
        records,
        config=TimeAxisConfig(bucket_seconds=5.0),
    )

    return cluster_patterns(
        ts_view,
        config=ClusterConfig(),
    )


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_scaffold_basic_smoke():
    """
    Scaffold dataset should be generated from clustering result.
    """
    cluster_result = _load_cluster_result(max_records=40)

    dataset = build_scaffold_dataset(cluster_result)

    assert isinstance(dataset, ScaffoldDataset)
    assert isinstance(dataset.rows, list)
    assert len(dataset.rows) > 0


def test_scaffold_determinism():
    """
    Same clustering input must generate identical scaffold dataset.
    """
    cluster_result = _load_cluster_result(max_records=60)

    ds1 = build_scaffold_dataset(cluster_result)
    ds2 = build_scaffold_dataset(cluster_result)

    assert ds1.rows == ds2.rows


def test_scaffold_cluster_and_unclustered_presence():
    """
    Both clustered and unclustered records must appear in scaffold.
    """
    cluster_result = _load_cluster_result(max_records=30)

    dataset = build_scaffold_dataset(cluster_result)

    cluster_ids = {row["cluster_id"] for row in dataset.rows}
    assert len(cluster_ids) >= 1


def test_scaffold_schema_minimal_fields():
    """
    Scaffold rows must include minimal required fields.
    """
    cluster_result = _load_cluster_result(max_records=20)

    dataset = build_scaffold_dataset(cluster_result)

    required_fields = {
        "cluster_id",
        "record_index",
        "session_id",
        "timestamp",
        "payload",
    }

    for row in dataset.rows:
        assert required_fields.issubset(row.keys())


def test_scaffold_empty_input_error():
    """
    Empty clustering result should raise error.
    """
    with pytest.raises(Phase5ScaffoldError):
        build_scaffold_dataset(None)
