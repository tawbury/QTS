"""feedback/impact.py 단위 테스트."""
import math
from decimal import Decimal

import pytest

from src.feedback.impact import estimate_market_impact_bps


class TestEstimateMarketImpact:
    def test_example_from_spec(self):
        """아키텍처 문서 예제: 1000주, 1M vol, 5bps spread → ~1.58bps."""
        result = estimate_market_impact_bps(
            order_qty=Decimal("1000"),
            avg_daily_volume=1_000_000,
            spread_bps=5.0,
        )
        expected = 5.0 * math.sqrt(1000 / 1_000_000) * 10
        assert pytest.approx(result, abs=0.01) == expected

    def test_zero_volume(self):
        """거래량 0이면 0 반환."""
        result = estimate_market_impact_bps(
            order_qty=Decimal("100"),
            avg_daily_volume=0,
            spread_bps=5.0,
        )
        assert result == 0.0

    def test_zero_qty(self):
        """수량 0이면 0 반환."""
        result = estimate_market_impact_bps(
            order_qty=Decimal("0"),
            avg_daily_volume=1_000_000,
            spread_bps=5.0,
        )
        assert result == 0.0

    def test_negative_volume(self):
        """음수 거래량은 0 반환."""
        result = estimate_market_impact_bps(
            order_qty=Decimal("100"),
            avg_daily_volume=-100,
            spread_bps=5.0,
        )
        assert result == 0.0

    def test_large_order(self):
        """대량 주문은 큰 충격."""
        small = estimate_market_impact_bps(
            order_qty=Decimal("100"),
            avg_daily_volume=1_000_000,
            spread_bps=5.0,
        )
        large = estimate_market_impact_bps(
            order_qty=Decimal("10000"),
            avg_daily_volume=1_000_000,
            spread_bps=5.0,
        )
        assert large > small

    def test_sqrt_relationship(self):
        """충격은 수량의 제곱근에 비례."""
        impact_1x = estimate_market_impact_bps(
            order_qty=Decimal("1000"),
            avg_daily_volume=1_000_000,
            spread_bps=5.0,
        )
        impact_4x = estimate_market_impact_bps(
            order_qty=Decimal("4000"),
            avg_daily_volume=1_000_000,
            spread_bps=5.0,
        )
        # sqrt(4x) / sqrt(x) = 2
        assert pytest.approx(impact_4x / impact_1x, abs=0.01) == 2.0

    def test_spread_proportional(self):
        """충격은 스프레드에 비례."""
        impact_5 = estimate_market_impact_bps(
            order_qty=Decimal("1000"),
            avg_daily_volume=1_000_000,
            spread_bps=5.0,
        )
        impact_10 = estimate_market_impact_bps(
            order_qty=Decimal("1000"),
            avg_daily_volume=1_000_000,
            spread_bps=10.0,
        )
        assert pytest.approx(impact_10 / impact_5, abs=0.01) == 2.0

    def test_zero_spread(self):
        """스프레드 0이면 충격 0."""
        result = estimate_market_impact_bps(
            order_qty=Decimal("1000"),
            avg_daily_volume=1_000_000,
            spread_bps=0.0,
        )
        assert result == 0.0

    def test_small_participation(self):
        """소량 참여율."""
        result = estimate_market_impact_bps(
            order_qty=Decimal("10"),
            avg_daily_volume=10_000_000,
            spread_bps=3.0,
        )
        assert result < 1.0  # 매우 작은 충격
