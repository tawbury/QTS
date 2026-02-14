"""ETEDA 피드백 루프 통합 테스트.

근거: docs/02-design/features/eteda-db-feedback-loop.design.md T-04
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.feedback.aggregator import FeedbackAggregator, NoopFeedbackDB
from src.feedback.contracts import FeedbackSummary, DEFAULT_FEEDBACK_SUMMARY
from src.feedback.performance_feedback import PerformanceFeedbackProvider


class TestFeedbackStoredInRepo:
    """Act 후 FeedbackRepository에 저장 확인."""

    def test_aggregate_and_store_uses_repo(self):
        """TimescaleDB repo가 있으면 비동기 저장 시도."""
        mock_repo = AsyncMock()
        mock_db = NoopFeedbackDB()
        agg = FeedbackAggregator(mock_db, feedback_repo=mock_repo)

        # repo.store는 async이므로 event loop이 필요. 여기서는 fallback 경로 테스트.
        # event loop 없을 때 JSONL fallback
        feedback = agg.aggregate_and_store(
            symbol="005930",
            order_id="test-001",
            execution_start=datetime.now(timezone.utc),
            execution_end=datetime.now(timezone.utc),
            decision_price=Decimal("70000"),
            avg_fill_price=Decimal("70010"),
            filled_qty=Decimal("10"),
            original_qty=Decimal("10"),
            partial_fill_ratio=0.0,
            avg_fill_latency_ms=12.5,
            strategy_tag="scalp",
            order_type="MARKET",
        )
        assert feedback.symbol == "005930"
        # event loop 없으므로 JSONL fallback
        assert len(mock_db.stored) == 1

    def test_aggregate_and_store_fallback_no_repo(self):
        """repo 없으면 JSONL 직접 저장."""
        mock_db = NoopFeedbackDB()
        agg = FeedbackAggregator(mock_db)

        feedback = agg.aggregate_and_store(
            symbol="005930",
            order_id="test-002",
            execution_start=datetime.now(timezone.utc),
            execution_end=datetime.now(timezone.utc),
            decision_price=Decimal("70000"),
            avg_fill_price=Decimal("70010"),
            filled_qty=Decimal("10"),
            original_qty=Decimal("10"),
            partial_fill_ratio=0.0,
            avg_fill_latency_ms=12.5,
        )
        assert len(mock_db.stored) == 1


class TestPerformanceConstraint:
    """MDD 높을 때 qty 감소."""

    def test_apply_performance_constraint_blocks_entry(self):
        """MDD > 5% -> HOLD 전환."""
        from datetime import date
        trades = [
            {"timestamp": f"{date.today().isoformat()}T10:00:00", "pnl": -6_000_000},
        ]
        mock_ledger = MagicMock()
        mock_ledger.get_all.return_value = trades
        mock_config = MagicMock()

        provider = PerformanceFeedbackProvider(mock_ledger, mock_config)
        assert provider.should_block_new_entry() is True

    def test_sizing_multiplier_reduces_qty(self):
        """MDD 3% -> qty 50%."""
        from datetime import date
        trades = [
            {"timestamp": f"{date.today().isoformat()}T10:00:00", "pnl": -3_500_000},
        ]
        mock_ledger = MagicMock()
        mock_ledger.get_all.return_value = trades
        mock_config = MagicMock()

        provider = PerformanceFeedbackProvider(mock_ledger, mock_config)
        multiplier = provider.get_sizing_multiplier()
        assert multiplier == 0.5

        # qty 100 * 0.5 = 50
        original_qty = 100
        adjusted_qty = max(1, int(original_qty * multiplier))
        assert adjusted_qty == 50


class TestStrategySpecificFeedback:
    """SCALP/SWING 별도 피드백."""

    @pytest.mark.asyncio
    async def test_get_summary_async_by_strategy(self):
        """전략별 비동기 요약 조회."""
        mock_repo = AsyncMock()
        mock_repo.fetch_summary_by_strategy.return_value = FeedbackSummary(
            avg_slippage_bps=1.5,
            avg_market_impact_bps=0.3,
            avg_quality_score=0.92,
            avg_fill_latency_ms=8.0,
            avg_fill_ratio=0.99,
            sample_count=25,
        )
        mock_db = NoopFeedbackDB()
        agg = FeedbackAggregator(mock_db, feedback_repo=mock_repo)

        summary = await agg.get_summary_async("005930", strategy_tag="scalp")
        assert summary.sample_count == 25
        assert summary.avg_slippage_bps == 1.5
        mock_repo.fetch_summary_by_strategy.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_summary_async_general(self):
        """전략 미지정 시 전체 요약."""
        mock_repo = AsyncMock()
        mock_repo.fetch_summary.return_value = FeedbackSummary(
            avg_slippage_bps=2.0,
            avg_market_impact_bps=0.5,
            avg_quality_score=0.88,
            avg_fill_latency_ms=12.0,
            avg_fill_ratio=0.95,
            sample_count=100,
        )
        mock_db = NoopFeedbackDB()
        agg = FeedbackAggregator(mock_db, feedback_repo=mock_repo)

        summary = await agg.get_summary_async("005930")
        assert summary.sample_count == 100
        mock_repo.fetch_summary.assert_awaited_once()


class TestFallbackToJsonl:
    """TimescaleDB 실패 시 JSONL fallback."""

    @pytest.mark.asyncio
    async def test_repo_failure_falls_back(self):
        """repo 실패 시 JSONL fallback."""
        mock_repo = AsyncMock()
        mock_repo.fetch_summary.side_effect = Exception("DB connection failed")
        mock_db = MagicMock()
        mock_db.fetch_feedback_summary.return_value = FeedbackSummary(
            avg_slippage_bps=3.0,
            avg_market_impact_bps=1.0,
            avg_quality_score=0.80,
            avg_fill_latency_ms=20.0,
            avg_fill_ratio=0.90,
            sample_count=50,
        )
        agg = FeedbackAggregator(mock_db, feedback_repo=mock_repo)

        summary = await agg.get_summary_async("005930")
        assert summary.sample_count == 50
        assert summary.avg_slippage_bps == 3.0
