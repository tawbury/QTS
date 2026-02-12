"""feedback/aggregator.py 단위 테스트."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.feedback.aggregator import FeedbackAggregator, NoopFeedbackDB
from src.feedback.contracts import (
    DEFAULT_FEEDBACK_SUMMARY,
    FeedbackSummary,
    MarketContext,
    TickRecord,
)


def _make_aggregator():
    db = NoopFeedbackDB()
    return FeedbackAggregator(db), db


def _base_kwargs():
    now = datetime.now(timezone.utc)
    return dict(
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
    )


class TestFeedbackAggregator:
    def test_aggregate_basic(self):
        agg, _ = _make_aggregator()
        feedback = agg.aggregate(**_base_kwargs())
        assert feedback.symbol == "005930"
        assert feedback.total_slippage_bps > 0  # positive slippage
        assert feedback.execution_quality_score > 0
        assert feedback.feedback_generated_at is not None

    def test_aggregate_slippage_calculated(self):
        agg, _ = _make_aggregator()
        feedback = agg.aggregate(**_base_kwargs())
        # (75050 - 75000) / 75000 * 10000 ≈ 6.67 bps
        assert pytest.approx(feedback.total_slippage_bps, abs=0.1) == 6.67

    def test_aggregate_quality_score(self):
        agg, _ = _make_aggregator()
        feedback = agg.aggregate(**_base_kwargs())
        assert 0.0 <= feedback.execution_quality_score <= 1.0

    def test_aggregate_with_market_context(self):
        agg, _ = _make_aggregator()
        kwargs = _base_kwargs()
        kwargs["market"] = MarketContext(
            volatility=0.02,
            spread_bps=5.0,
            depth=15000,
            avg_daily_volume=1_000_000,
        )
        feedback = agg.aggregate(**kwargs)
        assert feedback.volatility_at_execution == 0.02
        assert feedback.spread_at_execution == 5.0
        assert feedback.depth_at_execution == 15000
        assert feedback.market_impact_bps > 0

    def test_aggregate_without_market_context(self):
        agg, _ = _make_aggregator()
        feedback = agg.aggregate(**_base_kwargs())
        assert feedback.market_impact_bps == 0.0  # no volume info

    def test_aggregate_with_ticks(self):
        agg, _ = _make_aggregator()
        kwargs = _base_kwargs()
        tick = TickRecord(
            timestamp=datetime.now(timezone.utc),
            symbol="005930",
            price=Decimal("75000"),
            volume=100,
            side="TRADE",
        )
        kwargs["ticks"] = [tick]
        feedback = agg.aggregate(**kwargs)
        assert len(feedback.scalp_ticks) == 1

    def test_aggregate_and_store(self):
        agg, db = _make_aggregator()
        feedback = agg.aggregate_and_store(**_base_kwargs())
        assert len(db.stored) == 1
        assert db.stored[0].symbol == "005930"

    def test_aggregate_and_store_multiple(self):
        agg, db = _make_aggregator()
        agg.aggregate_and_store(**_base_kwargs())
        agg.aggregate_and_store(**_base_kwargs())
        assert len(db.stored) == 2

    def test_get_summary_default(self):
        agg, _ = _make_aggregator()
        summary = agg.get_summary("005930")
        assert summary == DEFAULT_FEEDBACK_SUMMARY

    def test_get_summary_from_db(self):
        db = NoopFeedbackDB()

        class CustomDB(NoopFeedbackDB):
            def fetch_feedback_summary(self, symbol, lookback_days):
                return FeedbackSummary(
                    avg_slippage_bps=5.0,
                    avg_market_impact_bps=8.0,
                    avg_quality_score=0.92,
                    sample_count=50,
                )

        agg = FeedbackAggregator(CustomDB())
        summary = agg.get_summary("005930")
        assert summary.avg_slippage_bps == 5.0
        assert summary.sample_count == 50

    def test_zero_decision_price(self):
        agg, _ = _make_aggregator()
        kwargs = _base_kwargs()
        kwargs["decision_price"] = Decimal("0")
        feedback = agg.aggregate(**kwargs)
        assert feedback.total_slippage_bps == 0.0
