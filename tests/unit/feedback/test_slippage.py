"""feedback/slippage.py 단위 테스트."""
from decimal import Decimal

import pytest

from src.feedback.slippage import calculate_slippage_bps


class TestCalculateSlippageBps:
    def test_positive_slippage_buy(self):
        """매수 시 체결가가 높으면 양수 슬리피지."""
        result = calculate_slippage_bps(
            decision_price=Decimal("75000"),
            avg_fill_price=Decimal("75050"),
        )
        assert pytest.approx(result, abs=0.1) == 6.67

    def test_negative_slippage_buy(self):
        """매수 시 체결가가 낮으면 음수 슬리피지 (유리)."""
        result = calculate_slippage_bps(
            decision_price=Decimal("75000"),
            avg_fill_price=Decimal("74950"),
        )
        assert pytest.approx(result, abs=0.1) == -6.67

    def test_zero_slippage(self):
        """동일 가격이면 0."""
        result = calculate_slippage_bps(
            decision_price=Decimal("75000"),
            avg_fill_price=Decimal("75000"),
        )
        assert result == 0.0

    def test_decision_price_zero(self):
        """decision_price가 0이면 0.0 반환."""
        result = calculate_slippage_bps(
            decision_price=Decimal("0"),
            avg_fill_price=Decimal("75000"),
        )
        assert result == 0.0

    def test_large_slippage(self):
        """큰 슬리피지."""
        result = calculate_slippage_bps(
            decision_price=Decimal("10000"),
            avg_fill_price=Decimal("10100"),
        )
        assert pytest.approx(result, abs=0.1) == 100.0  # 100bps = 1%

    def test_sell_favorable(self):
        """매도 시 높은 체결가 = 양수 (유리)."""
        result = calculate_slippage_bps(
            decision_price=Decimal("50000"),
            avg_fill_price=Decimal("50025"),
        )
        assert result > 0

    def test_small_price(self):
        """소수점 가격."""
        result = calculate_slippage_bps(
            decision_price=Decimal("1.0000"),
            avg_fill_price=Decimal("1.0010"),
        )
        assert pytest.approx(result, abs=0.1) == 10.0

    def test_exact_bps_conversion(self):
        """1bps = 0.01% = 0.0001."""
        result = calculate_slippage_bps(
            decision_price=Decimal("100000"),
            avg_fill_price=Decimal("100010"),
        )
        assert pytest.approx(result, abs=0.01) == 1.0
