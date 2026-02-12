"""feedback/strategy_enhancer.py 단위 테스트."""
from decimal import Decimal

import pytest

from src.feedback.strategy_enhancer import (
    adjust_confidence,
    adjust_qty_for_market_impact,
    calculate_adjusted_entry_price,
)


class TestCalculateAdjustedEntryPrice:
    def test_buy_positive_slippage(self):
        """매수: 슬리피지만큼 높은 가격."""
        result = calculate_adjusted_entry_price(
            signal_price=Decimal("75000"),
            historical_slippage_bps=10.0,
            side="BUY",
        )
        # 75000 * (1 + 10/10000) = 75000 * 1.001 = 75075
        assert result == Decimal("75000") * Decimal("1.001")

    def test_sell_positive_slippage(self):
        """매도: 슬리피지만큼 낮은 가격."""
        result = calculate_adjusted_entry_price(
            signal_price=Decimal("75000"),
            historical_slippage_bps=10.0,
            side="SELL",
        )
        assert result == Decimal("75000") * Decimal("0.999")

    def test_zero_slippage(self):
        """0 슬리피지면 원래 가격."""
        result = calculate_adjusted_entry_price(
            signal_price=Decimal("75000"),
            historical_slippage_bps=0.0,
            side="BUY",
        )
        assert result == Decimal("75000")

    def test_zero_signal_price(self):
        """시그널 가격 0이면 그대로 반환."""
        result = calculate_adjusted_entry_price(
            signal_price=Decimal("0"),
            historical_slippage_bps=10.0,
            side="BUY",
        )
        assert result == Decimal("0")

    def test_negative_signal_price(self):
        result = calculate_adjusted_entry_price(
            signal_price=Decimal("-100"),
            historical_slippage_bps=10.0,
            side="BUY",
        )
        assert result == Decimal("-100")

    def test_case_insensitive_side(self):
        buy = calculate_adjusted_entry_price(
            signal_price=Decimal("100"),
            historical_slippage_bps=100.0,
            side="buy",
        )
        sell = calculate_adjusted_entry_price(
            signal_price=Decimal("100"),
            historical_slippage_bps=100.0,
            side="sell",
        )
        assert buy > Decimal("100")
        assert sell < Decimal("100")

    def test_large_slippage(self):
        """100bps = 1%."""
        result = calculate_adjusted_entry_price(
            signal_price=Decimal("10000"),
            historical_slippage_bps=100.0,
            side="BUY",
        )
        assert result == Decimal("10000") * Decimal("1.01")


class TestAdjustQtyForMarketImpact:
    def test_under_threshold(self):
        """충격이 허용 이하면 원래 수량."""
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("1000"),
            estimated_impact_bps=10.0,
            max_acceptable_impact_bps=20.0,
        )
        assert result == Decimal("1000")

    def test_at_threshold(self):
        """정확히 허용치면 원래 수량."""
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("1000"),
            estimated_impact_bps=20.0,
            max_acceptable_impact_bps=20.0,
        )
        assert result == Decimal("1000")

    def test_over_threshold(self):
        """초과 시 비례 축소."""
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("1000"),
            estimated_impact_bps=50.0,
            max_acceptable_impact_bps=20.0,
        )
        # reduction_ratio = 20/50 = 0.4
        assert result == Decimal("1000") * Decimal("0.4")

    def test_zero_qty(self):
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("0"),
            estimated_impact_bps=50.0,
        )
        assert result == Decimal("0")

    def test_negative_qty(self):
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("-100"),
            estimated_impact_bps=50.0,
        )
        assert result == Decimal("-100")

    def test_double_threshold(self):
        """충격이 2배면 수량 50%."""
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("1000"),
            estimated_impact_bps=40.0,
            max_acceptable_impact_bps=20.0,
        )
        assert result == Decimal("1000") * Decimal("0.5")

    def test_example_from_spec(self):
        """아키텍처 문서 예제: 50bps, max 20bps → 40%."""
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("1000"),
            estimated_impact_bps=50.0,
            max_acceptable_impact_bps=20.0,
        )
        assert result == Decimal("1000") * Decimal("0.4")


class TestAdjustConfidence:
    def test_full_quality(self):
        assert adjust_confidence(0.8, 1.0) == 0.8

    def test_half_quality(self):
        assert adjust_confidence(0.8, 0.5) == pytest.approx(0.4)

    def test_zero_quality(self):
        assert adjust_confidence(0.8, 0.0) == 0.0

    def test_clamped_max(self):
        assert adjust_confidence(1.0, 1.5) == 1.0

    def test_clamped_min(self):
        assert adjust_confidence(-0.5, 1.0) == 0.0

    def test_typical(self):
        """일반적인 케이스: 0.85 * 0.92 = 0.782."""
        result = adjust_confidence(0.85, 0.92)
        assert pytest.approx(result, abs=0.01) == 0.782
