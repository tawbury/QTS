"""FeedbackQueryService 단위 테스트.

근거: docs/02-design/features/eteda-db-feedback-loop.design.md T-02
"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.feedback.query_service import FeedbackQueryService


@pytest.fixture
def mock_pool():
    return AsyncMock()


@pytest.fixture
def service(mock_pool):
    return FeedbackQueryService(mock_pool)


@pytest.mark.asyncio
async def test_hourly_slippage_pattern(service, mock_pool):
    """시간대별 슬리피지 분포."""
    mock_pool.fetch.return_value = [
        {"hour": 9, "avg_slippage": 2.5},
        {"hour": 10, "avg_slippage": 1.8},
        {"hour": 14, "avg_slippage": 3.2},
    ]
    result = await service.get_hourly_slippage_pattern("005930", days=7)
    assert result[9] == 2.5
    assert result[10] == 1.8
    assert result[14] == 3.2


@pytest.mark.asyncio
async def test_strategy_comparison(service, mock_pool):
    """SCALP vs SWING 비교."""
    mock_pool.fetch.return_value = [
        {
            "strategy_tag": "scalp",
            "avg_slippage_bps": 2.0,
            "avg_impact_bps": 0.5,
            "avg_quality_score": 0.9,
            "avg_fill_latency_ms": 10.0,
            "avg_fill_ratio": 0.98,
            "sample_count": 50,
        },
        {
            "strategy_tag": "swing",
            "avg_slippage_bps": 1.0,
            "avg_impact_bps": 0.3,
            "avg_quality_score": 0.95,
            "avg_fill_latency_ms": 15.0,
            "avg_fill_ratio": 0.99,
            "sample_count": 20,
        },
    ]
    result = await service.get_strategy_comparison("005930", lookback_hours=24)
    assert "scalp" in result
    assert "swing" in result
    assert result["scalp"].sample_count == 50
    assert result["swing"].avg_slippage_bps == 1.0


@pytest.mark.asyncio
async def test_quality_trend(service, mock_pool):
    """일별 품질 점수 추이."""
    from datetime import datetime
    mock_pool.fetch.return_value = [
        {
            "day": datetime(2026, 2, 13),
            "avg_quality": 0.85,
            "avg_slippage": 2.1,
            "sample_count": 30,
        },
        {
            "day": datetime(2026, 2, 14),
            "avg_quality": 0.90,
            "avg_slippage": 1.8,
            "sample_count": 25,
        },
    ]
    result = await service.get_quality_trend("005930", days=7)
    assert len(result) == 2
    assert result[0]["avg_quality"] == 0.85
    assert result[1]["sample_count"] == 25


@pytest.mark.asyncio
async def test_degradation_alert_triggered(service, mock_pool):
    """슬리피지 열화 감지."""
    mock_pool.fetchrow.return_value = {
        "recent_slippage": 6.0,
        "recent_count": 10,
        "daily_slippage": 3.0,
        "daily_count": 50,
    }
    result = await service.get_degradation_alert("005930")
    assert result is not None
    assert result["alert_type"] == "SLIPPAGE_DEGRADATION"
    assert result["degradation_ratio"] == 2.0


@pytest.mark.asyncio
async def test_no_degradation(service, mock_pool):
    """정상 시 None 반환."""
    mock_pool.fetchrow.return_value = {
        "recent_slippage": 2.0,
        "recent_count": 10,
        "daily_slippage": 2.5,
        "daily_count": 50,
    }
    result = await service.get_degradation_alert("005930")
    assert result is None


@pytest.mark.asyncio
async def test_degradation_insufficient_samples(service, mock_pool):
    """샘플 부족 시 None 반환."""
    mock_pool.fetchrow.return_value = {
        "recent_slippage": 10.0,
        "recent_count": 1,
        "daily_slippage": 2.0,
        "daily_count": 2,
    }
    result = await service.get_degradation_alert("005930")
    assert result is None
