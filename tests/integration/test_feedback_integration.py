"""Feedback Loop 통합 테스트 — 전체 피드백 사이클."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.feedback.aggregator import FeedbackAggregator, NoopFeedbackDB
from src.feedback.contracts import (
    DEFAULT_FEEDBACK_SUMMARY,
    FeedbackConfig,
    FeedbackSummary,
    KPIThresholds,
    MarketContext,
    TickRecord,
)
from src.feedback.impact import estimate_market_impact_bps
from src.feedback.kpi import evaluate_kpis
from src.feedback.quality import calculate_execution_quality_score
from src.feedback.slippage import calculate_slippage_bps
from src.feedback.strategy_enhancer import (
    adjust_confidence,
    adjust_qty_for_market_impact,
    calculate_adjusted_entry_price,
)


class TestFullFeedbackCycle:
    """ExecutionResult → FeedbackData → Strategy Enhancement 전체 사이클."""

    def test_happy_path(self):
        """정상 실행 피드백 사이클."""
        now = datetime.now(timezone.utc)
        db = NoopFeedbackDB()
        agg = FeedbackAggregator(db)

        # 1. Aggregate feedback from execution
        feedback = agg.aggregate_and_store(
            symbol="005930",
            order_id="order-1",
            execution_start=now,
            execution_end=now,
            decision_price=Decimal("75000"),
            avg_fill_price=Decimal("75050"),
            filled_qty=Decimal("100"),
            original_qty=Decimal("100"),
            partial_fill_ratio=0.0,
            avg_fill_latency_ms=45.0,
            strategy_tag="SCALP_RSI",
            order_type="LIMIT",
            market=MarketContext(
                volatility=0.012,
                spread_bps=5.0,
                depth=15000,
                avg_daily_volume=1_000_000,
            ),
        )

        # 2. Verify feedback data
        assert feedback.symbol == "005930"
        assert feedback.total_slippage_bps > 0
        assert feedback.execution_quality_score > 0.8
        assert feedback.market_impact_bps > 0
        assert len(db.stored) == 1

        # 3. Apply feedback to strategy
        adjusted_price = calculate_adjusted_entry_price(
            signal_price=Decimal("76000"),
            historical_slippage_bps=feedback.total_slippage_bps,
            side="BUY",
        )
        assert adjusted_price > Decimal("76000")

        adjusted_qty = adjust_qty_for_market_impact(
            target_qty=Decimal("500"),
            estimated_impact_bps=feedback.market_impact_bps,
        )
        assert adjusted_qty == Decimal("500")  # impact under threshold

        confidence = adjust_confidence(0.85, feedback.execution_quality_score)
        assert 0.0 < confidence < 1.0

    def test_poor_execution_cycle(self):
        """나쁜 실행: 높은 슬리피지, 부분 체결."""
        now = datetime.now(timezone.utc)
        agg = FeedbackAggregator(NoopFeedbackDB())

        feedback = agg.aggregate(
            symbol="035720",
            order_id="order-2",
            execution_start=now,
            execution_end=now,
            decision_price=Decimal("50000"),
            avg_fill_price=Decimal("50200"),  # 40bps slippage
            filled_qty=Decimal("50"),
            original_qty=Decimal("100"),
            partial_fill_ratio=0.5,
            avg_fill_latency_ms=500.0,
            market=MarketContext(
                volatility=0.05,
                spread_bps=15.0,
                depth=5000,
                avg_daily_volume=500_000,
            ),
        )

        # Quality score should be low
        assert feedback.execution_quality_score < 0.7
        assert feedback.total_slippage_bps > 30

        # Strategy should reduce qty due to high impact
        adjusted_qty = adjust_qty_for_market_impact(
            target_qty=Decimal("1000"),
            estimated_impact_bps=feedback.market_impact_bps,
            max_acceptable_impact_bps=20.0,
        )
        if feedback.market_impact_bps > 20.0:
            assert adjusted_qty < Decimal("1000")

    def test_feedback_with_ticks(self):
        """틱 데이터 포함 피드백."""
        now = datetime.now(timezone.utc)
        ticks = [
            TickRecord(timestamp=now, symbol="005930", price=Decimal("75000"), volume=100, side="TRADE"),
            TickRecord(timestamp=now, symbol="005930", price=Decimal("75010"), volume=50, side="ASK"),
            TickRecord(timestamp=now, symbol="005930", price=Decimal("75020"), volume=200, side="TRADE"),
        ]
        agg = FeedbackAggregator(NoopFeedbackDB())
        feedback = agg.aggregate(
            symbol="005930",
            order_id="order-3",
            execution_start=now,
            execution_end=now,
            decision_price=Decimal("75000"),
            avg_fill_price=Decimal("75010"),
            filled_qty=Decimal("350"),
            original_qty=Decimal("350"),
            partial_fill_ratio=0.0,
            avg_fill_latency_ms=30.0,
            ticks=ticks,
        )
        assert len(feedback.scalp_ticks) == 3


class TestKPIIntegration:
    """KPI 평가 통합 테스트."""

    def test_good_performance_kpis(self):
        """좋은 성능 → 대부분 KPI 통과."""
        summary = FeedbackSummary(
            avg_slippage_bps=5.0,
            avg_market_impact_bps=8.0,
            avg_quality_score=0.92,
            avg_fill_latency_ms=30.0,
            avg_fill_ratio=0.99,
            sample_count=100,
        )
        results = evaluate_kpis(summary)
        assert all(r.passed for r in results)

    def test_bad_performance_kpis(self):
        """나쁜 성능 → KPI 실패."""
        summary = FeedbackSummary(
            avg_slippage_bps=25.0,
            avg_market_impact_bps=30.0,
            avg_quality_score=0.60,
            avg_fill_latency_ms=200.0,
            avg_fill_ratio=0.80,
        )
        results = evaluate_kpis(summary)
        assert all(not r.passed for r in results)

    def test_strict_thresholds(self):
        """엄격한 기준 적용."""
        summary = FeedbackSummary(
            avg_slippage_bps=8.0,
            avg_quality_score=0.88,
        )
        strict = KPIThresholds(max_avg_slippage_bps=5.0, min_quality_score=0.90)
        results = evaluate_kpis(summary, strict)
        slippage = next(r for r in results if r.metric == "avg_slippage_bps")
        quality = next(r for r in results if r.metric == "quality_score")
        assert slippage.passed is False
        assert quality.passed is False


class TestFallbackBehavior:
    """Fail-Safe: 피드백 없을 때 기본값 사용."""

    def test_default_summary_used(self):
        """피드백 데이터 없으면 기본 요약값 사용."""
        agg = FeedbackAggregator(NoopFeedbackDB())
        summary = agg.get_summary("UNKNOWN_SYMBOL")
        assert summary == DEFAULT_FEEDBACK_SUMMARY
        assert summary.avg_slippage_bps == 10.0
        assert summary.avg_quality_score == 0.75

    def test_strategy_works_with_defaults(self):
        """기본값으로도 전략 보정 동작."""
        summary = DEFAULT_FEEDBACK_SUMMARY

        price = calculate_adjusted_entry_price(
            signal_price=Decimal("75000"),
            historical_slippage_bps=summary.avg_slippage_bps,
            side="BUY",
        )
        assert price > Decimal("75000")  # 10bps 보정

        qty = adjust_qty_for_market_impact(
            target_qty=Decimal("1000"),
            estimated_impact_bps=summary.avg_market_impact_bps,
        )
        assert qty == Decimal("1000")  # impact 15 < max 20 → no reduction

    def test_confidence_with_default_quality(self):
        """기본 품질 점수로 신뢰도 보정."""
        confidence = adjust_confidence(0.90, DEFAULT_FEEDBACK_SUMMARY.avg_quality_score)
        assert pytest.approx(confidence, abs=0.01) == 0.675  # 0.90 * 0.75


class TestCalculationConsistency:
    """개별 계산 모듈 간 일관성 확인."""

    def test_slippage_in_aggregator_matches_standalone(self):
        """Aggregator 내 슬리피지 = 독립 계산 결과."""
        now = datetime.now(timezone.utc)
        decision = Decimal("75000")
        fill = Decimal("75050")

        standalone = calculate_slippage_bps(decision, fill)

        agg = FeedbackAggregator(NoopFeedbackDB())
        feedback = agg.aggregate(
            symbol="X",
            order_id="X",
            execution_start=now,
            execution_end=now,
            decision_price=decision,
            avg_fill_price=fill,
            filled_qty=Decimal("100"),
            original_qty=Decimal("100"),
            partial_fill_ratio=0.0,
            avg_fill_latency_ms=0.0,
        )
        assert feedback.total_slippage_bps == standalone

    def test_quality_in_aggregator_matches_standalone(self):
        """Aggregator 내 품질 점수 = 독립 계산 결과."""
        now = datetime.now(timezone.utc)
        agg = FeedbackAggregator(NoopFeedbackDB())

        slippage_bps = 8.5
        fill_ratio = 0.05
        latency_ms = 45.0

        standalone = calculate_execution_quality_score(slippage_bps, fill_ratio, latency_ms)

        feedback = agg.aggregate(
            symbol="X",
            order_id="X",
            execution_start=now,
            execution_end=now,
            decision_price=Decimal("75000"),
            avg_fill_price=Decimal("75063.75"),  # ≈ 8.5bps
            filled_qty=Decimal("100"),
            original_qty=Decimal("100"),
            partial_fill_ratio=fill_ratio,
            avg_fill_latency_ms=latency_ms,
        )
        # Note: aggregator calculates slippage from prices, so exact match depends on price
        assert abs(feedback.execution_quality_score - standalone) < 0.05
