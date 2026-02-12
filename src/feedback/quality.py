"""Execution Quality Score 계산."""
from __future__ import annotations


def calculate_execution_quality_score(
    total_slippage_bps: float,
    partial_fill_ratio: float,
    avg_fill_latency_ms: float,
) -> float:
    """실행 품질 점수 (0.0 = worst, 1.0 = best).

    가중 평균: slippage 50%, fill 30%, latency 20%.
    """
    # Slippage Score (낮을수록 좋음, 50bps 이상 = 0점)
    slippage_penalty = min(abs(total_slippage_bps) / 50.0, 1.0)
    slippage_score = 1.0 - slippage_penalty

    # Fill Score (partial_fill_ratio 낮을수록 좋음 = 완전 체결)
    fill_score = 1.0 - min(max(partial_fill_ratio, 0.0), 1.0)

    # Latency Score (낮을수록 좋음, 1000ms 이상 = 0점)
    latency_penalty = min(max(avg_fill_latency_ms, 0.0) / 1000.0, 1.0)
    latency_score = 1.0 - latency_penalty

    quality_score = (
        slippage_score * 0.5
        + fill_score * 0.3
        + latency_score * 0.2
    )
    return max(0.0, min(1.0, quality_score))
