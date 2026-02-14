"""SwingStrategyEngine unit tests."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

try:
    from src.strategy.engines.swing_engine import SwingStrategyEngine
    from src.strategy.interfaces.strategy import MarketContext, ExecutionContext, Intent
    from src.strategy.contracts import SwingConfig
    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False

pytestmark = pytest.mark.skipif(
    not _HAS_DEPS,
    reason="Strategy dependencies not installed",
)


class TestSwingStrategyEngine:
    """SwingStrategyEngine 테스트."""

    def test_strategy_id(self):
        engine = SwingStrategyEngine()
        assert engine.strategy_id == "swing_main"

    def test_name(self):
        engine = SwingStrategyEngine()
        assert engine.name == "swing_trend"

    def test_is_enabled_default(self):
        engine = SwingStrategyEngine()
        assert engine.is_enabled() is True

    def test_trend_entry_buy_no_position(self):
        """포지션 없으면 trend_entry BUY Intent 생성."""
        engine = SwingStrategyEngine()
        market = MarketContext(symbol="005930", price=70000.0)
        execution = ExecutionContext(position_qty=0, cash=10_000_000.0)

        intents = engine.generate_intents((market, execution))

        assert len(intents) == 1
        assert intents[0].side == "BUY"
        assert intents[0].symbol == "005930"
        assert "[swing]" in intents[0].reason

    def test_no_signal_with_position(self):
        """포지션 보유 시 exit condition 미충족이면 신호 없음."""
        engine = SwingStrategyEngine()
        market = MarketContext(symbol="005930", price=70000.0)
        execution = ExecutionContext(position_qty=10, cash=10_000_000.0)

        intents = engine.generate_intents((market, execution))

        assert len(intents) == 0

    def test_no_signal_zero_price(self):
        """가격 0이면 market filter 실패로 신호 없음."""
        engine = SwingStrategyEngine()
        market = MarketContext(symbol="005930", price=0.0)
        execution = ExecutionContext(position_qty=0, cash=10_000_000.0)

        intents = engine.generate_intents((market, execution))

        assert len(intents) == 0

    def test_qty_calculation(self):
        """max_position_pct 기반 수량 계산."""
        engine = SwingStrategyEngine()
        engine._config.max_position_pct = 0.05  # 5%

        market = MarketContext(symbol="005930", price=70000.0)
        execution = ExecutionContext(position_qty=0, cash=10_000_000.0)

        intents = engine.generate_intents((market, execution))

        assert len(intents) == 1
        expected_qty = int(10_000_000 * 0.05 / 70000)
        assert intents[0].qty == expected_qty

    def test_invalid_snapshot(self):
        """잘못된 snapshot 형식 시 빈 목록."""
        engine = SwingStrategyEngine()
        intents = engine.generate_intents("invalid")
        assert intents == []

    @pytest.mark.asyncio
    async def test_load_config_from_repo(self):
        """Config_Swing repository에서 파라미터 로드."""
        mock_repo = AsyncMock()
        mock_repo.get_market_filters.return_value = {
            "MIN_MARKET_CAP": "5e11",
            "MIN_AVG_VOLUME": "50000",
            "SECTOR_FILTER": "IT",
        }
        mock_repo.get_strategy_parameters.return_value = {
            "TREND_PERIOD": "90",
            "ENTRY_THRESHOLD": "0.08",
            "EXIT_THRESHOLD": "0.04",
            "HOLDING_PERIOD_MIN": "5",
            "HOLDING_PERIOD_MAX": "60",
        }
        mock_repo.get_risk_management.return_value = {
            "STOP_LOSS_PCT": "0.07",
            "TAKE_PROFIT_PCT": "0.15",
            "MAX_POSITION_PCT": "0.08",
            "MAX_CONCURRENT": "3",
        }

        engine = SwingStrategyEngine(config_repo=mock_repo)
        await engine.load_config()

        assert engine._config.min_market_cap == 5e11
        assert engine._config.trend_period == 90
        assert engine._config.entry_threshold == 0.08
        assert engine._config.stop_loss_pct == 0.07
        assert engine._config.max_position_pct == 0.08
        assert engine._config.max_concurrent == 3

    @pytest.mark.asyncio
    async def test_load_config_failure_uses_defaults(self):
        """Config 로드 실패 시 기본값 유지."""
        mock_repo = AsyncMock()
        mock_repo.get_market_filters.side_effect = Exception("Sheet not found")

        engine = SwingStrategyEngine(config_repo=mock_repo)
        await engine.load_config()

        assert engine._config.min_market_cap == 1e12
        assert engine._config.trend_period == 60
