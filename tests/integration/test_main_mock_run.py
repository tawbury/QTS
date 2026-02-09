"""
main.py Mock Run 통합 테스트

목적:
1. --local-only 모드에서 ETEDA 파이프라인 전체 흐름 검증
2. ExecutionIntent가 Broker에 정상 전달되는지 확인
3. Config → Runner → Strategy → Broker 데이터 흐름 검증

실행:
    pytest tests/integration/test_main_mock_run.py -v
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List

import pytest

# 프로젝트 루트 설정
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.qts.core.config.config_loader import load_local_only_config
from src.qts.core.config.config_models import UnifiedConfig
from src.db.mock_sheets_client import MockSheetsClient
from src.pipeline.mock_safety_hook import MockSafetyHook
from src.pipeline.loop.mock_snapshot_source import MockSnapshotSource
from src.provider.brokers.noop_broker import NoopBroker
from src.provider.brokers.mock_broker import MockBroker
from src.provider.models.intent import ExecutionIntent
from src.provider.models.response import ExecutionResponse
from src.pipeline.eteda_runner import ETEDARunner
from src.pipeline.loop.eteda_loop import run_eteda_loop


class IntentCapturingBroker(MockBroker):
    """
    테스트용 Broker: 전달된 ExecutionIntent를 캡처하여 검증 가능하게 함.
    """

    NAME = "intent-capturing-broker"

    def __init__(self):
        super().__init__()
        self.captured_intents: List[ExecutionIntent] = []

    def submit_intent(self, intent: ExecutionIntent) -> ExecutionResponse:
        self.captured_intents.append(intent)
        return super().submit_intent(intent)


class ForceSignalStrategyEngine:
    """
    테스트용 StrategyEngine: 특정 시그널을 강제로 반환.
    """

    def __init__(self, forced_action: str = "BUY", forced_qty: float = 10):
        self._forced_action = forced_action
        self._forced_qty = forced_qty

    def calculate_signal(self, market_data: Dict[str, Any], position_data: Dict[str, Any]) -> Dict[str, Any]:
        price_val = market_data.get('price', 0.0)
        close_price = float(price_val.get('close', 0.0)) if isinstance(price_val, dict) else float(price_val or 0.0)

        return {
            'symbol': market_data.get('symbol'),
            'action': self._forced_action,
            'qty': self._forced_qty,
            'weight': 1.0,
            'price': close_price,
            'timestamp': market_data.get('timestamp'),
        }


@pytest.fixture
def project_root() -> Path:
    return _ROOT


@pytest.fixture
def config(project_root: Path) -> UnifiedConfig:
    result = load_local_only_config(project_root)
    assert result.ok and result.unified_config is not None
    return result.unified_config


@pytest.fixture
def mock_sheets() -> MockSheetsClient:
    return MockSheetsClient()


@pytest.fixture
def mock_safety() -> MockSafetyHook:
    return MockSafetyHook(initial_state="NORMAL")


@pytest.fixture
def capturing_broker() -> IntentCapturingBroker:
    return IntentCapturingBroker()


class TestMainMockRun:
    """main.py Mock Run 통합 테스트"""

    def test_config_local_loads_successfully(self, config: UnifiedConfig):
        """Config_Local이 정상적으로 로드되는지 확인"""
        assert config is not None
        # INTERVAL_MS가 존재하는지 확인
        interval = config.get_flat("INTERVAL_MS")
        assert interval is not None, "INTERVAL_MS should be present in config_local"

    def test_mock_sheets_client_works(self, mock_sheets: MockSheetsClient):
        """MockSheetsClient가 정상 동작하는지 확인"""
        assert mock_sheets.spreadsheet_id == "mock-spreadsheet-id"

        # get_sheet_data가 빈 리스트를 반환하는지 확인
        async def _test():
            data = await mock_sheets.get_sheet_data("Position!A:Z")
            assert data == []

        asyncio.run(_test())

    def test_mock_safety_hook_works(self, mock_safety: MockSafetyHook):
        """MockSafetyHook이 정상 동작하는지 확인"""
        assert mock_safety.should_run() is True
        assert mock_safety.pipeline_state() == "NORMAL"

        # Fail-Safe 기록 테스트
        mock_safety.record_fail_safe("FS040", "test message", "Act")
        records = mock_safety.get_fail_safe_records()
        assert len(records) == 1
        assert records[0] == ("FS040", "test message", "Act")

    def test_mock_snapshot_source_generates_data(self):
        """MockSnapshotSource가 유효한 스냅샷을 생성하는지 확인"""
        source = MockSnapshotSource(
            symbols=["005930"],
            base_prices={"005930": 70000.0},
            max_iterations=3,
        )

        snapshot1 = source()
        assert snapshot1["trigger"] == "mock"
        assert snapshot1["context"]["symbol"] == "005930"
        assert "price" in snapshot1["observation"]["inputs"]

        snapshot2 = source()
        assert snapshot2["context"]["symbol"] == "005930"

        assert source.iteration_count == 2

    @pytest.mark.asyncio
    async def test_eteda_runner_run_once_with_mock_data(
        self,
        config: UnifiedConfig,
        project_root: Path,
        mock_sheets: MockSheetsClient,
        mock_safety: MockSafetyHook,
        capturing_broker: IntentCapturingBroker,
    ):
        """ETEDARunner.run_once가 Mock 데이터로 정상 실행되는지 확인"""
        runner = ETEDARunner(
            config=config,
            sheets_client=mock_sheets,
            project_root=project_root,
            broker=capturing_broker,
            safety_hook=mock_safety,
        )

        # Mock 스냅샷 생성
        snapshot = {
            "trigger": "test",
            "meta": {"timestamp": "2024-01-01 12:00:00", "timestamp_ms": 1704110400000},
            "context": {"symbol": "005930", "market": "KOSPI"},
            "observation": {
                "inputs": {
                    "price": {"open": 70000, "high": 70500, "low": 69500, "close": 70100},
                    "volume": 50000,
                }
            },
        }

        result = await runner.run_once(snapshot)

        # 결과 검증: 에러가 아닌 경우 status 키가 없을 수 있음
        if "status" in result:
            assert result["status"] != "error", f"run_once failed: {result.get('error')}"
        assert result["symbol"] == "005930"
        assert "signal" in result
        assert "decision" in result
        assert result["pipeline_state"] == "NORMAL"

    @pytest.mark.asyncio
    async def test_execution_intent_passed_to_broker(
        self,
        config: UnifiedConfig,
        project_root: Path,
        mock_sheets: MockSheetsClient,
        mock_safety: MockSafetyHook,
        capturing_broker: IntentCapturingBroker,
    ):
        """
        BUY 시그널 시 ExecutionIntent가 Broker에 정상 전달되는지 확인.

        전제: StrategyEngine을 강제로 BUY 시그널을 반환하도록 패치.
        """
        runner = ETEDARunner(
            config=config,
            sheets_client=mock_sheets,
            project_root=project_root,
            broker=capturing_broker,
            safety_hook=mock_safety,
        )

        # StrategyEngine을 강제 시그널 반환으로 교체
        runner._strategy_engine = ForceSignalStrategyEngine(forced_action="BUY", forced_qty=10)

        # Mock 스냅샷
        snapshot = {
            "trigger": "test",
            "meta": {"timestamp": "2024-01-01 12:00:00", "timestamp_ms": 1704110400000},
            "context": {"symbol": "005930", "market": "KOSPI"},
            "observation": {
                "inputs": {
                    "price": {"open": 70000, "high": 70500, "low": 69500, "close": 70100},
                    "volume": 50000,
                }
            },
        }

        result = await runner.run_once(snapshot)

        # ExecutionIntent가 Broker에 전달되었는지 확인
        assert len(capturing_broker.captured_intents) == 1, \
            f"Expected 1 intent, got {len(capturing_broker.captured_intents)}"

        intent = capturing_broker.captured_intents[0]
        assert intent.symbol == "005930"
        assert intent.side == "BUY"
        assert intent.quantity == 10
        assert intent.intent_type == "MARKET"

        # act_result 검증
        assert result["act_result"]["status"] == "executed"
        assert result["act_result"]["broker"] == "intent-capturing-broker"

    @pytest.mark.asyncio
    async def test_eteda_loop_runs_limited_iterations(
        self,
        config: UnifiedConfig,
        project_root: Path,
        mock_sheets: MockSheetsClient,
        mock_safety: MockSafetyHook,
    ):
        """ETEDA 루프가 지정된 반복 횟수 후 정상 종료되는지 확인"""
        broker = NoopBroker()
        runner = ETEDARunner(
            config=config,
            sheets_client=mock_sheets,
            project_root=project_root,
            broker=broker,
            safety_hook=mock_safety,
        )

        snapshot_source = MockSnapshotSource(
            symbols=["005930"],
            base_prices={"005930": 70000.0},
            max_iterations=3,
        )

        iteration_count = [0]

        def should_stop() -> bool:
            return snapshot_source.iteration_count >= 3

        # 루프 실행
        await run_eteda_loop(
            runner=runner,
            config=config,
            should_stop=should_stop,
            snapshot_source=snapshot_source,
        )

        # 3회 반복 후 종료되었는지 확인
        assert snapshot_source.iteration_count == 3

    @pytest.mark.asyncio
    async def test_noop_broker_rejects_all_intents(
        self,
        config: UnifiedConfig,
        project_root: Path,
        mock_sheets: MockSheetsClient,
        mock_safety: MockSafetyHook,
    ):
        """NoopBroker가 모든 ExecutionIntent를 거부하는지 확인"""
        broker = NoopBroker()
        runner = ETEDARunner(
            config=config,
            sheets_client=mock_sheets,
            project_root=project_root,
            broker=broker,
            safety_hook=mock_safety,
        )

        # 강제 BUY 시그널
        runner._strategy_engine = ForceSignalStrategyEngine(forced_action="BUY", forced_qty=10)

        snapshot = {
            "trigger": "test",
            "meta": {"timestamp": "2024-01-01 12:00:00", "timestamp_ms": 1704110400000},
            "context": {"symbol": "005930", "market": "KOSPI"},
            "observation": {
                "inputs": {
                    "price": {"open": 70000, "high": 70500, "low": 69500, "close": 70100},
                    "volume": 50000,
                }
            },
        }

        result = await runner.run_once(snapshot)

        # NoopBroker는 거부해야 함
        assert result["act_result"]["status"] == "rejected"
        assert result["act_result"]["broker"] == "noop-broker"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
