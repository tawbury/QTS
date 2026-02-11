"""
src/qts/core/ 단위 테스트.

테스트 대상:
- AppContext: 전역 런타임 컨텍스트
- ExecutionMode / PipelineMode / TradingMode
- decide_execution_mode: LIVE 거래 허용 결정
- pipeline_to_trading_mode / trading_to_pipeline_mode
"""
import pytest
from src.qts.core.app_context import AppContext
from src.qts.core.config.execution_mode import (
    PipelineMode,
    TradingMode,
    ExecutionMode,
    LiveGateDecision,
    decide_execution_mode,
    pipeline_to_trading_mode,
    trading_to_pipeline_mode,
)


class TestAppContext:
    """AppContext 테스트."""

    def test_default_values(self):
        ctx = AppContext()
        assert ctx.runtime_flags == {}
        assert ctx.config_snapshot == {}

    def test_with_flags(self):
        ctx = AppContext(runtime_flags={"debug": True})
        assert ctx.runtime_flags["debug"] is True

    def test_with_config_snapshot(self):
        ctx = AppContext(config_snapshot={"key": "value"})
        assert ctx.config_snapshot["key"] == "value"


class TestPipelineMode:
    """PipelineMode 열거형 테스트."""

    def test_values(self):
        assert PipelineMode.VIRTUAL.value == "VIRTUAL"
        assert PipelineMode.SIM.value == "SIM"
        assert PipelineMode.REAL.value == "REAL"

    def test_is_str_enum(self):
        assert isinstance(PipelineMode.VIRTUAL, str)


class TestTradingMode:
    """TradingMode 열거형 테스트."""

    def test_values(self):
        assert TradingMode.PAPER.value == "PAPER"
        assert TradingMode.LIVE.value == "LIVE"

    def test_execution_mode_alias(self):
        assert ExecutionMode is TradingMode


class TestPipelineToTradingMode:
    """pipeline_to_trading_mode 변환 테스트."""

    def test_virtual_returns_none(self):
        assert pipeline_to_trading_mode(PipelineMode.VIRTUAL) is None

    def test_sim_returns_paper(self):
        assert pipeline_to_trading_mode(PipelineMode.SIM) == TradingMode.PAPER

    def test_real_returns_live(self):
        assert pipeline_to_trading_mode(PipelineMode.REAL) == TradingMode.LIVE


class TestTradingToPipelineMode:
    """trading_to_pipeline_mode 변환 테스트."""

    def test_paper_returns_sim(self):
        assert trading_to_pipeline_mode(TradingMode.PAPER) == PipelineMode.SIM

    def test_live_returns_real(self):
        assert trading_to_pipeline_mode(TradingMode.LIVE) == PipelineMode.REAL


class TestDecideExecutionMode:
    """decide_execution_mode 함수 테스트."""

    def test_default_is_paper(self):
        result = decide_execution_mode(None, None, None)
        assert result.mode == ExecutionMode.PAPER
        assert result.live_allowed is False
        assert result.reason == "mode_not_live"

    def test_mode_not_live(self):
        result = decide_execution_mode("PAPER", "true", "I_UNDERSTAND_LIVE_TRADING")
        assert result.live_allowed is False
        assert result.reason == "mode_not_live"

    def test_live_enabled_false(self):
        result = decide_execution_mode("LIVE", "false", "I_UNDERSTAND_LIVE_TRADING")
        assert result.mode == ExecutionMode.LIVE
        assert result.live_allowed is False
        assert result.reason == "live_enabled_false"

    def test_ack_missing(self):
        result = decide_execution_mode("LIVE", "true", None)
        assert result.live_allowed is False
        assert result.reason == "ack_missing_or_invalid"

    def test_ack_invalid(self):
        result = decide_execution_mode("LIVE", "true", "wrong_ack")
        assert result.live_allowed is False
        assert result.reason == "ack_missing_or_invalid"

    def test_all_conditions_met(self):
        result = decide_execution_mode("LIVE", "true", "I_UNDERSTAND_LIVE_TRADING")
        assert result.mode == ExecutionMode.LIVE
        assert result.live_allowed is True
        assert result.reason == "live_allowed"

    def test_case_insensitive_mode(self):
        result = decide_execution_mode("live", "1", "I_UNDERSTAND_LIVE_TRADING")
        assert result.live_allowed is True

    @pytest.mark.parametrize("enabled", ["1", "true", "yes", "on", "y"])
    def test_truthy_live_enabled(self, enabled):
        result = decide_execution_mode("LIVE", enabled, "I_UNDERSTAND_LIVE_TRADING")
        assert result.live_allowed is True

    def test_live_gate_decision_is_frozen(self):
        decision = LiveGateDecision(mode=ExecutionMode.PAPER, live_allowed=False, reason="test")
        assert decision.mode == ExecutionMode.PAPER
