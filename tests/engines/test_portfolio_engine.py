#!/usr/bin/env python3
"""
Portfolio Engine 테스트
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, date

from runtime.engines.portfolio_engine import PortfolioEngine, Position, PortfolioSummary
from runtime.config.config_models import UnifiedConfig, ConfigScope


class TestPortfolioEngine:
    """PortfolioEngine 테스트 클래스"""
    
    def setup_method(self):
        """테스트 설정"""
        self.config = UnifiedConfig(
            config_map={},
            metadata={}
        )
        self.engine = PortfolioEngine(self.config)
    
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
        assert 'Technology' in summary.sector_allocation
        assert 'Swing' in summary.strategy_allocation
    
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
        """포트폴리오 KPI 업데이트 테스트"""
        kpi_data = {
            'total_equity': 1000000.0,
            'daily_pnl': 5000.0,
            'exposure': 0.75
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
        """실행 오퍼레이션 테스트"""
        # get_portfolio_summary
        result = await self.engine.execute({'operation': 'get_portfolio_summary'})
        assert result['success'] is True
        assert 'data' in result
        
        # get_positions
        result = await self.engine.execute({'operation': 'get_positions'})
        assert result['success'] is True
        assert 'data' in result
        
        # calculate_exposure
        result = await self.engine.execute({'operation': 'calculate_exposure'})
        assert result['success'] is True
        assert 'data' in result
        
        # 잘못된 오퍼레이션 - PortfolioEngine은 ValueError를 발생시키지 않음
        result = await self.engine.execute({'operation': 'unknown'})
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """헬스체크 테스트"""
        health = await self.engine.health_check()
        
        assert 'status' in health
        assert 'engine' in health
        assert 'portfolio_health' in health
        assert health['engine'] == 'PortfolioEngine'
        
        portfolio_health = health['portfolio_health']
        assert 'portfolio_summary' in portfolio_health
        assert 'positions_count' in portfolio_health
        assert 'cache_status' in portfolio_health


if __name__ == "__main__":
    pytest.main([__file__])
