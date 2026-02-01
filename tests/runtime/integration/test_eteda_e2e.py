"""
NG-0 E2E: ETEDA Pipeline full-flow tests (no live_sheets, no real_broker).

체크리스트:
- ETEDA 파이프라인 전체 흐름 (Extract→Transform→Evaluate→Decide→Act)
- 시나리오 10회 연속 성공
- 에러 복구 시나리오
- 성능 벤치마크 (ETEDA 사이클 < 3초)
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from runtime.config.config_models import UnifiedConfig
from runtime.execution.brokers.mock_broker import MockBroker
from runtime.pipeline.eteda_runner import ETEDARunner


def _make_mock_sheets_client() -> MagicMock:
    """Mock GoogleSheetsClient for E2E tests (no live API)."""
    headers = [
        "Symbol", "Name", "Market", "Qty", "Avg_Price(Current_Currency)",
        "Current_Price(Current_Currency)", "Strategy", "Sector"
    ]

    async def get_sheet_data(range_name: str, max_retries: int = 3) -> List[List[Any]]:
        # Header row: Position!A1:Z1 etc
        if "1" in range_name and "A2" not in range_name and "2:" not in range_name:
            return [headers]
        return []

    client = MagicMock()
    client.spreadsheet_id = "test-e2e-spreadsheet-id"
    client.get_sheet_data = AsyncMock(side_effect=get_sheet_data)
    return client


def _make_snapshot(symbol: str = "TEST", price: float = 99.0) -> Dict[str, Any]:
    """Create minimal snapshot for ETEDA run_once."""
    return {
        "meta": {"timestamp": "2026-01-31T12:00:00Z", "timestamp_ms": 1738310400000},
        "context": {"symbol": symbol},
        "observation": {
            "inputs": {
                "price": price,
                "volume": 1000,
            }
        },
    }


@pytest.fixture
def eteda_runner_with_mock():
    """ETEDARunner with mock sheets + MockBroker (no live API)."""
    config = UnifiedConfig(
        config_map={
            "RUN_MODE": "PAPER",
            "LIVE_ENABLED": "0",
            "trading_enabled": "1",
            "PIPELINE_PAUSED": "0",
            "KILLSWITCH_STATUS": "OFF",
        },
        metadata={},
    )
    mock_client = _make_mock_sheets_client()
    broker = MockBroker()
    project_root = Path(__file__).resolve().parents[3]
    runner = ETEDARunner(
        config=config,
        sheets_client=mock_client,
        project_root=project_root,
        broker=broker,
        safety_hook=None,
    )
    return runner


# --- 1. E2E 시나리오 테스트 ---


@pytest.mark.asyncio
async def test_eteda_full_flow_extract_transform_evaluate_decide_act(eteda_runner_with_mock):
    """ETEDA 전체 흐름: Extract→Transform→Evaluate→Decide→Act (Mock Broker)."""
    runner = eteda_runner_with_mock
    snapshot = _make_snapshot(symbol="TEST", price=99.0)

    result = await runner.run_once(snapshot)

    assert result is not None
    assert "symbol" in result or "status" in result
    assert result.get("status") != "error" or "skipped" in str(result.get("reason", ""))
    # Extract 검증: symbol이 snapshot에서 추출됨
    if "symbol" in result:
        assert result["symbol"] == "TEST"
    # Act 검증: Mock Broker 사용 시 executed 또는 skipped
    act = result.get("act_result", {})
    if act and act.get("status") == "executed":
        assert act.get("broker") == "mock-broker" or act.get("accepted") is not None


@pytest.mark.asyncio
async def test_eteda_extract_validates_price_required():
    """Extract: price 없으면 no_market_data 반환."""
    config = UnifiedConfig(config_map={"RUN_MODE": "PAPER"}, metadata={})
    mock_client = _make_mock_sheets_client()
    project_root = Path(__file__).resolve().parents[3]
    runner = ETEDARunner(config=config, sheets_client=mock_client, project_root=project_root)

    snapshot = {"meta": {}, "context": {"symbol": "X"}, "observation": {"inputs": {}}}
    result = await runner.run_once(snapshot)

    assert result.get("status") == "skipped"
    assert result.get("reason") == "no_market_data"


@pytest.mark.asyncio
async def test_eteda_10_consecutive_successes(eteda_runner_with_mock):
    """시나리오 10회 연속 성공 달성."""
    runner = eteda_runner_with_mock
    success_count = 0

    for i in range(10):
        snapshot = _make_snapshot(symbol=f"TEST{i}", price=100.0 + i * 0.1)
        result = await runner.run_once(snapshot)
        if result.get("status") != "error":
            success_count += 1

    assert success_count == 10, f"Expected 10 consecutive successes, got {success_count}"


@pytest.mark.asyncio
async def test_eteda_error_recovery_consecutive_failures_then_success(eteda_runner_with_mock):
    """에러 복구: 잘못된 스냅샷 후 정상 스냅샷으로 복구."""
    runner = eteda_runner_with_mock

    bad_snapshot = {"meta": {}, "context": {}, "observation": {"inputs": {}}}
    result_bad = await runner.run_once(bad_snapshot)
    assert result_bad.get("reason") == "no_market_data" or result_bad.get("status") == "skipped"

    good_snapshot = _make_snapshot(symbol="RECOVERY", price=105.0)
    result_good = await runner.run_once(good_snapshot)
    assert result_good.get("status") != "error"
    assert "symbol" in result_good or "act_result" in result_good


# --- 2. 성능 벤치마크 ---


@pytest.mark.asyncio
async def test_eteda_cycle_latency_under_3_seconds(eteda_runner_with_mock):
    """ETEDA 사이클 평균 < 3초 (Mock 기준, Google Sheets 없음)."""
    runner = eteda_runner_with_mock
    latencies = []

    for _ in range(5):
        snapshot = _make_snapshot()
        start = time.perf_counter()
        await runner.run_once(snapshot)
        elapsed = time.perf_counter() - start
        latencies.append(elapsed)

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 3.0, f"Average ETEDA cycle {avg_latency:.3f}s exceeds 3s target"


@pytest.mark.asyncio
async def test_eteda_step_latency_targets_mock_mode(eteda_runner_with_mock):
    """각 ETEDA 단계별 레이턴시 목표 (Mock 모드)."""
    runner = eteda_runner_with_mock
    snapshot = _make_snapshot()

    start = time.perf_counter()
    result = await runner.run_once(snapshot)
    total_ms = (time.perf_counter() - start) * 1000

    # Mock 모드에서 Extract~Act 전체가 3초 이내여야 함
    assert total_ms < 3000, f"Full cycle {total_ms:.0f}ms exceeds 3000ms"
    assert result.get("status") != "error"
