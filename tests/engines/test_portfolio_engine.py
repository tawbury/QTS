#!/usr/bin/env python3
"""
Portfolio Engine 테스트

- 계약 검증 중심: 출력(Summary/Position 필드·타입·범위)만 검증; Mock 호출 수에는 의존하지 않음.
- 경계값(빈 포지션) 및 결정적 픽스처로 회귀 안정성 확보.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, date

from src.strategy.engines.portfolio_engine import PortfolioEngine, Position, PortfolioSummary
from src.qts.core.config.config_models import UnifiedConfig


def _make_position_repo_mock():
    """결정적 포지션 픽스처만 반환하는 PositionRepository 목 (테스트 전용)."""
    # Data Contract: Symbol, Qty, Avg_Price(Current_Currency), Current_Price(Current_Currency), Sector, Strategy 등
    fixture = [
        {
            "Symbol": "AAPL",
            "Name": "Apple Inc",
            "Market": "US",
            "Qty": 10,
            "Avg_Price(Current_Currency)": 170.0,
            "Current_Price(Current_Currency)": 185.0,
            "Strategy": "Swing",
            "Sector": "Technology",
        },
        {
            "Symbol": "MSFT",
            "Name": "Microsoft",
            "Market": "US",
            "Qty": 5,
            "Avg_Price(Current_Currency)": 350.0,
            "Current_Price(Current_Currency)": 360.0,
            "Strategy": "Swing",
            "Sector": "Technology",
        },
    ]
    repo = AsyncMock()
    repo.get_all = AsyncMock(return_value=fixture)
    return repo


def _make_portfolio_repo_mock():
    """Portfolio KPI 업데이트용 목 (테스트 전용)."""
    repo = Mock()
    repo.update_kpi_overview = Mock(return_value=True)
    return repo


def _make_t_ledger_repo_mock():
    """T_Ledger 참조용 목 (테스트에서 호출되지 않아도 생성자에 필요)."""
    return Mock()


def _make_engine_with_positions(positions_fixture, base_equity=1_000_000.0):
    """계약 검증용: 결정적 포지션 픽스처로 엔진 생성 (Mock 의존 최소화)."""
    config = UnifiedConfig(config_map={"BASE_EQUITY": base_equity}, metadata={})
    position_repo = AsyncMock()
    position_repo.get_all = AsyncMock(return_value=positions_fixture)
    portfolio_repo = Mock()
    portfolio_repo.update_kpi_overview = Mock(return_value=True)
    return PortfolioEngine(
        config=config,
        position_repo=position_repo,
        portfolio_repo=portfolio_repo,
        t_ledger_repo=Mock(),
    )


class TestPortfolioEngine:
    """PortfolioEngine 테스트 (리포지토리 주입, Engine I/O Contract 정합)."""

    def setup_method(self):
        """테스트 설정: Position/Portfolio/T_Ledger 리포지토리 목 주입."""
        self.config = UnifiedConfig(
            config_map={"BASE_EQUITY": 1000000.0},
            metadata={},
        )
        self.position_repo = _make_position_repo_mock()
        self.portfolio_repo = _make_portfolio_repo_mock()
        self.t_ledger_repo = _make_t_ledger_repo_mock()
        self.engine = PortfolioEngine(
            config=self.config,
            position_repo=self.position_repo,
            portfolio_repo=self.portfolio_repo,
            t_ledger_repo=self.t_ledger_repo,
        )

    @pytest.mark.asyncio
    async def test_initialization(self):
        """초기화 테스트"""
        result = await self.engine.initialize()
        assert result is True
        assert self.engine.state.is_running is False

    @pytest.mark.asyncio
    async def test_start(self):
        """시작 테스트"""
        result = await self.engine.start()
        assert result is True
        assert self.engine.state.is_running is True

    @pytest.mark.asyncio
    async def test_stop(self):
        """중지 테스트"""
        result = await self.engine.stop()
        assert result is True
        assert self.engine.state.is_running is False

    @pytest.mark.asyncio
    async def test_get_portfolio_summary(self):
        """포트폴리오 요약 조회 테스트"""
        summary = await self.engine.get_portfolio_summary()

        assert isinstance(summary, PortfolioSummary)
        assert summary.total_equity > 0
        assert summary.holdings_count > 0
        assert "Technology" in summary.sector_allocation
        assert "Swing" in summary.strategy_allocation

    @pytest.mark.asyncio
    async def test_get_positions(self):
        """포지션 목록 조회 테스트"""
        positions = await self.engine.get_positions()

        assert isinstance(positions, list)
        assert len(positions) > 0

        for position in positions:
            assert isinstance(position, Position)
            assert position.symbol
            assert position.market_value >= 0

    @pytest.mark.asyncio
    async def test_update_portfolio_kpi(self):
        """성과 KPI 업데이트 테스트"""
        kpi_data = {
            "total_equity": 1000000.0,
            "daily_pnl": 5000.0,
            "exposure": 0.75,
        }

        result = await self.engine.update_portfolio_kpi(kpi_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_calculate_exposure(self):
        """노출 계산 테스트"""
        exposure = await self.engine.calculate_exposure()

        assert isinstance(exposure, float)
        assert 0.0 <= exposure <= 1.0

    @pytest.mark.asyncio
    async def test_get_sector_allocation(self):
        """섹터별 자산 배분 조회 테스트"""
        allocation = await self.engine.get_sector_allocation()

        assert isinstance(allocation, dict)
        assert len(allocation) > 0

        total_allocation = sum(allocation.values())
        assert abs(total_allocation - 1.0) < 0.01  # 합계가 1에 가까워야 함

    @pytest.mark.asyncio
    async def test_get_strategy_allocation(self):
        """전략별 자산 배분 조회 테스트"""
        allocation = await self.engine.get_strategy_allocation()

        assert isinstance(allocation, dict)
        assert len(allocation) > 0

        total_allocation = sum(allocation.values())
        assert abs(total_allocation - 1.0) < 0.01  # 합계가 1에 가까워야 함

    @pytest.mark.asyncio
    async def test_execute_operations(self):
        """실행 오퍼레이션 테스트 (Engine I/O Contract: success, data, error)."""
        # get_portfolio_summary
        result = await self.engine.execute({"operation": "get_portfolio_summary"})
        assert result["success"] is True
        assert "data" in result

        # get_positions
        result = await self.engine.execute({"operation": "get_positions"})
        assert result["success"] is True
        assert "data" in result

        # calculate_exposure
        result = await self.engine.execute({"operation": "calculate_exposure"})
        assert result["success"] is True
        assert "data" in result

        # 잘못된 오퍼레이션
        result = await self.engine.execute({"operation": "unknown"})
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_health_check(self):
        """헬스체크 테스트 (state_kind 포함)."""
        health = await self.engine.health_check()

        assert "status" in health
        assert "engine" in health
        assert "portfolio_health" in health
        assert health["engine"] == "PortfolioEngine"
        assert "state_kind" in health

        portfolio_health = health["portfolio_health"]
        assert "portfolio_summary" in portfolio_health
        assert "positions_count" in portfolio_health
        assert "cache_status" in portfolio_health


class TestPortfolioEngineBoundaryAndContract:
    """
    경계값(0/빈 포지션) 및 계약 검증.
    출력 형태·타입·값 범위 중심; Mock 호출 수가 아닌 엔진 출력만 검증.
    """

    @pytest.mark.asyncio
    async def test_empty_positions_boundary(self):
        """경계: 포지션 0건 → holdings_count 0, exposure 0, allocation 빈 dict"""
        engine = _make_engine_with_positions(positions_fixture=[])
        summary = await engine.get_portfolio_summary()
        assert isinstance(summary, PortfolioSummary)
        assert summary.holdings_count == 0
        assert summary.sector_allocation == {}
        assert summary.strategy_allocation == {}
        exposure = await engine.calculate_exposure()
        assert exposure == 0.0
        positions = await engine.get_positions()
        assert positions == []

    @pytest.mark.asyncio
    async def test_contract_summary_shape_and_ranges(self):
        """계약: PortfolioSummary 필드·타입·범위 (exposure 0~1, allocation 합 ≈1)."""
        engine = _make_engine_with_positions(
            positions_fixture=[
                {
                    "Symbol": "AAPL",
                    "Name": "Apple",
                    "Market": "US",
                    "Qty": 10,
                    "Avg_Price(Current_Currency)": 100.0,
                    "Current_Price(Current_Currency)": 110.0,
                    "Strategy": "Swing",
                    "Sector": "Technology",
                },
            ],
            base_equity=10000.0,
        )
        summary = await engine.get_portfolio_summary()
        assert hasattr(summary, "total_equity") and summary.total_equity >= 0
        assert hasattr(summary, "exposure") and 0.0 <= summary.exposure <= 1.0
        assert hasattr(summary, "cash_ratio") and 0.0 <= summary.cash_ratio <= 1.0
        total_sector = sum(summary.sector_allocation.values())
        total_strategy = sum(summary.strategy_allocation.values())
        assert abs(total_sector - 1.0) < 0.01 or total_sector == 0.0
        assert abs(total_strategy - 1.0) < 0.01 or total_strategy == 0.0

    @pytest.mark.asyncio
    async def test_contract_position_shape(self):
        """계약: Position 필드·타입 (market_value >= 0, quantity >= 0)."""
        engine = _make_engine_with_positions(
            positions_fixture=[
                {
                    "Symbol": "X",
                    "Name": "X",
                    "Market": "US",
                    "Qty": 1,
                    "Avg_Price(Current_Currency)": 50.0,
                    "Current_Price(Current_Currency)": 55.0,
                    "Strategy": "S",
                    "Sector": "T",
                },
            ],
        )
        positions = await engine.get_positions()
        assert len(positions) == 1
        pos = positions[0]
        assert pos.symbol == "X"
        assert pos.market_value >= 0
        assert pos.quantity >= 0


if __name__ == "__main__":
    pytest.main([__file__])
