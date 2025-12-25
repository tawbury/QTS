# QTS/tests/e2e/test_phase5_clustering.py

from pathlib import Path

import pytest

from ops.observer.analysis.loader import load_pattern_records
from ops.observer.analysis.time_axis import normalize_time_axis, TimeAxisConfig
from ops.observer.analysis.clustering import (
    ClusterConfig,
    cluster_patterns,
    Phase5ClusteringError,
)


# ---------------------------------------------------------------------
# Test data path
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "observer"
TEST_FILE = DATA_DIR / "observer_test.jsonl"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _load_records(max_records=50):
    result = load_pattern_records(
        TEST_FILE,
        strict=True,
        max_records=max_records,
    )
    return result.records


def _build_time_view(records):
    return normalize_time_axis(
        records,
        config=TimeAxisConfig(bucket_seconds=5.0),
    )


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_clustering_basic_smoke():
    """
    Clustering should produce at least one cluster with valid inputs.
    """
    records = _load_records(max_records=50)
    ts_view = _build_time_view(records)

    clusters = cluster_patterns(
        ts_view,
        config=ClusterConfig(),
    )

    assert clusters.total_clusters >= 1
    assert clusters.total_records == ts_view.total_records
    assert isinstance(clusters.clusters, list)


def test_clustering_determinism():
    """
    Same input must produce identical clustering structure.
    """
    records = _load_records(max_records=60)
    ts_view = _build_time_view(records)

    result_1 = cluster_patterns(ts_view)
    result_2 = cluster_patterns(ts_view)

    assert result_1.total_clusters == result_2.total_clusters

    for c1, c2 in zip(result_1.clusters, result_2.clusters):
        assert c1.cluster_id == c2.cluster_id
        assert len(c1.records) == len(c2.records)


def test_clustering_config_effect():
    """
    Changing clustering config should alter cluster granularity.
    """
    records = _load_records(max_records=80)
    ts_view = _build_time_view(records)

    fine = cluster_patterns(
        ts_view,
        config=ClusterConfig(min_cluster_size=1),
    )
    coarse = cluster_patterns(
        ts_view,
        config=ClusterConfig(min_cluster_size=5),
    )

    # Larger min_cluster_size -> fewer or equal clusters
    assert coarse.total_clusters <= fine.total_clusters


def test_clustering_empty_input():
    """
    Empty time view should raise error.
    """
    with pytest.raises(Phase5ClusteringError):
        cluster_patterns(
            ts_view=None,  # invalid input
        )


def test_clustering_unbucketed_handling():
    """
    Unbucketed records should not break clustering.
    """
    records = _load_records(max_records=20)

    # Force one record to be unbucketed by removing snapshot
    mutated = records.copy()
    mutated[0] = mutated[0].__class__(
        session_id=mutated[0].session_id,
        generated_at=mutated[0].generated_at,
        observation={},  # no snapshot/meta
        schema=mutated[0].schema,
        quality=mutated[0].quality,
        interpretation=mutated[0].interpretation,
    )

    ts_view = normalize_time_axis(
        mutated,
        config=TimeAxisConfig(
            bucket_seconds=5.0,
            allow_missing_timestamps=True,
        ),
    )

    clusters = cluster_patterns(ts_view)

    # All records must be accounted for
    assert clusters.total_records == ts_view.total_records


def test_clustering_cluster_id_stability():
    """
    Cluster IDs must be stable and ordered.
    """
    records = _load_records(max_records=40)
    ts_view = _build_time_view(records)

    clusters = cluster_patterns(ts_view)

    cluster_ids = [c.cluster_id for c in clusters.clusters]

    # IDs should be monotonic integers starting from 0
    assert cluster_ids == list(range(len(cluster_ids)))
