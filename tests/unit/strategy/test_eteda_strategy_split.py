"""ETEDA pipeline strategy split integration tests."""
from __future__ import annotations

import pytest
from decimal import Decimal
from unittest.mock import MagicMock

try:
    from src.pipeline.eteda_runner import ETEDARunner
    from src.strategy.engines.scalp_engine import ScalpStrategyEngine
    from src.strategy.engines.swing_engine import SwingStrategyEngine
    from src.strategy.contracts import get_strategy_tag
    from src.capital.contracts import PoolId, CapitalPoolContract
    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False

pytestmark = pytest.mark.skipif(
    not _HAS_DEPS,
    reason="Pipeline dependencies not installed",
)


def _make_runner(**config_overrides):
    defaults = {
        "RUN_MODE": "PAPER",
        "LIVE_ENABLED": "0",
        "trading_enabled": "1",
        "PIPELINE_PAUSED": "0",
        "KS_ENABLED": "false",
        "FAILSAFE_ENABLED": "false",
        "OPERATING_STATE": "BALANCED",
    }
    defaults.update(config_overrides)

    from src.qts.core.config.config_models import UnifiedConfig
    config = UnifiedConfig(config_map=defaults, metadata={})

    mock_client = MagicMock()
    mock_client.spreadsheet_id = "test_spreadsheet"
    mock_client.get_sheet_data = MagicMock(return_value=[])

    return ETEDARunner(config, sheets_client=mock_client)


class TestCapitalRoutingScalp:
    """Scalp 신호 → SCALP 풀 갱신."""

    def test_scalp_buy_updates_scalp_pool(self):
        runner = _make_runner()

        scalp_pool = CapitalPoolContract(
            pool_id=PoolId.SCALP, total_capital=Decimal("10000000"), invested_capital=Decimal("0"))
        swing_pool = CapitalPoolContract(
            pool_id=PoolId.SWING, total_capital=Decimal("5000000"), invested_capital=Decimal("0"))
        pool_states = {PoolId.SCALP: scalp_pool, PoolId.SWING: swing_pool}

        decision = {"action": "BUY", "price": 70000, "qty": 10, "strategy": "scalp"}
        act_result = {"status": "executed"}

        runner._update_capital_after_act(pool_states, decision, act_result)

        assert scalp_pool.invested_capital == Decimal("700000")
        assert swing_pool.invested_capital == Decimal("0")


class TestCapitalRoutingSwing:
    """Swing 신호 → SWING 풀 갱신."""

    def test_swing_buy_updates_swing_pool(self):
        runner = _make_runner()

        scalp_pool = CapitalPoolContract(
            pool_id=PoolId.SCALP, total_capital=Decimal("10000000"), invested_capital=Decimal("0"))
        swing_pool = CapitalPoolContract(
            pool_id=PoolId.SWING, total_capital=Decimal("5000000"), invested_capital=Decimal("0"))
        pool_states = {PoolId.SCALP: scalp_pool, PoolId.SWING: swing_pool}

        decision = {"action": "BUY", "price": 70000, "qty": 10, "strategy": "swing"}
        act_result = {"status": "executed"}

        runner._update_capital_after_act(pool_states, decision, act_result)

        assert swing_pool.invested_capital == Decimal("700000")
        assert scalp_pool.invested_capital == Decimal("0")

    def test_swing_sell_reduces_swing_pool(self):
        runner = _make_runner()

        swing_pool = CapitalPoolContract(
            pool_id=PoolId.SWING, total_capital=Decimal("5000000"), invested_capital=Decimal("700000"))
        scalp_pool = CapitalPoolContract(
            pool_id=PoolId.SCALP, total_capital=Decimal("10000000"))
        pool_states = {PoolId.SCALP: scalp_pool, PoolId.SWING: swing_pool}

        decision = {"action": "SELL", "price": 70000, "qty": 10, "strategy": "swing"}
        act_result = {"status": "executed"}

        runner._update_capital_after_act(pool_states, decision, act_result)

        assert swing_pool.invested_capital == Decimal("0")


class TestCapitalRoutingDefault:
    """strategy 태그 없으면 SCALP 기본 라우팅."""

    def test_no_strategy_tag_defaults_to_scalp(self):
        runner = _make_runner()

        scalp_pool = CapitalPoolContract(
            pool_id=PoolId.SCALP, total_capital=Decimal("10000000"), invested_capital=Decimal("0"))
        swing_pool = CapitalPoolContract(
            pool_id=PoolId.SWING, total_capital=Decimal("5000000"))
        pool_states = {PoolId.SCALP: scalp_pool, PoolId.SWING: swing_pool}

        decision = {"action": "BUY", "price": 70000, "qty": 10}  # strategy 없음
        act_result = {"status": "executed"}

        runner._update_capital_after_act(pool_states, decision, act_result)

        assert scalp_pool.invested_capital == Decimal("700000")


class TestDecideRiskMultiplier:
    """_decide에서 전략별 Risk 승수 적용."""

    def test_scalp_tight_risk(self):
        runner = _make_runner()

        signal = {
            "symbol": "005930", "action": "BUY", "qty": 10,
            "price": 70000, "strategy": "scalp", "operating_state": "BALANCED",
        }

        decision = runner._decide(signal)

        # BALANCED risk_tolerance = 1.0 * 0.8 = 0.8
        assert decision["risk_tolerance_multiplier"] == pytest.approx(0.8)

    def test_swing_relaxed_risk(self):
        runner = _make_runner()

        signal = {
            "symbol": "005930", "action": "BUY", "qty": 10,
            "price": 70000, "strategy": "swing", "operating_state": "BALANCED",
        }

        decision = runner._decide(signal)

        # BALANCED risk_tolerance = 1.0 * 1.2 = 1.2
        assert decision["risk_tolerance_multiplier"] == pytest.approx(1.2)


class TestMultiplexerRegistration:
    """ETEDARunner에 엔진 등록 후 Multiplexer 사용."""

    def test_register_and_evaluate(self):
        runner = _make_runner()

        scalp = ScalpStrategyEngine()
        swing = SwingStrategyEngine()
        runner._strategy_registry.register(scalp)
        runner._strategy_registry.register(swing)

        data = {
            "market": {"symbol": "005930", "price": 70000.0},
            "position": {"quantity": 0},
        }

        signal = runner._evaluate(data)

        assert signal["action"] in ("BUY", "HOLD")
        assert "operating_state" in signal
        if signal["action"] == "BUY":
            assert signal.get("strategy") in ("scalp", "swing")

    def test_no_registered_engines_fallback(self):
        """등록된 엔진 없으면 기존 StrategyEngine fallback."""
        runner = _make_runner(VTS_TARGET_SYMBOLS="005930")

        data = {
            "market": {"symbol": "005930", "price": 70000.0},
            "position": {"quantity": 0},
        }

        signal = runner._evaluate(data)

        assert "operating_state" in signal

    def test_defensive_blocks_scalp(self):
        """DEFENSIVE 상태에서 Scalp 엔진 비활성화."""
        runner = _make_runner(OPERATING_STATE="DEFENSIVE")

        scalp = ScalpStrategyEngine()
        swing = SwingStrategyEngine()
        runner._strategy_registry.register(scalp)
        runner._strategy_registry.register(swing)

        data = {
            "market": {"symbol": "005930", "price": 70000.0},
            "position": {"quantity": 0},
        }

        signal = runner._evaluate(data)

        # DEFENSIVE에서 scalp 비활성화 → swing만 가능 또는 HOLD
        if signal["action"] != "HOLD":
            assert signal.get("strategy") == "swing"
