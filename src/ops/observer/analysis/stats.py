# QTS/src/ops/observer/analysis/stats.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .contracts.cluster_contract import PatternClusterContract


@dataclass(frozen=True)
class ClusterStats:
    cluster_id: str
    pattern_type: str
    count: int
    guard_pass_ratio: float
    first_ts: float | None
    last_ts: float | None


def aggregate_cluster_stats(
    clusters: List[PatternClusterContract],
) -> Dict[str, ClusterStats]:
    """
    Produce read-only statistics per cluster.
    """

    stats: Dict[str, ClusterStats] = {}

    for c in clusters:
        ts = sorted(c.timestamps)
        stats[c.cluster_id] = ClusterStats(
            cluster_id=c.cluster_id,
            pattern_type=c.pattern_type,
            count=c.size,
            guard_pass_ratio=c.guard_pass_ratio,
            first_ts=ts[0] if ts else None,
            last_ts=ts[-1] if ts else None,
        )

    return stats
