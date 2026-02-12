"""feedback/contracts.py 단위 테스트."""
from datetime import datetime, timezone
from decimal import Decimal

from src.feedback.contracts import (
    DEFAULT_FEEDBACK_SUMMARY,
    FeedbackConfig,
    FeedbackData,
    FeedbackSummary,
    KPIThresholds,
    MarketContext,
    TickRecord,
)


class TestTickRecord:
    def test_creation(self):
        t = TickRecord(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            symbol="005930",
            price=Decimal("75000"),
            volume=100,
            side="TRADE",
        )
        assert t.symbol == "005930"
        assert t.price == Decimal("75000")
        assert t.side == "TRADE"

    def test_frozen(self):
        t = TickRecord(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            symbol="005930",
            price=Decimal("75000"),
            volume=100,
            side="BID",
        )
        try:
            t.price = Decimal("80000")  # type: ignore[misc]
            assert False, "Should raise"
        except AttributeError:
            pass

    def test_sides(self):
        for side in ("BID", "ASK", "TRADE"):
            t = TickRecord(
                timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                symbol="X",
                price=Decimal("1"),
                volume=1,
                side=side,
            )
            assert t.side == side


class TestMarketContext:
    def test_defaults(self):
        mc = MarketContext()
        assert mc.volatility == 0.0
        assert mc.spread_bps == 0.0
        assert mc.depth == 0
        assert mc.avg_daily_volume == 0

    def test_custom(self):
        mc = MarketContext(
            volatility=0.02,
            spread_bps=5.0,
            depth=15000,
            avg_daily_volume=1_000_000,
        )
        assert mc.avg_daily_volume == 1_000_000


class TestFeedbackData:
    def test_creation_defaults(self):
        now = datetime.now(timezone.utc)
        fd = FeedbackData(
            symbol="005930",
            execution_start=now,
            execution_end=now,
            feedback_generated_at=now,
        )
        assert fd.total_slippage_bps == 0.0
        assert fd.total_filled_qty == Decimal("0")
        assert fd.scalp_ticks == []

    def test_creation_full(self):
        now = datetime.now(timezone.utc)
        tick = TickRecord(
            timestamp=now,
            symbol="005930",
            price=Decimal("75000"),
            volume=100,
            side="TRADE",
        )
        fd = FeedbackData(
            symbol="005930",
            execution_start=now,
            execution_end=now,
            feedback_generated_at=now,
            scalp_ticks=[tick],
            total_slippage_bps=8.5,
            avg_fill_latency_ms=45.2,
            partial_fill_ratio=0.0,
            total_filled_qty=Decimal("100"),
            avg_fill_price=Decimal("75063.5"),
            volatility_at_execution=0.012,
            spread_at_execution=5.3,
            depth_at_execution=15000,
            execution_quality_score=0.92,
            market_impact_bps=3.2,
            strategy_tag="SCALP_RSI",
            order_type="LIMIT",
            original_qty=Decimal("100"),
        )
        assert fd.total_slippage_bps == 8.5
        assert len(fd.scalp_ticks) == 1


class TestFeedbackSummary:
    def test_defaults(self):
        s = FeedbackSummary()
        assert s.avg_slippage_bps == 10.0
        assert s.avg_market_impact_bps == 15.0
        assert s.avg_quality_score == 0.75
        assert s.sample_count == 0

    def test_default_constant(self):
        assert DEFAULT_FEEDBACK_SUMMARY.avg_slippage_bps == 10.0
        assert DEFAULT_FEEDBACK_SUMMARY.sample_count == 0

    def test_custom(self):
        s = FeedbackSummary(
            avg_slippage_bps=5.0,
            avg_market_impact_bps=8.0,
            avg_quality_score=0.92,
            avg_fill_latency_ms=30.0,
            avg_fill_ratio=0.99,
            sample_count=100,
        )
        assert s.sample_count == 100


class TestConfigs:
    def test_feedback_config_defaults(self):
        c = FeedbackConfig()
        assert c.lookback_days == 30
        assert c.min_samples == 5
        assert c.max_acceptable_impact_bps == 20.0

    def test_kpi_thresholds_defaults(self):
        t = KPIThresholds()
        assert t.max_avg_slippage_bps == 10.0
        assert t.min_quality_score == 0.85
        assert t.min_fill_ratio == 0.95
        assert t.max_avg_latency_ms == 100.0
        assert t.max_avg_impact_bps == 15.0

    def test_kpi_thresholds_custom(self):
        t = KPIThresholds(max_avg_slippage_bps=5.0, min_quality_score=0.90)
        assert t.max_avg_slippage_bps == 5.0
        assert t.min_quality_score == 0.90
