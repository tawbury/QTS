# QTS/src/ops/observer/analysis/pipeline.py

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .loader import load_pattern_records
from .time_axis import TimeAxisConfig, normalize_time_axis
from .clustering import cluster_patterns
from .stats import aggregate_cluster_stats
from .dataset_builder import build_scalp_candidate_dataset


def run_phase5_pipeline(
    input_path: Path,
    *,
    bucket_seconds: float = 1.0,
    max_records: Optional[int] = None,
):
    """
    Execute Phase 5 Offline Analysis Pipeline.

    Order is fixed and must not be altered.
    """

    # 1) Load
    load_result = load_pattern_records(
        input_path,
        strict=True,
        max_records=max_records,
    )

    # 2) Time normalization
    ts_view = normalize_time_axis(
        load_result.records,
        config=TimeAxisConfig(bucket_seconds=bucket_seconds),
    )

    # 3) Clustering
    clusters = cluster_patterns(ts_view)

    # 4) Statistics
    stats = aggregate_cluster_stats(clusters)

    # 5) Dataset build
    dataset = build_scalp_candidate_dataset(clusters, stats)

    return {
        "load": load_result,
        "time_series": ts_view,
        "clusters": clusters,
        "stats": stats,
        "dataset": dataset,
    }
