"""_decide() + CalculatedRiskGate 통합 단위 테스트."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

try:
    from src.pipeline.eteda_runner import ETEDARunner
    from src.qts.core.config.config_models import UnifiedConfig
    from src.risk.gates.calculated_risk_gate import CalculatedRiskGate, GateDecision
    from src.risk.calculators.base_risk_calculator import RiskResult
    from src.strategy.interfaces.strategy import Intent, MarketContext, ExecutionContext
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
    client.spreadsheet_id = "test-risk-gate-spreadsheet"
    client.get_sheet_data = AsyncMock(side_effect=get_sheet_data)
    return client


def _make_signal(action="BUY", symbol="005930", price=75000, qty=10) -> Dict[str, Any]:
    return {
        "action": action,
        "symbol": symbol,
        "price": price,
        "qty": qty,
        "strategy": "scalp",
    }


def _make_risk_gate(allowed=True, risk_score=0.3, max_qty=None, reason="ok"):
    """Mock CalculatedRiskGate."""
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
            reason=reason,
        )
        return GateDecision(
            allowed=allowed,
            adjusted_intent=adjusted if allowed else None,
            risk=risk,
        )

    gate.apply = MagicMock(side_effect=apply_fn)
    return gate


class TestDecideWithoutRiskGate:
    """risk_gate=None 시 기존 동작 검증."""

    def test_decide_without_risk_gate(self, tmp_path):
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            risk_gate=None,
        )
        signal = _make_signal()
        result = runner._decide(signal)
        assert result["approved"] is True
        assert "risk_evaluated" not in result

    def test_decide_hold_no_risk_gate(self, tmp_path):
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            risk_gate=None,
        )
        signal = _make_signal(action="HOLD")
        result = runner._decide(signal)
        assert result["approved"] is True


class TestDecideWithRiskGate:
    """risk_gate 주입 시 동작 검증."""

    def test_risk_gate_allows(self, tmp_path):
        gate = _make_risk_gate(allowed=True, risk_score=0.3)
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            risk_gate=gate,
        )
        signal = _make_signal()
        result = runner._decide(signal)
        assert result["approved"] is True
        assert result.get("risk_evaluated") is True
        assert result.get("risk_score") == 0.3
        gate.apply.assert_called_once()

    def test_risk_gate_blocks(self, tmp_path):
        gate = _make_risk_gate(allowed=False, risk_score=0.9, reason="risk_too_high")
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            risk_gate=gate,
        )
        signal = _make_signal()
        result = runner._decide(signal)
        assert result["approved"] is False
        assert "risk_too_high" in result["reason"]

    def test_risk_gate_adjusts_qty(self, tmp_path):
        gate = _make_risk_gate(allowed=True, risk_score=0.5, max_qty=5)
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            risk_gate=gate,
        )
        signal = _make_signal(qty=10)
        result = runner._decide(signal)
        assert result["approved"] is True
        assert result["qty"] == 5
        assert result.get("risk_qty_adjusted") is True

    def test_risk_gate_error_fallback(self, tmp_path):
        gate = MagicMock()
        gate.apply = MagicMock(side_effect=RuntimeError("broken"))
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            risk_gate=gate,
        )
        signal = _make_signal()
        result = runner._decide(signal)
        # Fallback to default: approved=True
        assert result["approved"] is True
        assert "risk_evaluated" not in result

    def test_hold_skips_risk_gate(self, tmp_path):
        gate = _make_risk_gate(allowed=True)
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            risk_gate=gate,
        )
        signal = _make_signal(action="HOLD")
        result = runner._decide(signal)
        assert result["approved"] is True
        gate.apply.assert_not_called()
