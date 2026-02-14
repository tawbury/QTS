"""ScalpStrategyEngine unit tests."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

try:
    from src.strategy.engines.scalp_engine import ScalpStrategyEngine
    from src.strategy.interfaces.strategy import MarketContext, ExecutionContext, Intent
    from src.strategy.contracts import ScalpConfig
    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False

pytestmark = pytest.mark.skipif(
    not _HAS_DEPS,
    reason="Strategy dependencies not installed",
)


class TestScalpStrategyEngine:
    """ScalpStrategyEngine 테스트."""

    def test_strategy_id(self):
        engine = ScalpStrategyEngine()
        assert engine.strategy_id == "scalp_main"

    def test_name(self):
        engine = ScalpStrategyEngine()
        assert engine.name == "scalp_golden_cross"

    def test_is_enabled_default(self):
        engine = ScalpStrategyEngine()
        assert engine.is_enabled() is True

    def test_golden_cross_buy_no_position(self):
        """포지션 없으면 BUY Intent 생성."""
        engine = ScalpStrategyEngine()
        market = MarketContext(symbol="005930", price=70000.0)
        execution = ExecutionContext(position_qty=0, cash=10_000_000.0)

        intents = engine.generate_intents((market, execution))

        assert len(intents) == 1
        assert intents[0].side == "BUY"
        assert intents[0].symbol == "005930"
        assert "[scalp]" in intents[0].reason

    def test_no_signal_with_position(self):
        """포지션 있으면 신호 없음."""
        engine = ScalpStrategyEngine()
        market = MarketContext(symbol="005930", price=70000.0)
        execution = ExecutionContext(position_qty=10, cash=10_000_000.0)

        intents = engine.generate_intents((market, execution))

        assert len(intents) == 0

    def test_no_signal_zero_price(self):
        """가격 0이면 신호 없음."""
        engine = ScalpStrategyEngine()
        market = MarketContext(symbol="005930", price=0.0)
        execution = ExecutionContext(position_qty=0, cash=10_000_000.0)

        intents = engine.generate_intents((market, execution))

        assert len(intents) == 0

    def test_qty_calculation(self):
        """max_position_pct 기반 수량 계산."""
        engine = ScalpStrategyEngine()
        engine._config.max_position_pct = 0.01  # 1%

        market = MarketContext(symbol="005930", price=70000.0)
        execution = ExecutionContext(position_qty=0, cash=10_000_000.0)

        intents = engine.generate_intents((market, execution))

        assert len(intents) == 1
        expected_qty = int(10_000_000 * 0.01 / 70000)
        assert intents[0].qty == expected_qty

    def test_invalid_snapshot(self):
        """잘못된 snapshot 형식 시 빈 목록."""
        engine = ScalpStrategyEngine()
        intents = engine.generate_intents("invalid")
        assert intents == []

    @pytest.mark.asyncio
    async def test_load_config_from_repo(self):
        """Config_Scalp repository에서 파라미터 로드."""
        mock_repo = AsyncMock()
        mock_repo.get_golden_cross_parameters.return_value = {
            "SHORT_MA_PERIOD": "3",
            "LONG_MA_PERIOD": "15",
            "SIGNAL_THRESHOLD": "0.02",
        }
        mock_repo.get_rsi_parameters.return_value = {
            "RSI_PERIOD": "10",
            "RSI_OVERSOLD": "25.0",
            "RSI_OVERBOUGHT": "75.0",
        }
        mock_repo.get_bollinger_bands_parameters.return_value = {
            "BB_PERIOD": "15",
            "BB_STD_DEV": "1.5",
        }
        mock_repo.get_execution_settings.return_value = {
            "MAX_POSITION_PCT": "0.02",
            "SPLIT_STRATEGY": "VWAP",
            "MAX_SLIPPAGE_PCT": "0.005",
        }
        mock_repo.get_timeframe_settings.return_value = {
            "PRIMARY_TIMEFRAME": "3m",
            "ANALYSIS_TIMEFRAME": "15m",
        }

        engine = ScalpStrategyEngine(config_repo=mock_repo)
        await engine.load_config()

        assert engine._config.short_ma_period == 3
        assert engine._config.long_ma_period == 15
        assert engine._config.rsi_period == 10
        assert engine._config.bb_period == 15
        assert engine._config.max_position_pct == 0.02
        assert engine._config.primary_timeframe == "3m"

    @pytest.mark.asyncio
    async def test_load_config_failure_uses_defaults(self):
        """Config 로드 실패 시 기본값 유지."""
        mock_repo = AsyncMock()
        mock_repo.get_golden_cross_parameters.side_effect = Exception("Sheet not found")

        engine = ScalpStrategyEngine(config_repo=mock_repo)
        await engine.load_config()

        assert engine._config.short_ma_period == 5
        assert engine._config.long_ma_period == 20

    @pytest.mark.asyncio
    async def test_load_config_no_repo(self):
        """config_repo 없을 때 load_config 안전."""
        engine = ScalpStrategyEngine()
        await engine.load_config()
        assert engine._config.short_ma_period == 5
