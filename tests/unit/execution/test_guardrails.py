"""Execution Guardrails 테스트."""
from decimal import Decimal

import pytest

from src.execution.contracts import SplitOrder, SplitOrderStatus
from src.execution.guardrails import (
    check_all_sends_failed,
    check_daily_trade_limit,
    check_fill_delay,
    check_fill_timeout,
    check_insufficient_balance,
    check_invalid_symbol,
    check_slippage,
    check_slippage_exceeded,
    check_split_count,
)
from src.provider.models.order_request import OrderSide


def _make_split(seq=1) -> SplitOrder:
    return SplitOrder(
        split_id=f"s{seq}", parent_order_id="p", sequence=seq,
        symbol="005930", side=OrderSide.BUY, qty=100,
    )


class TestGR060SplitCount:
    def test_within_limit(self):
        splits = [_make_split(i) for i in range(10)]
        assert check_split_count(splits) == []

    def test_exceeds_limit(self):
        splits = [_make_split(i) for i in range(25)]
        alerts = check_split_count(splits, max_splits=20)
        assert len(alerts) == 1
        assert alerts[0].code == "GR060"

    def test_exact_limit(self):
        splits = [_make_split(i) for i in range(20)]
        assert check_split_count(splits) == []


class TestGR061InsufficientBalance:
    def test_sufficient(self):
        assert check_insufficient_balance(Decimal("5000"), Decimal("10000")) == []

    def test_insufficient(self):
        alerts = check_insufficient_balance(Decimal("10000"), Decimal("5000"))
        assert len(alerts) == 1
        assert alerts[0].code == "GR061"

    def test_zero_balance(self):
        alerts = check_insufficient_balance(Decimal("1000"), Decimal("0"))
        assert len(alerts) == 1
        assert alerts[0].code == "GR061"


class TestGR062DailyLimit:
    def test_under_limit(self):
        assert check_daily_trade_limit(50) == []

    def test_at_limit(self):
        alerts = check_daily_trade_limit(100)
        assert len(alerts) == 1
        assert alerts[0].code == "GR062"

    def test_over_limit(self):
        alerts = check_daily_trade_limit(150, limit=100)
        assert len(alerts) == 1


class TestGR063Slippage:
    def test_no_slippage(self):
        assert check_slippage(Decimal("75000"), Decimal("75000")) == []

    def test_within_threshold(self):
        assert check_slippage(Decimal("75000"), Decimal("75100")) == []

    def test_exceeds_threshold(self):
        alerts = check_slippage(Decimal("75000"), Decimal("75500"), Decimal("0.003"))
        assert len(alerts) == 1
        assert alerts[0].code == "GR063"

    def test_zero_price(self):
        assert check_slippage(Decimal("0"), Decimal("75000")) == []


class TestGR064FillDelay:
    def test_no_delay(self):
        assert check_fill_delay(1000) == []

    def test_exceeded(self):
        alerts = check_fill_delay(35000)
        assert len(alerts) == 1
        assert alerts[0].code == "GR064"

    def test_custom_threshold(self):
        alerts = check_fill_delay(5000, threshold_ms=3000)
        assert len(alerts) == 1


class TestFS090AllSendsFailed:
    def test_some_sent(self):
        assert check_all_sends_failed(sent=1, failed=2) == []

    def test_all_failed(self):
        alerts = check_all_sends_failed(sent=0, failed=3)
        assert len(alerts) == 1
        assert alerts[0].code == "FS090"

    def test_none(self):
        assert check_all_sends_failed(sent=0, failed=0) == []


class TestFS091InvalidSymbol:
    def test_valid(self):
        assert check_invalid_symbol("005930") == []

    def test_empty(self):
        alerts = check_invalid_symbol("")
        assert len(alerts) == 1
        assert alerts[0].code == "FS091"

    def test_not_in_valid_set(self):
        alerts = check_invalid_symbol("INVALID", valid_symbols={"005930", "000660"})
        assert len(alerts) == 1

    def test_in_valid_set(self):
        assert check_invalid_symbol("005930", valid_symbols={"005930"}) == []


class TestFS093FillTimeout:
    def test_complete(self):
        assert check_fill_timeout(100, 100) == []

    def test_partial(self):
        alerts = check_fill_timeout(50, 100)
        assert len(alerts) == 1
        assert alerts[0].code == "FS093"


class TestFS094SlippageExceeded:
    def test_within(self):
        assert check_slippage_exceeded(Decimal("75000"), Decimal("75100")) == []

    def test_exceeded(self):
        alerts = check_slippage_exceeded(
            Decimal("75000"), Decimal("76000"), Decimal("0.005"),
        )
        assert len(alerts) == 1
        assert alerts[0].code == "FS094"

    def test_zero_price(self):
        assert check_slippage_exceeded(Decimal("0"), Decimal("75000")) == []
