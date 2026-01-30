#!/usr/bin/env python3
"""
Strategy 리포지토리 단위 테스트

클라이언트 목 주입으로 계약(get_all/get_by_id 반환 형태)만 검증. Google Sheets 미연동.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from runtime.data.repositories.strategy_repository import StrategyRepository


def _mock_client_empty_sheet():
    """빈 시트 반환하는 목 클라이언트."""
    client = Mock()
    client.get_sheet_data = AsyncMock(return_value=[])
    return client


class TestStrategyRepository:
    """StrategyRepository 계약 검증."""

    @pytest.mark.asyncio
    async def test_get_all_empty(self):
        client = _mock_client_empty_sheet()
        repo = StrategyRepository(client, "sid")
        repo.get_headers = AsyncMock(return_value=[])
        result = await repo.get_all()
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_by_id_missing(self):
        client = _mock_client_empty_sheet()
        repo = StrategyRepository(client, "sid")
        repo.get_all = AsyncMock(return_value=[])
        result = await repo.get_by_id("rsi_period")
        assert result is None
