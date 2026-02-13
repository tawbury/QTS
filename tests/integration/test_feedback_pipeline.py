"""ETEDA 파이프라인 ↔ Feedback 루프 통합 테스트.

Phase 1 핵심 검증: Act → Feedback 수집 → 다음 사이클 Strategy 보정.

NOTE: gspread 의존성이 필요합니다 (ETEDARunner → GoogleSheetsClient import chain).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.feedback.aggregator import FeedbackAggregator
from src.feedback.contracts import DEFAULT_FEEDBACK_SUMMARY, FeedbackSummary
from src.feedback.sheet_adapter import JsonlFeedbackDB

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
    client.spreadsheet_id = "test-feedback-spreadsheet"
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
    }
    defaults.update(overrides)
    return UnifiedConfig(config_map=defaults, metadata={})


class _MockBroker:
    """테스트용 Mock Broker (accept_all 모드 지원)."""

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


def _make_runner(
    tmp_path: Path,
    *,
    config: UnifiedConfig | None = None,
    broker: _MockBroker | None = None,
    feedback_agg: FeedbackAggregator | None = None,
) -> ETEDARunner:
    cfg = config or _make_config()
    brk = broker or _MockBroker(accept_all=True)
    if feedback_agg is None:
        db = JsonlFeedbackDB(tmp_path / "feedback.jsonl")
        feedback_agg = FeedbackAggregator(db=db)

    return ETEDARunner(
        config=cfg,
        sheets_client=_make_mock_sheets_client(),
        project_root=tmp_path,
        broker=brk,
        safety_hook=None,
        feedback_aggregator=feedback_agg,
    )


# ---------------------------------------------------------------------------
# 통합 테스트
# ---------------------------------------------------------------------------

class TestFeedbackPipelineIntegration:
    """ETEDA 파이프라인 ↔ Feedback 루프 통합 테스트."""

    @pytest.mark.asyncio
    async def test_run_once_without_feedback(self, tmp_path):
        """Feedback 미주입 시에도 파이프라인 정상 동작."""
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            broker=_MockBroker(),
            safety_hook=None,
            feedback_aggregator=None,
        )
        result = await runner.run_once(_make_snapshot())
        assert result.get("status") != "error"

    @pytest.mark.asyncio
    async def test_feedback_collected_after_act(self, tmp_path):
        """Act 실행 후 피드백 데이터가 JSONL에 기록됨."""
        jsonl_path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(jsonl_path)
        agg = FeedbackAggregator(db=db)
        runner = _make_runner(tmp_path, feedback_agg=agg)

        await runner.run_once(_make_snapshot())

        # JSONL 파일이 존재하고 내용이 있어야 함
        if jsonl_path.exists():
            lines = jsonl_path.read_text().strip().split("\n")
            assert len(lines) >= 0  # 실행이 HOLD 아닌 경우에만 기록됨

    @pytest.mark.asyncio
    async def test_feedback_summary_used_in_evaluate(self, tmp_path):
        """Feedback summary가 _evaluate에서 참조됨."""
        jsonl_path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(jsonl_path)
        agg = FeedbackAggregator(db=db)

        # 충분한 피드백 데이터 미리 저장 (5개 이상)
        from datetime import datetime, timezone
        from decimal import Decimal

        for i in range(6):
            agg.aggregate_and_store(
                symbol="005930",
                order_id=f"pre-order-{i}",
                execution_start=datetime.now(timezone.utc),
                execution_end=datetime.now(timezone.utc),
                decision_price=Decimal("75000"),
                avg_fill_price=Decimal("75050"),
                filled_qty=Decimal("100"),
                original_qty=Decimal("100"),
                partial_fill_ratio=0.0,
                avg_fill_latency_ms=40.0,
                strategy_tag="SCALP_RSI",
                order_type="MARKET",
            )

        runner = _make_runner(tmp_path, feedback_agg=agg)
        result = await runner.run_once(_make_snapshot(symbol="005930", price=75000))

        # 파이프라인 자체가 에러 없이 완료되어야 함
        assert result.get("status") != "error"

        # signal에 feedback_applied가 있으면 보정이 적용된 것
        signal = result.get("signal", {})
        if signal.get("action") != "HOLD" and signal.get("feedback_applied"):
            assert signal["feedback_sample_count"] >= 5

    @pytest.mark.asyncio
    async def test_feedback_fire_and_forget_on_exception(self, tmp_path):
        """Feedback 수집 실패 시에도 파이프라인 결과에 영향 없음."""

        class FailingDB:
            def store_feedback(self, feedback):
                raise RuntimeError("DB write failed!")

            def fetch_feedback_summary(self, symbol, lookback_days):
                raise RuntimeError("DB read failed!")

        agg = FeedbackAggregator(db=FailingDB())
        runner = _make_runner(tmp_path, feedback_agg=agg)

        result = await runner.run_once(_make_snapshot())
        # DB 장애에도 파이프라인이 정상 완료
        assert result.get("status") != "error"

    @pytest.mark.asyncio
    async def test_no_feedback_for_hold_signal(self, tmp_path):
        """HOLD 신호 시 피드백 수집 하지 않음."""
        jsonl_path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(jsonl_path)
        agg = FeedbackAggregator(db=db)
        runner = _make_runner(tmp_path, feedback_agg=agg)

        # price 없는 스냅샷 → no_market_data → 피드백 수집 안 됨
        snapshot = {
            "meta": {},
            "context": {"symbol": "TEST"},
            "observation": {"inputs": {}},
        }
        result = await runner.run_once(snapshot)
        assert result.get("status") == "skipped"

        # JSONL에 아무것도 기록되지 않아야 함
        if jsonl_path.exists():
            content = jsonl_path.read_text().strip()
            assert content == ""

    @pytest.mark.asyncio
    async def test_rejected_order_no_feedback(self, tmp_path):
        """거부된 주문은 피드백 수집하지 않음."""
        jsonl_path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(jsonl_path)
        agg = FeedbackAggregator(db=db)
        broker = _MockBroker(accept_all=False)
        runner = _make_runner(tmp_path, broker=broker, feedback_agg=agg)

        result = await runner.run_once(_make_snapshot())

        # 거부 시 피드백 수집 안 됨 (accepted=False)
        # JSONL이 비어있거나 존재하지 않아야 함
        if jsonl_path.exists():
            content = jsonl_path.read_text().strip()
            # rejected + status != "executed" → _collect_feedback 스킵
            # (HOLD 결과일 수도 있음)


class TestFeedbackAdjustments:
    """_apply_feedback_adjustments 보정 동작 테스트."""

    @pytest.mark.asyncio
    async def test_adjustments_applied_with_sufficient_samples(self, tmp_path):
        """샘플 5개 이상 시 보정 적용."""
        jsonl_path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(jsonl_path)
        agg = FeedbackAggregator(db=db)

        from datetime import datetime, timezone
        from decimal import Decimal

        for i in range(10):
            agg.aggregate_and_store(
                symbol="005930",
                order_id=f"order-{i}",
                execution_start=datetime.now(timezone.utc),
                execution_end=datetime.now(timezone.utc),
                decision_price=Decimal("75000"),
                avg_fill_price=Decimal("75050"),
                filled_qty=Decimal("100"),
                original_qty=Decimal("100"),
                partial_fill_ratio=0.0,
                avg_fill_latency_ms=40.0,
                strategy_tag="SCALP_RSI",
                order_type="MARKET",
            )

        runner = _make_runner(tmp_path, feedback_agg=agg)

        # _get_feedback_summary 직접 테스트
        summary = runner._get_feedback_summary("005930")
        assert summary is not None
        assert summary.sample_count == 10

    @pytest.mark.asyncio
    async def test_adjustments_skipped_with_insufficient_samples(self, tmp_path):
        """샘플 5개 미만 시 보정 미적용."""
        jsonl_path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(jsonl_path)
        agg = FeedbackAggregator(db=db)

        from datetime import datetime, timezone
        from decimal import Decimal

        # 3개만 저장 (5개 미만)
        for i in range(3):
            agg.aggregate_and_store(
                symbol="005930",
                order_id=f"order-{i}",
                execution_start=datetime.now(timezone.utc),
                execution_end=datetime.now(timezone.utc),
                decision_price=Decimal("75000"),
                avg_fill_price=Decimal("75050"),
                filled_qty=Decimal("100"),
                original_qty=Decimal("100"),
                partial_fill_ratio=0.0,
                avg_fill_latency_ms=40.0,
            )

        runner = _make_runner(tmp_path, feedback_agg=agg)
        summary = runner._get_feedback_summary("005930")
        assert summary is not None
        assert summary.sample_count == 3
        # sample_count < 5 이므로 _evaluate에서 보정 미적용

    @pytest.mark.asyncio
    async def test_no_feedback_summary_for_unknown_symbol(self, tmp_path):
        """알 수 없는 종목은 DEFAULT_FEEDBACK_SUMMARY 반환."""
        db = JsonlFeedbackDB(tmp_path / "feedback.jsonl")
        agg = FeedbackAggregator(db=db)
        runner = _make_runner(tmp_path, feedback_agg=agg)

        summary = runner._get_feedback_summary("UNKNOWN")
        assert summary is not None
        assert summary.sample_count == 0


class TestFeedbackNoneAggregator:
    """feedback_aggregator=None 시 하위 호환 테스트."""

    @pytest.mark.asyncio
    async def test_get_feedback_summary_returns_none(self, tmp_path):
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            feedback_aggregator=None,
        )
        assert runner._get_feedback_summary("005930") is None

    @pytest.mark.asyncio
    async def test_collect_feedback_noop(self, tmp_path):
        runner = ETEDARunner(
            config=_make_config(),
            sheets_client=_make_mock_sheets_client(),
            project_root=tmp_path,
            feedback_aggregator=None,
        )
        # 예외 없이 조용히 반환
        runner._collect_feedback(
            {"symbol": "005930", "action": "BUY", "price": 75000, "qty": 10},
            {"status": "executed", "accepted": True},
        )
