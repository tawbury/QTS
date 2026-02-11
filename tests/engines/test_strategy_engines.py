"""
src/strategy/engines/ 단위 테스트.

테스트 대상:
- BaseEngine: 엔진 기본 클래스 (EngineState, EngineMetrics, 이벤트, 상태 관리)
- StrategyEngine: 전략 엔진 (초기화, 시작/중지, calculate_signal)
"""
import pytest
import asyncio
from unittest.mock import AsyncMock

from src.qts.core.config.config_models import UnifiedConfig
from src.strategy.engines.base_engine import BaseEngine, EngineState, EngineMetrics
from src.strategy.engines.strategy_engine import StrategyEngine


# --------------------------------------------------
# Fixture: 최소 UnifiedConfig
# --------------------------------------------------

@pytest.fixture
def minimal_config():
    """테스트용 최소 UnifiedConfig."""
    return UnifiedConfig(
        config_map={
            "BASE_EQUITY": "1000000",
            "INTERVAL_MS": "1000",
            "RUN_MODE": "VIRTUAL",
        },
        metadata={"source": "test"},
    )


# --------------------------------------------------
# EngineState / EngineMetrics 데이터클래스 테스트
# --------------------------------------------------

class TestEngineState:
    """EngineState 데이터클래스 테스트."""

    def test_defaults(self):
        state = EngineState()
        assert state.is_running is False
        assert state.last_updated is None
        assert state.error_count == 0
        assert state.last_error is None

    def test_custom_values(self):
        state = EngineState(is_running=True, error_count=5, last_error="timeout")
        assert state.is_running is True
        assert state.error_count == 5
        assert state.last_error == "timeout"


class TestEngineMetrics:
    """EngineMetrics 데이터클래스 테스트."""

    def test_defaults(self):
        metrics = EngineMetrics()
        assert metrics.total_operations == 0
        assert metrics.success_operations == 0
        assert metrics.error_operations == 0
        assert metrics.average_execution_time == 0.0
        assert metrics.last_execution_time is None


# --------------------------------------------------
# BaseEngine 테스트 (StrategyEngine을 concrete 구현으로 사용)
# --------------------------------------------------

class TestBaseEngineViaStrategyEngine:
    """BaseEngine 공통 기능 테스트 (StrategyEngine 사용)."""

    def test_initialization(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        assert engine.config is minimal_config
        assert engine.state.is_running is False
        assert engine.state.error_count == 0
        assert engine.metrics.total_operations == 0

    def test_register_event_callback(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        callback = AsyncMock()
        engine.register_event_callback("test_event", callback)
        assert "test_event" in engine._event_callbacks
        assert callback in engine._event_callbacks["test_event"]

    def test_unregister_event_callback(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        callback = AsyncMock()
        engine.register_event_callback("test_event", callback)
        engine.unregister_event_callback("test_event", callback)
        assert len(engine._event_callbacks["test_event"]) == 0

    def test_unregister_nonexistent_callback(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        callback = AsyncMock()
        # 등록하지 않은 콜백 해제 시도 → 에러 없음
        engine.unregister_event_callback("no_event", callback)

    def test_update_metrics_success(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        engine._update_metrics(0.5, success=True)
        assert engine.metrics.total_operations == 1
        assert engine.metrics.success_operations == 1
        assert engine.metrics.error_operations == 0
        assert engine.metrics.last_execution_time == 0.5

    def test_update_metrics_failure(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        engine._update_metrics(0.3, success=False)
        assert engine.metrics.total_operations == 1
        assert engine.metrics.success_operations == 0
        assert engine.metrics.error_operations == 1
        assert engine.state.error_count == 1

    def test_update_state(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        engine._update_state(is_running=True)
        assert engine.state.is_running is True
        assert engine.state.last_updated is not None

    def test_update_state_with_error(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        engine._update_state(is_running=False, error="connection failed")
        assert engine.state.last_error == "connection failed"

    def test_state_kind_ok(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        assert engine._state_kind() == "OK"

    def test_state_kind_warning(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        engine.state.error_count = 1
        assert engine._state_kind() == "WARNING"

    def test_state_kind_fault(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        engine.state.error_count = 10
        assert engine._state_kind() == "FAULT"


# --------------------------------------------------
# StrategyEngine 비동기 테스트
# --------------------------------------------------

class TestStrategyEngine:
    """StrategyEngine 테스트."""

    @pytest.mark.asyncio
    async def test_initialize(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        result = await engine.initialize()
        assert result is True
        assert engine.state.is_running is False

    @pytest.mark.asyncio
    async def test_start(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        result = await engine.start()
        assert result is True
        assert engine.state.is_running is True

    @pytest.mark.asyncio
    async def test_stop(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        await engine.start()
        result = await engine.stop()
        assert result is True
        assert engine.state.is_running is False

    @pytest.mark.asyncio
    async def test_execute_calculate_signal(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        result = await engine.execute({
            "operation": "calculate_signal",
            "market_data": {"symbol": "005930", "price": 70000},
        })
        assert result["success"] is True
        assert result["data"]["symbol"] == "005930"
        assert result["data"]["action"] == "HOLD"
        assert "execution_time" in result

    @pytest.mark.asyncio
    async def test_execute_with_dict_price(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        result = await engine.execute({
            "operation": "calculate_signal",
            "market_data": {"symbol": "005930", "price": {"close": 70000}},
        })
        assert result["success"] is True
        assert result["data"]["price"] == 70000

    @pytest.mark.asyncio
    async def test_execute_with_position_data(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        result = await engine.execute({
            "operation": "calculate_signal",
            "market_data": {"symbol": "005930", "price": 70000},
            "position_data": {"quantity": 10},
        })
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_unknown_operation(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        result = await engine.execute({"operation": "unknown_op"})
        assert result["success"] is False
        assert "Unknown operation" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_no_operation(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        result = await engine.execute({})
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_updates_metrics(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        await engine.execute({
            "operation": "calculate_signal",
            "market_data": {"symbol": "005930", "price": 70000},
        })
        assert engine.metrics.total_operations == 1
        assert engine.metrics.success_operations == 1

    @pytest.mark.asyncio
    async def test_get_status(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        await engine.start()
        status = await engine.get_status()
        assert status["engine_type"] == "StrategyEngine"
        assert status["state_kind"] == "OK"
        assert status["state"]["is_running"] is True
        assert "metrics" in status

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        health = await engine.health_check()
        assert health["status"] == "healthy"
        assert health["engine"] == "StrategyEngine"
        assert health["state_kind"] == "OK"

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        engine.state.error_count = 15
        health = await engine.health_check()
        assert health["status"] == "unhealthy"
        assert health["state_kind"] == "FAULT"

    def test_calculate_signal_hold_default(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        signal = engine.calculate_signal(
            {"symbol": "005930", "price": 70000},
            {"quantity": 10},
        )
        assert signal["action"] == "HOLD"
        assert signal["symbol"] == "005930"
        assert signal["qty"] == 0

    def test_calculate_signal_no_position(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        signal = engine.calculate_signal(
            {"symbol": "005930", "price": 70000},
            None,
        )
        assert signal["action"] == "HOLD"

    def test_calculate_signal_empty_market_data(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        signal = engine.calculate_signal({}, {})
        assert signal["action"] == "HOLD"
        assert signal["symbol"] is None
        assert signal["price"] == 0.0

    @pytest.mark.asyncio
    async def test_emit_event(self, minimal_config):
        engine = StrategyEngine(minimal_config)
        received = []
        callback = AsyncMock(side_effect=lambda data: received.append(data))
        engine.register_event_callback("test", callback)
        await engine._emit_event("test", {"key": "value"})
        callback.assert_called_once_with({"key": "value"})
