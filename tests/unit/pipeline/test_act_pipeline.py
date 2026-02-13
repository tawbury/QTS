"""_act() + ExecutionPipeline 통합 단위 테스트."""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

try:
    from src.pipeline.eteda_runner import ETEDARunner
    from src.qts.core.config.config_models import UnifiedConfig
    from src.execution.pipeline import ExecutionPipeline
    from src.execution.contracts import (
        ExecutionContext,
        ExecutionResult,
        ExecutionState,
        OrderDecision,
        SplitOrder,
        SplitOrderStatus,
        SplitResult,
        SendResult,
        FillEvent,
        ExecutionAlert,
    )
    from src.provider.models.response import ExecutionResponse
    from src.provider.models.order_request import OrderSide, OrderType
    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False

pytestmark = pytest.mark.skipif(
    not _HAS_DEPS,
    reason="Pipeline dependencies not installed",
)


def _make_config(**overrides) -> UnifiedConfig:
    defaults = {
        "RUN_MODE": "PAPER",
        "LIVE_ENABLED": "0",
        "trading_enabled": "1",
        "PIPELINE_PAUSED": "0",
        "KS_ENABLED": "false",
        "FAILSAFE_ENABLED": "false",
    }
    defaults.update(overrides)
    return UnifiedConfig(config_map=defaults, metadata={})


def _make_mock_sheets_client() -> MagicMock:
    headers = [
        "Symbol", "Name", "Market", "Qty", "Avg_Price(Current_Currency)",
        "Current_Price(Current_Currency)", "Strategy", "Sector",
    ]

    async def get_sheet_data(range_name: str, max_retries: int = 3) -> List[List[Any]]:
        if "1" in range_name and "A2" not in range_name and "2:" not in range_name:
            return [headers]
        return []

    client = MagicMock()
    client.spreadsheet_id = "test-exec-pipeline-spreadsheet"
    client.get_sheet_data = AsyncMock(side_effect=get_sheet_data)
    return client


class _MockBroker:
    NAME = "mock-broker"

    def __init__(self, *, accept_all: bool = True):
        self._accept_all = accept_all

    def submit_intent(self, intent):
        from src.provider.models.response import ExecutionResponse
        return ExecutionResponse(
            intent_id=intent.intent_id,
            accepted=self._accept_all and intent.quantity > 0,
            broker=self.NAME,
            message="Mock accepted" if self._accept_all else "Mock rejected",
        )


def _make_decision(action="BUY", symbol="005930", price=75000, qty=10) -> Dict[str, Any]:
    return {
        "action": action,
        "symbol": symbol,
        "price": price,
        "qty": qty,
        "approved": True,
        "reason": "test",
        "strategy": "scalp",
    }


class TestActWithoutPipeline:
    """execution_pipeline=None 시 기존 직접 broker 호출."""

    @pytest.mark.asyncio
    async def test_act_without_pipeline(self, tmp_path):
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            broker=_MockBroker(accept_all=True),
            execution_pipeline=None,
        )
        result = await runner._act(_make_decision())
        assert result["status"] == "executed"
        assert result.get("execution_pipeline_used") is not True

    @pytest.mark.asyncio
    async def test_act_hold_skips(self, tmp_path):
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            broker=_MockBroker(),
            execution_pipeline=ExecutionPipeline(),
        )
        result = await runner._act(_make_decision(action="HOLD"))
        assert result["status"] == "skipped"


class TestActWithPipeline:
    """execution_pipeline 주입 시 6단계 파이프라인 실행."""

    @pytest.mark.asyncio
    async def test_act_with_pipeline_success(self, tmp_path):
        pipeline = ExecutionPipeline()
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            broker=_MockBroker(accept_all=True),
            execution_pipeline=pipeline,
        )
        decision = _make_decision()
        result = await runner._act(decision)
        assert result.get("execution_pipeline_used") is True
        assert result["status"] in ("executed", "failed")

    @pytest.mark.asyncio
    async def test_act_pipeline_precheck_lockdown(self, tmp_path):
        """Safety LOCKDOWN 시 PreCheck 실패 → FAILED."""
        pipeline = ExecutionPipeline()
        safety_hook = MagicMock()
        safety_hook.should_run.return_value = True
        safety_hook.pipeline_state.return_value = "LOCKDOWN"

        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            broker=_MockBroker(),
            safety_hook=safety_hook,
            execution_pipeline=pipeline,
        )
        decision = _make_decision()
        result = await runner._act(decision)
        assert result.get("execution_pipeline_used") is True
        assert result.get("pipeline_state") == "FAILED"

    @pytest.mark.asyncio
    async def test_act_pipeline_error_fallback(self, tmp_path):
        """파이프라인 예외 → fallback to 직접 broker 호출."""
        pipeline = MagicMock(spec=ExecutionPipeline)
        pipeline.run_precheck.side_effect = RuntimeError("broken pipeline")

        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            broker=_MockBroker(accept_all=True),
            execution_pipeline=pipeline,
        )
        decision = _make_decision()
        result = await runner._act(decision)
        # Fallback to direct broker
        assert result["status"] == "executed"
        assert result.get("execution_pipeline_used") is not True

    @pytest.mark.asyncio
    async def test_act_pipeline_broker_reject(self, tmp_path):
        """Broker 전부 거부 → FS090 + FAILED."""
        pipeline = ExecutionPipeline()
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            broker=_MockBroker(accept_all=False),
            execution_pipeline=pipeline,
        )
        decision = _make_decision()
        result = await runner._act(decision)
        assert result.get("execution_pipeline_used") is True
        assert result.get("pipeline_state") == "FAILED"
