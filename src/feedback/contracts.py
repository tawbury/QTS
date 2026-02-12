"""Feedback Loop 데이터 계약."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


# ---------------------------------------------------------------------------
# TickRecord
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TickRecord:
    """개별 틱 레코드."""

    timestamp: datetime
    symbol: str
    price: Decimal
    volume: int
    side: str  # BID / ASK / TRADE


# ---------------------------------------------------------------------------
# MarketContext
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MarketContext:
    """실행 시점 시장 컨텍스트."""

    volatility: float = 0.0
    spread_bps: float = 0.0
    depth: int = 0
    avg_daily_volume: int = 0


# ---------------------------------------------------------------------------
# FeedbackData
# ---------------------------------------------------------------------------

@dataclass
class FeedbackData:
    """Execution → Strategy 피드백 데이터."""

    # Metadata
    symbol: str
    execution_start: datetime
    execution_end: datetime
    feedback_generated_at: datetime

    # Tick Data
    scalp_ticks: list[TickRecord] = field(default_factory=list)

    # Execution Metrics
    total_slippage_bps: float = 0.0
    avg_fill_latency_ms: float = 0.0
    partial_fill_ratio: float = 0.0
    total_filled_qty: Decimal = Decimal("0")
    avg_fill_price: Decimal = Decimal("0")

    # Market Context at Execution
    volatility_at_execution: float = 0.0
    spread_at_execution: float = 0.0
    depth_at_execution: int = 0

    # Learning Signals
    execution_quality_score: float = 0.0
    market_impact_bps: float = 0.0

    # Strategy Context
    strategy_tag: str = ""
    order_type: str = ""
    original_qty: Decimal = Decimal("0")


# ---------------------------------------------------------------------------
# FeedbackSummary
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeedbackSummary:
    """종목별 피드백 집계 요약."""

    avg_slippage_bps: float = 10.0       # Conservative default
    avg_market_impact_bps: float = 15.0
    avg_quality_score: float = 0.75
    avg_fill_latency_ms: float = 50.0
    avg_fill_ratio: float = 0.95
    sample_count: int = 0


DEFAULT_FEEDBACK_SUMMARY = FeedbackSummary()


# ---------------------------------------------------------------------------
# Configs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeedbackConfig:
    """피드백 집계 설정."""

    lookback_days: int = 30
    min_samples: int = 5
    max_acceptable_impact_bps: float = 20.0


@dataclass(frozen=True)
class KPIThresholds:
    """Execution Quality KPI 기준값."""

    max_avg_slippage_bps: float = 10.0
    min_quality_score: float = 0.85
    min_fill_ratio: float = 0.95
    max_avg_latency_ms: float = 100.0
    max_avg_impact_bps: float = 15.0
