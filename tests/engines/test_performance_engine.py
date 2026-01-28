#!/usr/bin/env python3
"""
Performance Engine 테스트
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, date

from runtime.engines.performance_engine import PerformanceEngine, PerformanceMetrics, DailyPerformance, MonthlyPerformance
from runtime.config.config_models import UnifiedConfig, ConfigScope


class TestPerformanceEngine:
    """PerformanceEngine 테스트 클래스"""
    
    def setup_method(self):
        """테스트 설정"""
        self.config = UnifiedConfig(
            config_map={},
            metadata={}
        )
        self.engine = PerformanceEngine(self.config)
    
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
    async def test_calculate_performance_metrics(self):
        """성과 지표 계산 테스트"""
        metrics = await self.engine.calculate_performance_metrics()
        
        assert isinstance(metrics, PerformanceMetrics)
        assert isinstance(metrics.total_return, float)
        assert isinstance(metrics.mdd, float)
        assert isinstance(metrics.sharpe_ratio, float)
        assert isinstance(metrics.win_rate, float)
        assert metrics.mdd >= 0  # MDD는 음수 또는 0
        assert 0.0 <= metrics.win_rate <= 1.0  # 승률은 0-1 사이
    
    @pytest.mark.asyncio
    async def test_get_daily_performance(self):
        """일별 성과 조회 테스트"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        daily_perf = await self.engine.get_daily_performance(start_date, end_date)
        
        assert isinstance(daily_perf, list)
        assert len(daily_perf) > 0
        
        for perf in daily_perf:
            assert isinstance(perf, DailyPerformance)
            assert isinstance(perf.date, date)
            assert isinstance(perf.total_equity, (int, float))
            assert isinstance(perf.daily_pnl, (int, float))
            assert isinstance(perf.daily_return, float)
    
    @pytest.mark.asyncio
    async def test_get_monthly_performance(self):
        """월별 성과 조회 테스트"""
        monthly_perf = await self.engine.get_monthly_performance(2024)
        
        assert isinstance(monthly_perf, list)
        assert len(monthly_perf) == 12  # 12개월
        
        for perf in monthly_perf:
            assert isinstance(perf, MonthlyPerformance)
            assert perf.month.startswith('2024-')
            assert isinstance(perf.monthly_return, float)
            assert isinstance(perf.cumulative_monthly_return, float)
    
    @pytest.mark.asyncio
    async def test_update_performance_kpi(self):
        """성과 KPI 업데이트 테스트"""
        kpi_data = {
            'total_return': 0.15,
            'mdd': -0.08,
            'sharpe': 1.25,
            'win_rate': 0.65
        }
        
        result = await self.engine.update_performance_kpi(kpi_data)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_execute_operations(self):
        """실행 오퍼레이션 테스트"""
        # calculate_performance_metrics
        result = await self.engine.execute({'operation': 'calculate_performance_metrics'})
        assert result['success'] is True
        assert 'data' in result
        
        # get_daily_performance
        result = await self.engine.execute({
            'operation': 'get_daily_performance',
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 1, 31)
        })
        assert result['success'] is True
        assert 'data' in result
        
        # get_monthly_performance
        result = await self.engine.execute({'operation': 'get_monthly_performance', 'year': 2024})
        assert result['success'] is True
        assert 'data' in result
        
        # calculate_sharpe_ratio
        result = await self.engine.execute({
            'operation': 'calculate_sharpe_ratio',
            'returns': [0.01, -0.02, 0.03, 0.01, -0.01]
        })
        assert result['success'] is True
        assert 'data' in result
        
        # 잘못된 오퍼레이션 - PerformanceEngine은 ValueError를 발생시키지 않음
        result = await self.engine.execute({'operation': 'unknown'})
        assert result['success'] is False
        assert 'error' in result
    
    def test_calculate_total_return(self):
        """총 수익률 계산 테스트"""
        # 빈 배열
        assert self.engine._calculate_total_return([]) == 0.0
        
        # 양수 배열
        returns = [0.01, 0.02, -0.01, 0.03]
        expected = (1.01 * 1.02 * 0.99 * 1.03) - 1.0
        actual = self.engine._calculate_total_return(returns)
        assert abs(actual - expected) < 0.0001
    
    def test_calculate_max_drawdown(self):
        """최대 낙폭 계산 테스트"""
        # 빈 배열
        assert self.engine._calculate_max_drawdown_from_returns([]) == 0.0
        
        # 테스트 데이터
        returns = [0.05, 0.03, -0.02, -0.04, -0.01, 0.02, 0.01]
        mdd = self.engine._calculate_max_drawdown_from_returns(returns)
        assert mdd > 0
    
    def test_calculate_volatility(self):
        """변동성 계산 테스트"""
        # 빈 배열
        assert self.engine._calculate_volatility([]) == 0.0
        
        # 테스트 데이터
        returns = [0.01, -0.01, 0.02, -0.02, 0.01]
        vol = self.engine._calculate_volatility(returns)
        assert vol > 0
    
    def test_calculate_sharpe_ratio(self):
        """샤프 비율 계산 테스트"""
        # 빈 배열
        assert self.engine._calculate_sharpe_ratio([]) == 0.0
        
        # 테스트 데이터
        returns = [0.01, 0.02, -0.01, 0.03]
        sharpe = self.engine._calculate_sharpe_ratio(returns)
        assert isinstance(sharpe, float)
    
    def test_calculate_trade_statistics(self):
        """거래 통계 계산 테스트"""
        # 빈 배열
        win_rate, avg_win, avg_loss = self.engine._calculate_trade_statistics([])
        assert win_rate == 0.0
        assert avg_win == 0.0
        assert avg_loss == 0.0
        
        # 테스트 데이터
        returns = [0.01, -0.01, 0.02, -0.02, 0.03, -0.01]
        win_rate, avg_win, avg_loss = self.engine._calculate_trade_statistics(returns)
        assert 0.0 <= win_rate <= 1.0
        assert avg_win > 0
        assert avg_loss < 0
    
    def test_calculate_max_consecutive_losses(self):
        """최대 연속 손실 계산 테스트"""
        # 빈 배열
        assert self.engine._calculate_max_consecutive_losses([]) == 0
        
        # 테스트 데이터
        returns = [0.01, -0.01, -0.02, -0.01, 0.02, -0.03, -0.01]
        max_consecutive = self.engine._calculate_max_consecutive_losses(returns)
        assert max_consecutive == 3
    
    def test_calculate_profit_factor(self):
        """수익 팩터 계산 테스트"""
        # 빈 배열
        assert self.engine._calculate_profit_factor([]) == 0.0
        
        # 양수만 있는 경우
        returns = [0.01, 0.02, 0.03]
        assert self.engine._calculate_profit_factor(returns) == float('inf')
        
        # 손익과 손실이 있는 경우
        returns = [0.01, -0.01, 0.02, -0.02, 0.03, -0.01]
        profit_factor = self.engine._calculate_profit_factor(returns)
        assert profit_factor > 0
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """헬스체크 테스트"""
        health = await self.engine.health_check()
        
        assert 'status' in health
        assert 'engine' in health
        assert 'performance_health' in health
        assert health['engine'] == 'PerformanceEngine'
        
        performance_health = health['performance_health']
        assert 'current_metrics' in performance_health
        assert 'daily_performance_count' in performance_health
        assert 'cache_status' in performance_health


if __name__ == "__main__":
    pytest.main([__file__])
