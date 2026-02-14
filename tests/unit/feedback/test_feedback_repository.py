"""FeedbackRepository 단위 테스트.

근거: docs/02-design/features/eteda-db-feedback-loop.design.md T-01
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.db.repositories.feedback_repository import FeedbackRepository
from src.feedback.contracts import FeedbackData, FeedbackSummary, DEFAULT_FEEDBACK_SUMMARY


@pytest.fixture
def mock_pool():
    pool = AsyncMock()
    return pool


@pytest.fixture
def repo(mock_pool):
    return FeedbackRepository(mock_pool)


def _make_feedback(**overrides) -> FeedbackData:
    from datetime import datetime, timezone
    from decimal import Decimal
    defaults = dict(
        symbol="005930",
        execution_start=datetime.now(timezone.utc),
        execution_end=datetime.now(timezone.utc),
        feedback_generated_at=datetime.now(timezone.utc),
        scalp_ticks=[],
        total_slippage_bps=1.5,
        avg_fill_latency_ms=12.3,
        partial_fill_ratio=0.0,
        total_filled_qty=Decimal("10"),
        avg_fill_price=Decimal("70000"),
        volatility_at_execution=0.02,
        spread_at_execution=3.0,
        depth_at_execution=100,
        execution_quality_score=0.85,
        market_impact_bps=0.5,
        strategy_tag="scalp",
        order_type="MARKET",
        original_qty=Decimal("10"),
    )
    defaults.update(overrides)
    return FeedbackData(**defaults)


@pytest.mark.asyncio
async def test_store_calls_pool_execute(repo, mock_pool):
    """저장 시 pool.execute가 호출되는지 확인."""
    feedback = _make_feedback()
    await repo.store(feedback)
    mock_pool.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_fetch_summary_with_data(repo, mock_pool):
    """데이터 존재 시 FeedbackSummary 반환."""
    mock_pool.fetchrow.return_value = {
        "avg_slippage_bps": 2.0,
        "avg_impact_bps": 0.5,
        "avg_quality_score": 0.9,
        "avg_fill_latency_ms": 10.0,
        "avg_fill_ratio": 0.95,
        "sample_count": 15,
    }
    summary = await repo.fetch_summary("005930", lookback_hours=24)
    assert isinstance(summary, FeedbackSummary)
    assert summary.sample_count == 15
    assert summary.avg_slippage_bps == 2.0
    assert summary.avg_quality_score == 0.9


@pytest.mark.asyncio
async def test_fetch_summary_by_strategy(repo, mock_pool):
    """전략별 분리 집계."""
    mock_pool.fetchrow.return_value = {
        "avg_slippage_bps": 1.0,
        "avg_impact_bps": 0.3,
        "avg_quality_score": 0.95,
        "avg_fill_latency_ms": 8.0,
        "avg_fill_ratio": 0.98,
        "sample_count": 10,
    }
    summary = await repo.fetch_summary_by_strategy("005930", "scalp", lookback_hours=24)
    assert isinstance(summary, FeedbackSummary)
    assert summary.sample_count == 10
    assert summary.avg_slippage_bps == 1.0


@pytest.mark.asyncio
async def test_fetch_recent(repo, mock_pool):
    """최근 N건 조회."""
    mock_pool.fetch.return_value = [
        {
            "time": "2026-02-14T10:00:00",
            "symbol": "005930",
            "strategy_tag": "scalp",
            "slippage_bps": 1.5,
            "quality_score": 0.9,
            "impact_bps": 0.5,
            "fill_latency_ms": 10.0,
            "fill_ratio": 1.0,
            "filled_qty": 10,
            "fill_price": 70000,
            "original_qty": 10,
            "volatility": 0.02,
            "spread_bps": 3.0,
            "depth": 100,
            "order_type": "MARKET",
        },
    ]
    results = await repo.fetch_recent("005930", limit=5)
    assert len(results) == 1


@pytest.mark.asyncio
async def test_empty_summary_returns_default(repo, mock_pool):
    """데이터 없을 때 기본값."""
    mock_pool.fetchrow.return_value = {
        "avg_slippage_bps": None,
        "avg_impact_bps": None,
        "avg_quality_score": None,
        "avg_fill_latency_ms": None,
        "avg_fill_ratio": None,
        "sample_count": 0,
    }
    summary = await repo.fetch_summary("UNKNOWN", lookback_hours=24)
    assert summary == DEFAULT_FEEDBACK_SUMMARY
