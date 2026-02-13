"""Scalp Execution Pipeline ↔ ETEDA 통합 테스트.

NOTE: gspread 의존성이 필요합니다 (ETEDARunner → GoogleSheetsClient import chain).
"""
from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

try:
    from src.pipeline.eteda_runner import ETEDARunner
    from src.qts.core.config.config_models import UnifiedConfig
    from src.execution.pipeline import ExecutionPipeline
    from src.risk.gates.calculated_risk_gate import CalculatedRiskGate, GateDecision
    from src.risk.calculators.base_risk_calculator import RiskResult
    from src.strategy.interfaces.strategy import Intent
    from src.provider.models.response import ExecutionResponse
    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False

pytestmark = pytest.mark.skipif(
    not _HAS_DEPS,
    reason="Pipeline dependencies (gspread) not installed",
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
    client.spreadsheet_id = "test-scalp-exec-spreadsheet"
    client.get_sheet_data = AsyncMock(side_effect=get_sheet_data)
    return client


def _make_snapshot(symbol="005930", price=75000) -> Dict[str, Any]:
    return {
        "meta": {"timestamp": "2026-02-13T09:30:00Z", "timestamp_ms": 1739432400000},
        "context": {"symbol": symbol},
        "observation": {"inputs": {"price": price, "volume": 5000}},
    }


class _MockBroker:
    NAME = "mock-broker"

    def __init__(self, *, accept_all: bool = True):
        self._accept_all = accept_all

    def submit_intent(self, intent):
        return ExecutionResponse(
            intent_id=intent.intent_id,
            accepted=self._accept_all and intent.quantity > 0,
            broker=self.NAME,
            message="Mock accepted" if self._accept_all else "Mock rejected",
        )


def _make_risk_gate(allowed=True, risk_score=0.3, max_qty=None):
    gate = MagicMock(spec=CalculatedRiskGate)

    def apply_fn(intent, market, exec_ctx):
        adjusted = intent if max_qty is None else Intent(
            symbol=intent.symbol,
            side=intent.side,
            qty=min(intent.qty, max_qty),
            reason=intent.reason,
        )
        risk = RiskResult(
            allowed=allowed,
            risk_score=risk_score,
            max_qty_allowed=max_qty or intent.qty,
            reason="ok",
        )
        return GateDecision(
            allowed=allowed,
            adjusted_intent=adjusted if allowed else None,
            risk=risk,
        )

    gate.apply = MagicMock(side_effect=apply_fn)
    return gate


class TestScalpExecutionIntegration:
    """Risk Gate + ExecutionPipeline 전체 흐름 통합 테스트."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_risk_and_execution(self, tmp_path):
        """Risk Gate + ExecutionPipeline 모두 주입 시 전체 파이프라인 정상 동작."""
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            broker=_MockBroker(accept_all=True),
            risk_gate=_make_risk_gate(allowed=True),
            execution_pipeline=ExecutionPipeline(),
        )
        result = await runner.run_once(_make_snapshot())
        assert result.get("status") != "error"

    @pytest.mark.asyncio
    async def test_backward_compat_no_injection(self, tmp_path):
        """기존 의존성 없이 정상 동작 (하위 호환)."""
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            broker=_MockBroker(accept_all=True),
        )
        result = await runner.run_once(_make_snapshot())
        assert result.get("status") != "error"

    @pytest.mark.asyncio
    async def test_risk_gate_blocks_stops_execution(self, tmp_path):
        """Risk Gate 차단 시 Act 단계에서 HOLD로 skip."""
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            broker=_MockBroker(accept_all=True),
            risk_gate=_make_risk_gate(allowed=False, risk_score=0.95),
            execution_pipeline=ExecutionPipeline(),
        )
        result = await runner.run_once(_make_snapshot())
        # decision should be not approved, so act should skip
        decision = result.get("decision", {})
        if decision.get("action") != "HOLD":
            assert decision.get("approved") is False
