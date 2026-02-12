"""데이터 레이어 계약 테스트."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.db.contracts import (
    HealthStatus,
    LedgerEntry,
    OHLCV,
    Position,
    TickData,
)


class TestPosition:
    """Position 데이터 계약."""

    def test_create_position(self):
        pos = Position(
            symbol="005930",
            qty=Decimal("100"),
            avg_price=Decimal("75000"),
        )
        assert pos.symbol == "005930"
        assert pos.qty == Decimal("100")
        assert pos.market == ""
        assert pos.unrealized_pnl == Decimal("0")

    def test_position_frozen(self):
        pos = Position(symbol="A", qty=Decimal("1"), avg_price=Decimal("1"))
        with pytest.raises(AttributeError):
            pos.qty = Decimal("2")  # type: ignore[misc]

    def test_to_cache_dict(self):
        now = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        pos = Position(
            symbol="005930",
            qty=Decimal("100"),
            avg_price=Decimal("75000"),
            updated_at=now,
        )
        d = pos.to_cache_dict()
        assert d["symbol"] == "005930"
        assert d["qty"] == "100"
        assert d["avg_price"] == "75000"
        assert d["updated_at"] != ""

    def test_from_cache_dict_roundtrip(self):
        now = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        original = Position(
            symbol="005930",
            qty=Decimal("100"),
            avg_price=Decimal("75000"),
            market="KOSPI",
            updated_at=now,
        )
        restored = Position.from_cache_dict(original.to_cache_dict())
        assert restored.symbol == original.symbol
        assert restored.qty == original.qty
        assert restored.avg_price == original.avg_price
        assert restored.market == original.market

    def test_from_cache_dict_no_updated_at(self):
        d = {
            "symbol": "A",
            "qty": "10",
            "avg_price": "100",
            "updated_at": "",
        }
        pos = Position.from_cache_dict(d)
        assert pos.updated_at is None


class TestLedgerEntry:
    """LedgerEntry 데이터 계약."""

    def test_create_entry(self):
        entry = LedgerEntry(
            timestamp=datetime.now(timezone.utc),
            symbol="005930",
            side="BUY",
            qty=Decimal("50"),
            price=Decimal("75000"),
            amount=Decimal("3750000"),
        )
        assert entry.side == "BUY"
        assert entry.fee == Decimal("0")
        assert entry.id is None

    def test_entry_frozen(self):
        entry = LedgerEntry(
            timestamp=datetime.now(timezone.utc),
            symbol="A",
            side="SELL",
            qty=Decimal("1"),
            price=Decimal("1"),
            amount=Decimal("1"),
        )
        with pytest.raises(AttributeError):
            entry.side = "BUY"  # type: ignore[misc]


class TestOHLCV:
    """OHLCV 데이터 계약."""

    def test_create_ohlcv(self):
        ohlcv = OHLCV(
            time=datetime.now(timezone.utc),
            symbol="005930",
            open=Decimal("74000"),
            high=Decimal("76000"),
            low=Decimal("73500"),
            close=Decimal("75000"),
            volume=1000000,
        )
        assert ohlcv.high > ohlcv.low
        assert ohlcv.volume == 1000000


class TestTickData:
    """TickData 데이터 계약."""

    def test_create_tick(self):
        tick = TickData(
            time=datetime.now(timezone.utc),
            symbol="005930",
            price=Decimal("75000"),
            volume=100,
        )
        assert tick.bid is None
        assert tick.source == ""

    def test_tick_with_bid_ask(self):
        tick = TickData(
            time=datetime.now(timezone.utc),
            symbol="005930",
            price=Decimal("75050"),
            volume=100,
            bid=Decimal("75000"),
            ask=Decimal("75100"),
            source="KIS",
        )
        assert tick.bid == Decimal("75000")
        assert tick.ask == Decimal("75100")


class TestHealthStatus:
    """HealthStatus 데이터 계약."""

    def test_healthy(self):
        hs = HealthStatus(healthy=True, source="test", latency_ms=1.5)
        assert hs.healthy
        assert hs.error == ""

    def test_unhealthy(self):
        hs = HealthStatus(
            healthy=False, source="test", error="connection_refused"
        )
        assert not hs.healthy
        assert hs.error == "connection_refused"
