"""Micro Risk Contracts 테스트."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.micro_risk.contracts import (
    ActionType,
    MAEConfig,
    MarketData,
    MicroRiskAction,
    MicroRiskAlert,
    MicroRiskConfig,
    PositionShadow,
    PriceFeed,
    SHORT_CIRCUIT_ACTIONS,
    StrategyType,
    SYNC_FIELDS,
    LOCAL_FIELDS,
    TimeInTradeConfig,
    TrailingStopConfig,
    VolatilityKillSwitchConfig,
)


class TestActionType:
    def test_all_types(self):
        assert len(ActionType) == 6

    def test_short_circuit(self):
        assert ActionType.KILL_SWITCH in SHORT_CIRCUIT_ACTIONS
        assert ActionType.FULL_EXIT in SHORT_CIRCUIT_ACTIONS
        assert ActionType.PARTIAL_EXIT not in SHORT_CIRCUIT_ACTIONS


class TestPositionShadow:
    def test_creation_defaults(self):
        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("75500"),
        )
        assert shadow.symbol == "005930"
        assert shadow.qty == 100
        assert shadow.highest_price_since_entry == Decimal("75500")
        assert shadow.lowest_price_since_entry == Decimal("75500")
        assert shadow.strategy == StrategyType.SCALP

    def test_update_extremes_high(self):
        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("75000"),
        )
        shadow.update_extremes(Decimal("76000"))
        assert shadow.highest_price_since_entry == Decimal("76000")
        assert shadow.mfe_pct > 0

    def test_update_extremes_low(self):
        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("75000"),
        )
        shadow.update_extremes(Decimal("74000"))
        assert shadow.lowest_price_since_entry == Decimal("74000")
        assert shadow.mae_pct < 0

    def test_update_pnl_long(self):
        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("76000"),
        )
        shadow.update_pnl()
        assert shadow.unrealized_pnl == Decimal("100000")  # (76000-75000)*100

    def test_update_pnl_zero_qty(self):
        shadow = PositionShadow(
            symbol="005930", qty=0,
            avg_price=Decimal("75000"), current_price=Decimal("76000"),
        )
        shadow.update_pnl()
        assert shadow.unrealized_pnl == Decimal("0")

    def test_mae_mfe_long(self):
        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("100"), current_price=Decimal("100"),
        )
        shadow.update_extremes(Decimal("105"))
        shadow.update_extremes(Decimal("97"))
        assert shadow.mae_pct == Decimal("-0.03")  # (97-100)/100
        assert shadow.mfe_pct == Decimal("0.05")   # (105-100)/100


class TestPriceFeed:
    def test_frozen(self):
        feed = PriceFeed(
            symbol="005930", price=Decimal("75000"),
            bid=Decimal("74900"), ask=Decimal("75100"),
        )
        assert feed.source == "BROKER_KIS"
        with pytest.raises(AttributeError):
            feed.price = Decimal("76000")  # type: ignore[misc]


class TestMarketData:
    def test_defaults(self):
        md = MarketData()
        assert md.vix == Decimal("20")
        assert md.realized_volatility == Decimal("0.02")


class TestMicroRiskAction:
    def test_frozen(self):
        action = MicroRiskAction(
            action_type=ActionType.FULL_EXIT,
            symbol="005930",
            payload={"qty": 100},
        )
        assert action.priority == "P0"
        with pytest.raises(AttributeError):
            action.symbol = "000660"  # type: ignore[misc]


class TestConfigs:
    def test_trailing_stop_defaults(self):
        c = TrailingStopConfig()
        assert c.activation_profit_pct == Decimal("0.01")
        assert c.ratchet_only is True

    def test_mae_defaults(self):
        c = MAEConfig()
        assert c.position_mae_threshold_pct == Decimal("0.02")

    def test_time_in_trade_get_max(self):
        c = TimeInTradeConfig()
        assert c.get_max_time(StrategyType.SCALP) == 3600
        assert c.get_max_time(StrategyType.SWING) == 604800
        assert c.get_max_time(StrategyType.PORTFOLIO) is None

    def test_volatility_defaults(self):
        c = VolatilityKillSwitchConfig()
        assert c.vix_kill_level == Decimal("40")

    def test_micro_risk_config_composites(self):
        c = MicroRiskConfig()
        assert c.loop_interval_ms == 100
        assert c.trailing_stop.ratchet_only is True


class TestSyncFields:
    def test_sync_fields(self):
        assert "qty" in SYNC_FIELDS
        assert "avg_price" in SYNC_FIELDS

    def test_local_fields(self):
        assert "trailing_stop_active" in LOCAL_FIELDS
        assert "mae_pct" in LOCAL_FIELDS

    def test_no_overlap(self):
        assert SYNC_FIELDS.isdisjoint(LOCAL_FIELDS)
