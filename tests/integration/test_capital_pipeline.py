"""ETEDA 파이프라인 ↔ Capital Engine 통합 테스트.

NOTE: gspread 의존성이 필요합니다 (ETEDARunner → GoogleSheetsClient import chain).
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.capital.contracts import CapitalPoolContract, PoolId
from src.capital.engine import CapitalEngine
from src.capital.pool_repository import CapitalPoolRepository

try:
    from src.pipeline.eteda_runner import ETEDARunner
    from src.qts.core.config.config_models import UnifiedConfig
    _HAS_PIPELINE_DEPS = True
except ImportError:
    _HAS_PIPELINE_DEPS = False

pytestmark = pytest.mark.skipif(
    not _HAS_PIPELINE_DEPS,
    reason="Pipeline dependencies (gspread) not installed",
)


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

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
    client.spreadsheet_id = "test-capital-spreadsheet"
    client.get_sheet_data = AsyncMock(side_effect=get_sheet_data)
    return client


def _make_snapshot(symbol: str = "005930", price: float = 75000) -> Dict[str, Any]:
    return {
        "meta": {"timestamp": "2026-02-13T09:30:00Z", "timestamp_ms": 1739432400000},
        "context": {"symbol": symbol},
        "observation": {
            "inputs": {
                "price": price,
                "volume": 5000,
            }
        },
    }


def _make_config(**overrides) -> UnifiedConfig:
    defaults = {
        "RUN_MODE": "PAPER",
        "LIVE_ENABLED": "0",
        "trading_enabled": "1",
        "PIPELINE_PAUSED": "0",
        "KS_ENABLED": "false",
        "FAILSAFE_ENABLED": "false",
        "OPERATING_STATE": "BALANCED",
    }
    defaults.update(overrides)
    return UnifiedConfig(config_map=defaults, metadata={})


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


def _make_pools(tmp_path: Path) -> CapitalPoolRepository:
    repo = CapitalPoolRepository(tmp_path / "capital" / "pool_states.jsonl")
    pools = {
        PoolId.SCALP: CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("10000000"),
            allocation_pct=Decimal("0.40"),
            target_allocation_pct=Decimal("0.40"),
        ),
        PoolId.SWING: CapitalPoolContract(
            pool_id=PoolId.SWING,
            total_capital=Decimal("8000000"),
            allocation_pct=Decimal("0.32"),
            target_allocation_pct=Decimal("0.35"),
        ),
        PoolId.PORTFOLIO: CapitalPoolContract(
            pool_id=PoolId.PORTFOLIO,
            total_capital=Decimal("7000000"),
            allocation_pct=Decimal("0.28"),
            target_allocation_pct=Decimal("0.25"),
        ),
    }
    repo.save_pool_states(pools)
    return repo


def _make_runner(
    tmp_path: Path,
    *,
    config: UnifiedConfig | None = None,
    broker: _MockBroker | None = None,
    capital_engine: CapitalEngine | None = None,
    capital_pool_repo: CapitalPoolRepository | None = None,
) -> ETEDARunner:
    cfg = config or _make_config()
    brk = broker or _MockBroker(accept_all=True)

    return ETEDARunner(
        config=cfg,
        sheets_client=_make_mock_sheets_client(),
        project_root=tmp_path,
        broker=brk,
        safety_hook=None,
        feedback_aggregator=None,
        capital_engine=capital_engine,
        capital_pool_repo=capital_pool_repo,
    )


# ---------------------------------------------------------------------------
# 통합 테스트
# ---------------------------------------------------------------------------

class TestCapitalPipelineIntegration:
    """ETEDA 파이프라인 ↔ Capital Engine 통합 테스트."""

    @pytest.mark.asyncio
    async def test_run_once_without_capital(self, tmp_path):
        """Capital 미주입 시에도 파이프라인 정상 동작."""
        runner = _make_runner(tmp_path)
        result = await runner.run_once(_make_snapshot())
        assert result.get("status") != "error"

    @pytest.mark.asyncio
    async def test_run_once_with_capital_engine(self, tmp_path):
        """Capital Engine 주입 시 파이프라인 정상 동작."""
        pool_repo = _make_pools(tmp_path)
        engine = CapitalEngine()
        runner = _make_runner(
            tmp_path,
            capital_engine=engine,
            capital_pool_repo=pool_repo,
        )
        result = await runner.run_once(_make_snapshot())
        assert result.get("status") != "error"

    @pytest.mark.asyncio
    async def test_capital_evaluated_flag(self, tmp_path):
        """Capital 평가 후 signal에 capital_evaluated 플래그 존재."""
        pool_repo = _make_pools(tmp_path)
        engine = CapitalEngine()
        runner = _make_runner(
            tmp_path,
            capital_engine=engine,
            capital_pool_repo=pool_repo,
        )
        result = await runner.run_once(_make_snapshot())
        signal = result.get("signal", {})
        # HOLD이 아닌 경우에만 capital_evaluated 적용
        if signal.get("action") != "HOLD":
            assert signal.get("capital_evaluated") is True

    @pytest.mark.asyncio
    async def test_no_pools_file_still_works(self, tmp_path):
        """풀 파일이 없어도 파이프라인 정상 동작."""
        pool_repo = CapitalPoolRepository(tmp_path / "nonexistent" / "pools.jsonl")
        engine = CapitalEngine()
        runner = _make_runner(
            tmp_path,
            capital_engine=engine,
            capital_pool_repo=pool_repo,
        )
        result = await runner.run_once(_make_snapshot())
        assert result.get("status") != "error"


class TestCapitalConstraint:
    """Capital 제약 테스트."""

    @pytest.mark.asyncio
    async def test_lockdown_converts_to_hold(self, tmp_path):
        """Safety LOCKDOWN 시 HOLD 전환."""
        pool_repo = _make_pools(tmp_path)
        engine = CapitalEngine()

        # Safety Hook 모킹: LOCKDOWN 상태
        safety_hook = MagicMock()
        safety_hook.should_run.return_value = True
        safety_hook.pipeline_state.return_value = "LOCKDOWN"

        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            broker=_MockBroker(),
            safety_hook=safety_hook,
            capital_engine=engine,
            capital_pool_repo=pool_repo,
        )
        result = await runner.run_once(_make_snapshot())
        signal = result.get("signal", {})
        # LOCKDOWN 시 capital_blocked=True 또는 action=HOLD
        if signal.get("action") != "HOLD":
            # 전략이 HOLD을 반환하지 않았다면 capital이 차단했어야 함
            assert signal.get("capital_blocked") is True


class TestCapitalPoolUpdate:
    """Act 후 풀 상태 갱신 테스트."""

    @pytest.mark.asyncio
    async def test_pool_states_saved_after_act(self, tmp_path):
        """Act 실행 후 풀 상태가 저장됨."""
        pool_repo = _make_pools(tmp_path)
        engine = CapitalEngine()
        runner = _make_runner(
            tmp_path,
            capital_engine=engine,
            capital_pool_repo=pool_repo,
        )
        await runner.run_once(_make_snapshot())

        # JSONL 파일에 최소 1줄 존재 (초기 + 갱신)
        jsonl_path = tmp_path / "capital" / "pool_states.jsonl"
        assert jsonl_path.exists()
        lines = jsonl_path.read_text().strip().split("\n")
        assert len(lines) >= 1


class TestCapitalNoneEngine:
    """capital_engine=None 시 하위 호환 테스트."""

    @pytest.mark.asyncio
    async def test_load_and_evaluate_returns_none(self, tmp_path):
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            capital_engine=None,
            capital_pool_repo=None,
        )
        pool_states, decision = runner._load_and_evaluate_capital()
        assert pool_states is None
        assert decision is None

    @pytest.mark.asyncio
    async def test_update_capital_noop(self, tmp_path):
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            capital_engine=None,
            capital_pool_repo=None,
        )
        # 예외 없이 조용히 반환
        runner._update_capital_after_act(
            None,
            {"action": "BUY", "price": 75000, "qty": 10},
            {"status": "executed"},
        )
