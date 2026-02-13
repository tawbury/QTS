"""ETEDARunner Operating State 통합 테스트.

근거: docs/arch/sub/18_System_State_Promotion_Architecture.md §6.2, §6.3
"""
from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

try:
    from src.pipeline.eteda_runner import ETEDARunner
    from src.qts.core.config.config_models import UnifiedConfig
    from src.state.contracts import OperatingState, STATE_PROPERTIES
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
    client.spreadsheet_id = "test-spreadsheet"
    client.get_sheet_data = AsyncMock(side_effect=get_sheet_data)
    return client


def _make_signal(action="BUY", symbol="005930", price=75000, qty=10, **kwargs) -> Dict[str, Any]:
    sig = {
        "action": action,
        "symbol": symbol,
        "price": price,
        "qty": qty,
        "strategy": "scalp",
    }
    sig.update(kwargs)
    return sig


class TestGetOperatingStateProperties:
    """_get_operating_state_properties 메서드."""

    def test_balanced_default(self, tmp_path):
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
        )
        state, props = runner._get_operating_state_properties()
        assert state == OperatingState.BALANCED
        assert props.scalp_engine_active is True
        assert props.new_entry_enabled is True

    def test_defensive_state(self, tmp_path):
        runner = ETEDARunner(
            config=_make_config(OPERATING_STATE="DEFENSIVE"),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
        )
        state, props = runner._get_operating_state_properties()
        assert state == OperatingState.DEFENSIVE
        assert props.scalp_engine_active is False
        assert props.new_entry_enabled is False

    def test_aggressive_state(self, tmp_path):
        runner = ETEDARunner(
            config=_make_config(OPERATING_STATE="AGGRESSIVE"),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
        )
        state, props = runner._get_operating_state_properties()
        assert state == OperatingState.AGGRESSIVE
        assert props.scalp_engine_active is True
        assert props.new_entry_enabled is True

    def test_invalid_state_falls_back_balanced(self, tmp_path):
        runner = ETEDARunner(
            config=_make_config(OPERATING_STATE="INVALID_STATE"),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
        )
        state, props = runner._get_operating_state_properties()
        assert state == OperatingState.BALANCED


class TestEvaluateStateFiltering:
    """_evaluate() Operating State 필터링 (§6.2)."""

    def test_defensive_blocks_scalp(self, tmp_path):
        """DEFENSIVE 상태에서 scalp engine 비활성화 → HOLD."""
        runner = ETEDARunner(
            config=_make_config(OPERATING_STATE="DEFENSIVE"),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
        )
        data = {
            "market": {"symbol": "005930", "price": 75000, "volume": 1000},
            "position": {},
        }
        result = runner._evaluate(data)
        assert result["action"] == "HOLD"
        assert "SCALP_DISABLED" in result["reason"]
        assert result["operating_state"] == "DEFENSIVE"

    def test_balanced_allows_signal(self, tmp_path):
        """BALANCED 상태에서 신호 통과."""
        runner = ETEDARunner(
            config=_make_config(OPERATING_STATE="BALANCED"),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
        )
        data = {
            "market": {"symbol": "005930", "price": 75000, "volume": 1000},
            "position": {},
        }
        result = runner._evaluate(data)
        # StrategyEngine이 mock이므로 어떤 결과든 나오지만 SCALP_DISABLED는 아님
        assert "SCALP_DISABLED" not in result.get("reason", "")
        assert result.get("operating_state") == "BALANCED"

    def test_aggressive_lower_threshold(self, tmp_path):
        """AGGRESSIVE 상태는 entry_signal_threshold가 낮아 더 많은 신호 통과."""
        aggressive_props = STATE_PROPERTIES[OperatingState.AGGRESSIVE]
        balanced_props = STATE_PROPERTIES[OperatingState.BALANCED]
        assert aggressive_props.entry_signal_threshold < balanced_props.entry_signal_threshold


class TestDecideStateOverride:
    """_decide() Operating State 오버라이드 (§6.3)."""

    def test_defensive_blocks_buy(self, tmp_path):
        """DEFENSIVE 상태에서 BUY 신규 진입 차단."""
        runner = ETEDARunner(
            config=_make_config(OPERATING_STATE="DEFENSIVE"),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
        )
        signal = _make_signal(action="BUY")
        result = runner._decide(signal)
        assert result["action"] == "HOLD"
        assert result["approved"] is False
        assert "NEW_ENTRY_BLOCKED" in result["reason"]

    def test_defensive_allows_sell(self, tmp_path):
        """DEFENSIVE 상태에서 SELL은 허용 (청산)."""
        runner = ETEDARunner(
            config=_make_config(OPERATING_STATE="DEFENSIVE"),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
        )
        signal = _make_signal(action="SELL")
        result = runner._decide(signal)
        # SELL은 차단 대상이 아님
        assert result["action"] == "SELL"

    def test_defensive_allows_hold(self, tmp_path):
        """DEFENSIVE 상태에서 HOLD 그대로 통과."""
        runner = ETEDARunner(
            config=_make_config(OPERATING_STATE="DEFENSIVE"),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
        )
        signal = _make_signal(action="HOLD")
        result = runner._decide(signal)
        assert result["action"] == "HOLD"
        assert result["approved"] is True

    def test_balanced_allows_buy(self, tmp_path):
        """BALANCED 상태에서 BUY 허용."""
        runner = ETEDARunner(
            config=_make_config(OPERATING_STATE="BALANCED"),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
        )
        signal = _make_signal(action="BUY")
        result = runner._decide(signal)
        assert result["action"] == "BUY"
        assert result["approved"] is True

    def test_aggressive_allows_buy(self, tmp_path):
        """AGGRESSIVE 상태에서 BUY 허용."""
        runner = ETEDARunner(
            config=_make_config(OPERATING_STATE="AGGRESSIVE"),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
        )
        signal = _make_signal(action="BUY")
        result = runner._decide(signal)
        assert result["action"] == "BUY"
        assert result["approved"] is True
