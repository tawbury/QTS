# QTS/src/ops/observer/analysis/dataset_builder.py

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from .contracts.cluster_contract import PatternClusterContract
from .contracts.dataset_contract import ScalpCandidateDatasetContract
from .stats import ClusterStats


class Phase5DatasetBuildError(Exception):
    pass


def build_scalp_candidate_dataset(
    clusters: List[PatternClusterContract],
    stats: Dict[str, ClusterStats],
    *,
    min_count: int = 3,
    min_guard_pass_ratio: float = 0.6,
) -> ScalpCandidateDatasetContract:
    """
    Select clusters that satisfy fixed, explainable criteria.
    """

    selected: List[PatternClusterContract] = []

    for c in clusters:
        s = stats.get(c.cluster_id)
        if not s:
            continue

        if s.count < min_count:
            continue

        if s.guard_pass_ratio < min_guard_pass_ratio:
            continue

        selected.append(c)

    return ScalpCandidateDatasetContract(
        generated_at=datetime.utcnow().isoformat(),
        criteria={
            "min_count": float(min_count),
            "min_guard_pass_ratio": float(min_guard_pass_ratio),
        },
        clusters=selected,
    )
