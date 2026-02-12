"""Price Feed Handler 테스트."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.micro_risk.contracts import PositionShadow, PriceFeed
from src.micro_risk.price_handler import PriceFeedHandler


def _make_feed(symbol="005930", price=Decimal("75000")) -> PriceFeed:
    return PriceFeed(
        symbol=symbol, price=price,
        bid=price - Decimal("100"), ask=price + Decimal("100"),
    )


class TestOnPriceTick:
    def test_basic_tick(self):
        h = PriceFeedHandler()
        alerts = h.on_price_tick(_make_feed())
        assert len(alerts) == 0
        assert h.has_data("005930")

    def test_updates_shadow(self):
        h = PriceFeedHandler()
        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("75000"),
        )
        h.on_price_tick(_make_feed(price=Decimal("76000")), shadow)
        assert shadow.current_price == Decimal("76000")

    def test_anomaly_detection(self):
        h = PriceFeedHandler()
        h.on_price_tick(_make_feed(price=Decimal("75000")))
        # 10% 급등
        alerts = h.on_price_tick(_make_feed(price=Decimal("82500")))
        assert len(alerts) == 1
        assert alerts[0].code == "FS105"

    def test_no_anomaly_small_change(self):
        h = PriceFeedHandler()
        h.on_price_tick(_make_feed(price=Decimal("75000")))
        alerts = h.on_price_tick(_make_feed(price=Decimal("75100")))
        assert len(alerts) == 0


class TestBuffer:
    def test_buffer_size(self):
        h = PriceFeedHandler(buffer_size=5)
        for i in range(10):
            h.on_price_tick(_make_feed(price=Decimal(str(75000 + i * 100))))
        buf = h.get_buffer("005930")
        assert len(buf) == 5

    def test_get_latest(self):
        h = PriceFeedHandler()
        h.on_price_tick(_make_feed(price=Decimal("75000")))
        h.on_price_tick(_make_feed(price=Decimal("76000")))
        latest = h.get_latest("005930")
        assert latest is not None
        assert latest.price == Decimal("76000")

    def test_get_latest_empty(self):
        h = PriceFeedHandler()
        assert h.get_latest("005930") is None


class TestStale:
    def test_no_data_is_stale(self):
        h = PriceFeedHandler()
        assert h.is_price_stale("005930") is True

    def test_fresh_data(self):
        h = PriceFeedHandler()
        h.on_price_tick(_make_feed())
        assert h.is_price_stale("005930", threshold_ms=1000) is False


class TestAnomaly:
    def test_first_tick_no_anomaly(self):
        h = PriceFeedHandler()
        assert h.detect_anomaly("005930", Decimal("75000")) is False

    def test_large_change(self):
        h = PriceFeedHandler()
        h.on_price_tick(_make_feed(price=Decimal("75000")))
        assert h.detect_anomaly("005930", Decimal("82500")) is True

    def test_zero_prev_price(self):
        h = PriceFeedHandler()
        h.on_price_tick(_make_feed(price=Decimal("0")))
        assert h.detect_anomaly("005930", Decimal("75000")) is False


class TestClear:
    def test_clear_all(self):
        h = PriceFeedHandler()
        h.on_price_tick(_make_feed())
        h.clear()
        assert not h.has_data("005930")

    def test_clear_symbol(self):
        h = PriceFeedHandler()
        h.on_price_tick(_make_feed("A"))
        h.on_price_tick(_make_feed("B"))
        h.clear("A")
        assert not h.has_data("A")
        assert h.has_data("B")
