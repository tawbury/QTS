"""Position Shadow Manager 테스트."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.micro_risk.contracts import PositionShadow
from src.micro_risk.shadow_manager import PositionShadowManager


def _make_shadow(symbol="005930", qty=100, price=Decimal("75000")) -> PositionShadow:
    return PositionShadow(
        symbol=symbol, qty=qty,
        avg_price=price, current_price=price,
    )


class TestAddRemove:
    def test_add(self):
        mgr = PositionShadowManager()
        mgr.add_position(_make_shadow())
        assert mgr.count() == 1
        assert mgr.has_position("005930")

    def test_remove(self):
        mgr = PositionShadowManager()
        mgr.add_position(_make_shadow())
        removed = mgr.remove_position("005930")
        assert removed is not None
        assert mgr.count() == 0

    def test_remove_nonexistent(self):
        mgr = PositionShadowManager()
        assert mgr.remove_position("NONE") is None

    def test_get(self):
        mgr = PositionShadowManager()
        mgr.add_position(_make_shadow())
        s = mgr.get("005930")
        assert s is not None
        assert s.qty == 100

    def test_items(self):
        mgr = PositionShadowManager()
        mgr.add_position(_make_shadow("005930"))
        mgr.add_position(_make_shadow("000660"))
        symbols = [sym for sym, _ in mgr.items()]
        assert "005930" in symbols
        assert "000660" in symbols

    def test_symbols(self):
        mgr = PositionShadowManager()
        mgr.add_position(_make_shadow("A"))
        mgr.add_position(_make_shadow("B"))
        assert sorted(mgr.symbols()) == ["A", "B"]


class TestSync:
    def test_sync_fields(self):
        mgr = PositionShadowManager()
        mgr.add_position(_make_shadow())

        alerts = mgr.sync_from_main({
            "005930": {
                "qty": 100, "avg_price": 75000,
                "current_price": 76000,
                "unrealized_pnl": 100000,
                "unrealized_pnl_pct": 0.0133,
            },
        })

        s = mgr.get("005930")
        assert s.current_price == Decimal("76000")
        assert s.unrealized_pnl == Decimal("100000")
        assert len(alerts) == 0

    def test_sync_qty_mismatch(self):
        mgr = PositionShadowManager()
        shadow = _make_shadow()
        shadow.qty = 50  # 섀도우는 50
        mgr.add_position(shadow)

        alerts = mgr.sync_from_main({
            "005930": {"qty": 100},  # 메인은 100
        })

        s = mgr.get("005930")
        assert s.qty == 100  # 메인이 우선
        assert len(alerts) == 1
        assert alerts[0].code == "FS101"

    def test_sync_unknown_symbol(self):
        mgr = PositionShadowManager()
        mgr.add_position(_make_shadow())

        alerts = mgr.sync_from_main({"UNKNOWN": {"qty": 50}})
        assert len(alerts) == 0  # 무시


class TestStaleness:
    def test_not_stale(self):
        mgr = PositionShadowManager()
        mgr.add_position(_make_shadow())
        alerts = mgr.check_sync_staleness()
        assert len(alerts) == 0

    def test_stale(self):
        mgr = PositionShadowManager()
        shadow = _make_shadow()
        shadow.last_sync_time = datetime.now(timezone.utc) - timedelta(seconds=2)
        mgr.add_position(shadow)
        alerts = mgr.check_sync_staleness(stale_threshold_ms=1000)
        assert len(alerts) == 1
        assert alerts[0].code == "FS101"


class TestTimeUpdate:
    def test_time_in_trade(self):
        mgr = PositionShadowManager()
        shadow = _make_shadow()
        shadow.entry_time = datetime.now(timezone.utc) - timedelta(seconds=300)
        mgr.add_position(shadow)
        mgr.update_time_in_trade()
        assert shadow.time_in_trade_sec >= 299
