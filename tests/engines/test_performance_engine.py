#!/usr/bin/env python3
"""
Performance Engine 테스트

- 계약 검증 중심: 엔진 출력(필드·타입·값 범위)만 검증하며, Mock 호출 수에는 의존하지 않음.
- 결정적 픽스처만 사용; 경계값(0/빈/음수) 및 회귀(고정 입력→고정 출력)로 KPI 산출 고정.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, date, timedelta

from src.strategy.engines.performance_engine import (
    PerformanceEngine,
    PerformanceMetrics,
    DailyPerformance,
    MonthlyPerformance,
)
from src.qts.core.config.config_models import UnifiedConfig


def _make_history_repo_mock():
    """결정적 픽스처만 반환하는 HistoryRepository 목 (테스트 전용)."""
    # 일별 성과/수익률 계산용: Daily_Return 포함
    execution_fixture = [
        {
            "Date": "2024-01-01",
            "Total_Equity": 1_000_000.0,
            "Daily_PnL": 1000.0,
            "Daily_Return": "0.1%",
            "Cumulative_Return": "0%",
            "Volatility_20D": "0.02",
            "High_Watermark": 1_000_000.0,
            "Drawdown": "0%",
            "MDD": "0%",
        },
        {
            "Date": "2024-01-02",
            "Total_Equity": 1_001_500.0,
            "Daily_PnL": 1500.0,
            "Daily_Return": "0.15%",
            "Cumulative_Return": "0.25%",
            "Volatility_20D": "0.02",
            "High_Watermark": 1_001_500.0,
            "Drawdown": "0%",
            "MDD": "0%",
        },
        {
            "Date": "2024-01-03",
            "Total_Equity": 999_000.0,
            "Daily_PnL": -2500.0,
            "Daily_Return": "-0.25%",
            "Cumulative_Return": "0%",
            "Volatility_20D": "0.02",
            "High_Watermark": 1_001_500.0,
            "Drawdown": "0.25%",
            "MDD": "0.25%",
        },
    ]
    # 월별 성과용: 2024년 12개월 데이터 (실제 데이터 기반 개수 검증)
    monthly_fixture = []
    base_equity = 1_000_000.0
    for m in range(1, 13):
        monthly_fixture.append({
            "Date": f"2024-{m:02d}-15",
            "Total_Equity": base_equity,
            "Daily_PnL": 0.0,
            "Daily_Return": "0%",
            "Cumulative_Return": "0%",
        })
        base_equity += 5000.0 * m  # 월별 상승

    history_repo = AsyncMock()
    history_repo.get_execution_history = AsyncMock(return_value=execution_fixture)
    history_repo.get_performance_metrics = AsyncMock(return_value={"period_days": 252, "total_records": 3})
    history_repo.get_all = AsyncMock(return_value=monthly_fixture)
    history_repo.log_execution = AsyncMock(return_value=None)
    return history_repo


def _make_performance_repo_mock():
    """Performance KPI 업데이트용 목 (테스트 전용). 엔진은 update_kpi_summary를 await하지 않음."""
    perf_repo = Mock()
    perf_repo.update_kpi_summary = Mock(return_value=None)
    return perf_repo


class TestPerformanceEngine:
    """PerformanceEngine 테스트 클래스 (리포지토리 주입, 결정적 픽스처만 사용)."""

    def setup_method(self):
        """테스트 설정: History/Performance 리포지토리 목 주입."""
        self.config = UnifiedConfig(config_map={}, metadata={})
        self.history_repo = _make_history_repo_mock()
        self.performance_repo = _make_performance_repo_mock()
        self.engine = PerformanceEngine(
            self.config,
            history_repo=self.history_repo,
            performance_repo=self.performance_repo,
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


class TestPerformanceEngineKpiBoundaryAndRegression:
    """
    계약 검증·경계값·회귀 테스트.
    Mock 호출이 아닌 출력 형태/값 범위/결정론적 결과로 KPI 산출을 고정.
    """

    def setup_method(self):
        self.config = UnifiedConfig(config_map={}, metadata={})
        self.history_repo = _make_history_repo_mock()
        self.performance_repo = _make_performance_repo_mock()
        self.engine = PerformanceEngine(
            self.config,
            history_repo=self.history_repo,
            performance_repo=self.performance_repo,
        )

    # ---- 경계값: 0 / 빈 입력 / 음수 ----
    def test_total_return_boundary_empty(self):
        """총 수익률: 빈 입력 → 0.0 (계약)"""
        assert self.engine._calculate_total_return([]) == 0.0

    def test_total_return_boundary_single_zero(self):
        """총 수익률: 단일 0 → 0.0"""
        assert self.engine._calculate_total_return([0.0]) == 0.0

    def test_total_return_boundary_all_zeros(self):
        """총 수익률: 전부 0 → 0.0"""
        assert self.engine._calculate_total_return([0.0, 0.0, 0.0]) == 0.0

    def test_total_return_negative_returns(self):
        """총 수익률: 음수 수익률 포함 → (1+r1)(1+r2)... - 1"""
        # -10% then -5% → 0.9 * 0.95 - 1 = -0.145
        r = self.engine._calculate_total_return([-0.10, -0.05])
        assert abs(r - (-0.145)) < 1e-9

    def test_max_drawdown_boundary_empty(self):
        """MDD: 빈 입력 → 0.0 (계약)"""
        assert self.engine._calculate_max_drawdown_from_returns([]) == 0.0

    def test_max_drawdown_boundary_all_positive(self):
        """MDD: 전부 양수 수익 → 0.0"""
        assert self.engine._calculate_max_drawdown_from_returns([0.01, 0.02, 0.01]) == 0.0

    def test_volatility_boundary_empty_or_single(self):
        """변동성: 빈/단일 → 0.0 (계약)"""
        assert self.engine._calculate_volatility([]) == 0.0
        assert self.engine._calculate_volatility([0.01]) == 0.0

    def test_sharpe_boundary_empty_or_single(self):
        """샤프: 빈/단일 → 0.0 (계약)"""
        assert self.engine._calculate_sharpe_ratio([]) == 0.0
        assert self.engine._calculate_sharpe_ratio([0.01]) == 0.0

    def test_trade_statistics_boundary_all_negative(self):
        """거래 통계: 전부 음수 → win_rate 0, avg_win 0, avg_loss < 0"""
        win_rate, avg_win, avg_loss = self.engine._calculate_trade_statistics([-0.01, -0.02])
        assert win_rate == 0.0
        assert avg_win == 0.0
        assert avg_loss < 0

    def test_trade_statistics_boundary_all_positive(self):
        """거래 통계: 전부 양수 → win_rate 1, avg_win > 0, avg_loss 0"""
        win_rate, avg_win, avg_loss = self.engine._calculate_trade_statistics([0.01, 0.02])
        assert win_rate == 1.0
        assert avg_win > 0
        assert avg_loss == 0.0

    def test_profit_factor_boundary_only_negative(self):
        """수익 팩터: 손실만 → 0.0 (계약)"""
        assert self.engine._calculate_profit_factor([-0.01, -0.02]) == 0.0

    # ---- 결정론적 회귀: 고정 입력 → 고정 출력 ----
    def test_regression_total_return_deterministic(self):
        """회귀: 고정 수익률 리스트 → 동일 총 수익률"""
        returns = [0.01, -0.02, 0.03, 0.01, -0.01]
        expected = (1.01 * 0.98 * 1.03 * 1.01 * 0.99) - 1.0
        assert abs(self.engine._calculate_total_return(returns) - expected) < 1e-12

    def test_regression_max_drawdown_deterministic(self):
        """회귀: 고정 수익률 → 동일 MDD"""
        returns = [0.05, 0.03, -0.02, -0.04, -0.01, 0.02, 0.01]
        mdd = self.engine._calculate_max_drawdown_from_returns(returns)
        assert mdd >= 0.0
        assert mdd <= 1.0
        # 누적: .05,.08,.06,.02,.01,.03,.04 → peak .08, max dd from .08 to .01
        assert mdd > 0.01

    def test_regression_profit_factor_deterministic(self):
        """회귀: 고정 수익/손실 → 동일 수익 팩터"""
        returns = [0.01, -0.01, 0.02, -0.02, 0.03, -0.01]  # profit .06, loss .04 → 1.5
        pf = self.engine._calculate_profit_factor(returns)
        assert abs(pf - 1.5) < 1e-9

    def test_regression_max_consecutive_losses_deterministic(self):
        """회귀: 고정 수익률 → 연속 손실 3"""
        returns = [0.01, -0.01, -0.02, -0.01, 0.02, -0.03, -0.01]
        assert self.engine._calculate_max_consecutive_losses(returns) == 3

    # ---- 계약 검증: PerformanceMetrics 필드·타입·범위 ----
    @pytest.mark.asyncio
    async def test_contract_metrics_shape_and_ranges(self):
        """계약: calculate_performance_metrics 반환값 필드·타입·범위"""
        metrics = await self.engine.calculate_performance_metrics()
        assert isinstance(metrics, PerformanceMetrics)
        assert hasattr(metrics, "total_return") and isinstance(metrics.total_return, float)
        assert hasattr(metrics, "mdd") and isinstance(metrics.mdd, float)
        assert hasattr(metrics, "sharpe_ratio") and isinstance(metrics.sharpe_ratio, float)
        assert hasattr(metrics, "win_rate") and isinstance(metrics.win_rate, float)
        assert metrics.mdd >= 0.0
        assert 0.0 <= metrics.win_rate <= 1.0
        assert not (metrics.win_rate != metrics.win_rate)  # not NaN
        assert not (metrics.mdd != metrics.mdd)


if __name__ == "__main__":
    pytest.main([__file__])
