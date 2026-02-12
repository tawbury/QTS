"""Feedback Loop KPI 평가."""
from __future__ import annotations

from dataclasses import dataclass

from src.feedback.contracts import FeedbackSummary, KPIThresholds


@dataclass
class KPIResult:
    """개별 KPI 평가 결과."""

    metric: str
    value: float
    threshold: float
    passed: bool


def evaluate_kpis(
    summary: FeedbackSummary,
    thresholds: KPIThresholds | None = None,
) -> list[KPIResult]:
    """FeedbackSummary 기반 KPI 평가.

    Returns:
        5개 KPI 결과 리스트.
    """
    t = thresholds or KPIThresholds()

    return [
        KPIResult(
            metric="avg_slippage_bps",
            value=summary.avg_slippage_bps,
            threshold=t.max_avg_slippage_bps,
            passed=summary.avg_slippage_bps <= t.max_avg_slippage_bps,
        ),
        KPIResult(
            metric="quality_score",
            value=summary.avg_quality_score,
            threshold=t.min_quality_score,
            passed=summary.avg_quality_score >= t.min_quality_score,
        ),
        KPIResult(
            metric="fill_ratio",
            value=summary.avg_fill_ratio,
            threshold=t.min_fill_ratio,
            passed=summary.avg_fill_ratio >= t.min_fill_ratio,
        ),
        KPIResult(
            metric="avg_latency_ms",
            value=summary.avg_fill_latency_ms,
            threshold=t.max_avg_latency_ms,
            passed=summary.avg_fill_latency_ms <= t.max_avg_latency_ms,
        ),
        KPIResult(
            metric="market_impact_bps",
            value=summary.avg_market_impact_bps,
            threshold=t.max_avg_impact_bps,
            passed=summary.avg_market_impact_bps <= t.max_avg_impact_bps,
        ),
    ]
