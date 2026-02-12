"""Micro Risk Guardrails 테스트."""
from decimal import Decimal

import pytest

from src.micro_risk.contracts import (
    MicroRiskConfig,
    PositionShadow,
    StrategyType,
)
from src.micro_risk.guardrails import (
    check_emergency_exit,
    check_emergency_order_failure,
    check_eteda_suspend,
    check_kill_switch,
    check_loop_error,
    check_mae_approaching,
    check_price_feed_interrupted,
    check_sync_delay,
    check_time_warning,
    check_trailing_stop_adjustment_frequency,
    check_volatility_rising,
    run_micro_risk_guardrails,
)


class TestFS100LoopError:
    def test_no_error(self):
        assert check_loop_error(None) == []

    def test_with_error(self):
        alerts = check_loop_error(ValueError("test"))
        assert len(alerts) == 1
        assert alerts[0].code == "FS100"
        assert alerts[0].severity == "CRITICAL"


class TestFS101SyncDelay:
    def test_within_threshold(self):
        assert check_sync_delay(500) == []

    def test_exceeded(self):
        alerts = check_sync_delay(1500)
        assert len(alerts) == 1
        assert alerts[0].code == "FS101"

    def test_critical_severity(self):
        alerts = check_sync_delay(2500, threshold_ms=1000)
        assert alerts[0].severity == "CRITICAL"


class TestFS102EmergencyExit:
    def test_alert(self):
        alerts = check_emergency_exit("005930", 100, "MAE")
        assert len(alerts) == 1
        assert alerts[0].code == "FS102"


class TestFS103ETEDASuspend:
    def test_alert(self):
        alerts = check_eteda_suspend("KILL_SWITCH")
        assert len(alerts) == 1
        assert alerts[0].code == "FS103"


class TestFS104KillSwitch:
    def test_alert(self):
        alerts = check_kill_switch("VOLATILITY")
        assert len(alerts) == 1
        assert alerts[0].code == "FS104"


class TestFS105PriceFeed:
    def test_not_stale(self):
        assert check_price_feed_interrupted("005930", False) == []

    def test_stale(self):
        alerts = check_price_feed_interrupted("005930", True)
        assert len(alerts) == 1
        assert alerts[0].code == "FS105"


class TestGR070TrailingStopFrequency:
    def test_within_limit(self):
        assert check_trailing_stop_adjustment_frequency(30) == []

    def test_exceeded(self):
        alerts = check_trailing_stop_adjustment_frequency(70)
        assert len(alerts) == 1
        assert alerts[0].code == "GR070"


class TestGR071MAEApproaching:
    def test_not_approaching(self):
        assert check_mae_approaching(Decimal("-0.005"), Decimal("0.02")) == []

    def test_approaching(self):
        alerts = check_mae_approaching(Decimal("-0.017"), Decimal("0.02"))
        assert len(alerts) == 1
        assert alerts[0].code == "GR071"


class TestGR072TimeWarning:
    def test_no_warning(self):
        assert check_time_warning(1000, 3600) == []

    def test_warning(self):
        alerts = check_time_warning(3000, 3600)
        assert len(alerts) == 1
        assert alerts[0].code == "GR072"


class TestGR073VolatilityRising:
    def test_low_vix(self):
        assert check_volatility_rising(Decimal("20")) == []

    def test_high_vix(self):
        alerts = check_volatility_rising(Decimal("27"))
        assert len(alerts) == 1
        assert alerts[0].code == "GR073"


class TestGR074EmergencyOrderFailure:
    def test_success(self):
        assert check_emergency_order_failure(True, "005930") == []

    def test_failure(self):
        alerts = check_emergency_order_failure(False, "005930")
        assert len(alerts) == 1
        assert alerts[0].code == "GR074"


class TestCombinedRunner:
    def test_multiple_alerts(self):
        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("75000"),
        )
        shadow.mae_pct = Decimal("-0.017")
        shadow.time_in_trade_sec = 3000
        config = MicroRiskConfig()
        alerts = run_micro_risk_guardrails(
            shadow, config, market_vix=Decimal("27"),
        )
        codes = {a.code for a in alerts}
        assert "GR071" in codes  # MAE approaching
        assert "GR072" in codes  # Time warning
        assert "GR073" in codes  # Volatility rising

    def test_no_time_warning_for_portfolio(self):
        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("75000"),
        )
        shadow.strategy = StrategyType.PORTFOLIO
        shadow.time_in_trade_sec = 999999
        config = MicroRiskConfig()
        alerts = run_micro_risk_guardrails(shadow, config)
        codes = {a.code for a in alerts}
        assert "GR072" not in codes
