"""Strategy Toggle Control 단위 테스트.

Config_Scalp/Config_Swing 시트의 STRATEGY_ENABLED 토글이
ScalpStrategyEngine/SwingStrategyEngine의 is_enabled() 플래그를
올바르게 제어하는지 검증한다.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

try:
    from src.strategy.engines.scalp_engine import ScalpStrategyEngine
    from src.strategy.engines.swing_engine import SwingStrategyEngine
    from src.strategy.registry.strategy_registry import StrategyRegistry
    from src.strategy.multiplexer.strategy_multiplexer import StrategyMultiplexer
    from src.strategy.interfaces.strategy import MarketContext, ExecutionContext
    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False

pytestmark = pytest.mark.skipif(
    not _HAS_DEPS,
    reason="Strategy dependencies not installed",
)


def _make_mock_repo(strategy_enabled_value: str = "ON"):
    """STRATEGY_CONTROL 카테고리를 포함한 mock repository 생성."""
    repo = AsyncMock()

    # get_strategy_enabled는 직접 bool 반환하므로 별도 mock
    if strategy_enabled_value.upper() == "OFF":
        repo.get_strategy_enabled = AsyncMock(return_value=False)
    else:
        repo.get_strategy_enabled = AsyncMock(return_value=True)

    # 기존 config 메서드들 mock
    repo.get_golden_cross_parameters = AsyncMock(return_value={})
    repo.get_rsi_parameters = AsyncMock(return_value={})
    repo.get_bollinger_bands_parameters = AsyncMock(return_value={})
    repo.get_execution_settings = AsyncMock(return_value={})
    repo.get_timeframe_settings = AsyncMock(return_value={})
    repo.get_market_filters = AsyncMock(return_value={})
    repo.get_strategy_parameters = AsyncMock(return_value={})
    repo.get_risk_management = AsyncMock(return_value={})

    return repo


class TestStrategyToggleScalp:
    """ScalpStrategyEngine 토글 테스트."""

    @pytest.mark.asyncio
    async def test_strategy_enabled_on(self):
        """STRATEGY_ENABLED=ON → is_enabled()=True"""
        repo = _make_mock_repo("ON")
        engine = ScalpStrategyEngine(config_repo=repo)
        await engine.load_config()
        assert engine.is_enabled() is True

    @pytest.mark.asyncio
    async def test_strategy_enabled_off(self):
        """STRATEGY_ENABLED=OFF → is_enabled()=False"""
        repo = _make_mock_repo("OFF")
        engine = ScalpStrategyEngine(config_repo=repo)
        await engine.load_config()
        assert engine.is_enabled() is False

    @pytest.mark.asyncio
    async def test_strategy_enabled_default_no_repo(self):
        """config_repo=None → is_enabled()=True (기본값)"""
        engine = ScalpStrategyEngine(config_repo=None)
        await engine.load_config()
        assert engine.is_enabled() is True

    @pytest.mark.asyncio
    async def test_strategy_enabled_repo_exception(self):
        """get_strategy_enabled 예외 → is_enabled()=True (fail-open)"""
        repo = AsyncMock()
        repo.get_strategy_enabled = AsyncMock(side_effect=Exception("API error"))
        engine = ScalpStrategyEngine(config_repo=repo)
        await engine.load_config()
        assert engine.is_enabled() is True


class TestStrategyToggleRepoLogic:
    """Repository get_strategy_enabled() 로직 테스트 (값 파싱)."""

    @pytest.mark.asyncio
    async def test_invalid_value_defaults_on(self):
        """잘못된 값(MAYBE 등) -> ON으로 처리"""
        repo = AsyncMock()
        repo.get_strategy_enabled = AsyncMock(return_value=True)  # 'MAYBE' != 'OFF' -> True
        engine = ScalpStrategyEngine(config_repo=repo)
        await engine.load_config()
        assert engine.is_enabled() is True

    @pytest.mark.asyncio
    async def test_off_case_insensitive(self):
        """OFF 대소문자 무관 처리 (Repository에서 .upper() 적용)"""
        repo = AsyncMock()
        repo.get_strategy_enabled = AsyncMock(return_value=False)  # 'off'.upper() == 'OFF' -> False
        engine = ScalpStrategyEngine(config_repo=repo)
        await engine.load_config()
        assert engine.is_enabled() is False


class TestStrategyToggleSwing:
    """SwingStrategyEngine 토글 테스트."""

    @pytest.mark.asyncio
    async def test_strategy_enabled_on(self):
        """STRATEGY_ENABLED=ON → is_enabled()=True"""
        repo = _make_mock_repo("ON")
        engine = SwingStrategyEngine(config_repo=repo)
        await engine.load_config()
        assert engine.is_enabled() is True

    @pytest.mark.asyncio
    async def test_strategy_enabled_off(self):
        """STRATEGY_ENABLED=OFF → is_enabled()=False"""
        repo = _make_mock_repo("OFF")
        engine = SwingStrategyEngine(config_repo=repo)
        await engine.load_config()
        assert engine.is_enabled() is False


class TestStrategyToggleMultiplexer:
    """Multiplexer가 engine disabled를 올바르게 처리하는지 검증."""

    @pytest.mark.asyncio
    async def test_multiplexer_skips_disabled_engine(self):
        """disabled engine은 active_strategies()에서 제외되어 Multiplexer에서 스킵"""
        repo = _make_mock_repo("OFF")

        scalp = ScalpStrategyEngine(config_repo=repo)
        await scalp.load_config()

        registry = StrategyRegistry()
        registry.register(scalp)
        mux = StrategyMultiplexer(registry)

        market = MarketContext(symbol="005930", price=70000.0)
        exec_ctx = ExecutionContext(position_qty=0, cash=10_000_000)

        result = mux.collect(snapshot=(market, exec_ctx))
        assert len(result) == 0  # disabled이므로 신호 없음

    @pytest.mark.asyncio
    async def test_both_controls_and_condition(self):
        """시트 ON + Multiplexer state disabled → 스킵 (AND 조건)"""
        repo = _make_mock_repo("ON")

        scalp = ScalpStrategyEngine(config_repo=repo)
        await scalp.load_config()
        assert scalp.is_enabled() is True  # 시트에서는 ON

        registry = StrategyRegistry()
        registry.register(scalp)
        mux = StrategyMultiplexer(registry)

        # Operating State에서 scalp 비활성화
        mux.set_engine_state(scalp_enabled=False, swing_enabled=True)

        market = MarketContext(symbol="005930", price=70000.0)
        exec_ctx = ExecutionContext(position_qty=0, cash=10_000_000)

        result = mux.collect(snapshot=(market, exec_ctx))
        assert len(result) == 0  # Operating State에서 차단
