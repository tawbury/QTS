"""
Performance Engine

성과 추적, 수익률 계산, 리스크 지표, 통계 분석 등 성과 관련 비즈니스 로직을 구현합니다.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass, asdict
import asyncio
import statistics
import math

from .base_engine import BaseEngine, EngineState, EngineMetrics
from ..config.config_models import UnifiedConfig
from ..data.repositories.enhanced_performance_repository import EnhancedPerformanceRepository
from ..data.repositories.history_repository import HistoryRepository


@dataclass
class PerformanceMetrics:
    """성과 지표"""
    total_return: float
    mdd: float
    daily_volatility: float
    sharpe_ratio: float
    win_rate: float
    avg_win: float
    avg_loss: float
    max_consecutive_losses: int
    profit_factor: float
    calmar_ratio: float


@dataclass
class DailyPerformance:
    """일별 성과"""
    date: date
    total_equity: float
    daily_pnl: float
    daily_return: float
    cumulative_return: float
    volatility_20d: float
    high_watermark: float
    drawdown: float
    mdd: float


@dataclass
class MonthlyPerformance:
    """월별 성과"""
    month: str
    monthly_return: float
    cumulative_monthly_return: float
    mom_change: float
    volatility: float
    sharpe_ratio: float


class PerformanceEngine(BaseEngine):
    """
    성과 엔진
    
    성과 추적, 수익률 계산, 리스크 지표, 통계 분석 등 성과 관련 기능을 제공합니다.
    """
    
    def __init__(self, config: UnifiedConfig):
        """
        PerformanceEngine 초기화
        
        Args:
            config: 통합 설정 객체
        """
        super().__init__(config)
        
        # 리포지토리 인스턴스 (나중에 초기화)
        self._performance_repo: Optional[EnhancedPerformanceRepository] = None
        self._history_repo: Optional[HistoryRepository] = None
        
        # 캐시
        self._performance_cache: Optional[PerformanceMetrics] = None
        self._daily_performance_cache: List[DailyPerformance] = []
        self._monthly_performance_cache: List[MonthlyPerformance] = []
        self._last_cache_update: Optional[datetime] = None
        
        # 설정
        self._risk_free_rate = 0.02  # 무위험 이자율 (연 2%)
        self._trading_days_per_year = 252
        
        self.logger.info("PerformanceEngine created")
    
    async def initialize(self) -> bool:
        """
        성과 엔진 초기화
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            self.logger.info("Initializing PerformanceEngine...")
            
            # 리포지토리 초기화 (실제 구현에서는 의존성 주입 필요)
            # 여기서는 Mock으로 처리
            self._performance_repo = None  # 실제로는 의존성 주입 필요
            self._history_repo = None
            
            self._update_state(is_running=False)
            self.logger.info("PerformanceEngine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PerformanceEngine: {str(e)}")
            self._update_state(is_running=False, error=str(e))
            return False
    
    async def start(self) -> bool:
        """
        성과 엔진 시작
        
        Returns:
            bool: 시작 성공 여부
        """
        try:
            self.logger.info("Starting PerformanceEngine...")
            
            # 초기화 확인
            if not self._performance_repo:
                await self.initialize()
            
            self._update_state(is_running=True)
            await self._emit_event('engine_started', {'engine': 'PerformanceEngine'})
            
            self.logger.info("PerformanceEngine started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start PerformanceEngine: {str(e)}")
            self._update_state(is_running=False, error=str(e))
            return False
    
    async def stop(self) -> bool:
        """
        성과 엔진 중지
        
        Returns:
            bool: 중지 성공 여부
        """
        try:
            self.logger.info("Stopping PerformanceEngine...")
            
            self._update_state(is_running=False)
            await self._emit_event('engine_stopped', {'engine': 'PerformanceEngine'})
            
            self.logger.info("PerformanceEngine stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop PerformanceEngine: {str(e)}")
            return False
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        성과 엔진 실행
        
        Args:
            data: 실행 데이터
            
        Returns:
            Dict[str, Any]: 실행 결과
        """
        start_time = datetime.now()
        
        try:
            operation = data.get('operation')
            
            if operation == 'calculate_performance_metrics':
                result = await self.calculate_performance_metrics()
            elif operation == 'get_daily_performance':
                result = await self.get_daily_performance(data.get('start_date'), data.get('end_date'))
            elif operation == 'get_monthly_performance':
                result = await self.get_monthly_performance(data.get('year'))
            elif operation == 'update_performance_kpi':
                result = await self.update_performance_kpi(data.get('kpi_data', {}))
            elif operation == 'calculate_sharpe_ratio':
                result = self._calculate_sharpe_ratio(data.get('returns', []))
            elif operation == 'calculate_max_drawdown':
                result = self._calculate_max_drawdown_from_returns(data.get('equity_curve', []))
            elif operation == 'calculate_volatility':
                result = self._calculate_volatility(data.get('returns', []))
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(execution_time, success=True)
            
            return {
                'success': True,
                'data': result,
                'execution_time': execution_time
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(execution_time, success=False)
            self._update_state(is_running=True, error=str(e))
            
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time
            }
    
    async def calculate_performance_metrics(self) -> PerformanceMetrics:
        """
        성과 지표 계산
        
        Returns:
            PerformanceMetrics: 성과 지표
        """
        try:
            # 실제 구현에서는 HistoryRepository를 통해 데이터 조회
            # 여기서는 Mock 데이터로 계산
            daily_returns = self._generate_mock_daily_returns()
            
            total_return = self._calculate_total_return(daily_returns)
            mdd = self._calculate_max_drawdown_from_returns(daily_returns)
            volatility = self._calculate_volatility(daily_returns)
            sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
            
            win_rate, avg_win, avg_loss = self._calculate_trade_statistics(daily_returns)
            max_consecutive_losses = self._calculate_max_consecutive_losses(daily_returns)
            profit_factor = self._calculate_profit_factor(daily_returns)
            calmar_ratio = total_return / abs(mdd) if mdd != 0 else 0.0
            
            metrics = PerformanceMetrics(
                total_return=total_return,
                mdd=mdd,
                daily_volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                max_consecutive_losses=max_consecutive_losses,
                profit_factor=profit_factor,
                calmar_ratio=calmar_ratio
            )
            
            self._performance_cache = metrics
            self._last_cache_update = datetime.now()
            
            await self._emit_event('performance_metrics_calculated', asdict(metrics))
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to calculate performance metrics: {str(e)}")
            raise
    
    async def get_daily_performance(self, start_date: Optional[date] = None, 
                                   end_date: Optional[date] = None) -> List[DailyPerformance]:
        """
        일별 성과 조회
        
        Args:
            start_date: 시작일
            end_date: 종료일
            
        Returns:
            List[DailyPerformance]: 일별 성과 목록
        """
        try:
            # 실제 구현에서는 HistoryRepository를 통해 데이터 조회
            # 여기서는 Mock 데이터 반환
            mock_daily_perf = self._generate_mock_daily_performance(start_date, end_date)
            
            self._daily_performance_cache = mock_daily_perf
            
            await self._emit_event('daily_performance_updated', {
                'count': len(mock_daily_perf),
                'period': f"{start_date} to {end_date}"
            })
            
            return mock_daily_perf
            
        except Exception as e:
            self.logger.error(f"Failed to get daily performance: {str(e)}")
            raise
    
    async def get_monthly_performance(self, year: Optional[int] = None) -> List[MonthlyPerformance]:
        """
        월별 성과 조회
        
        Args:
            year: 연도 (None이면 현재 연도)
            
        Returns:
            List[MonthlyPerformance]: 월별 성과 목록
        """
        try:
            if year is None:
                year = datetime.now().year
            
            # 실제 구현에서는 HistoryRepository를 통해 데이터 조회
            # 여기서는 Mock 데이터 반환
            mock_monthly_perf = self._generate_mock_monthly_performance(year)
            
            self._monthly_performance_cache = mock_monthly_perf
            
            await self._emit_event('monthly_performance_updated', {
                'year': year,
                'count': len(mock_monthly_perf)
            })
            
            return mock_monthly_perf
            
        except Exception as e:
            self.logger.error(f"Failed to get monthly performance: {str(e)}")
            raise
    
    async def update_performance_kpi(self, kpi_data: Dict[str, Any]) -> bool:
        """
        성과 KPI 업데이트
        
        Args:
            kpi_data: KPI 데이터
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            # 실제 구현에서는 PerformanceRepository를 통해 데이터 업데이트
            self.logger.info(f"Updating performance KPI: {kpi_data}")
            
            await self._emit_event('performance_kpi_updated', kpi_data)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update performance KPI: {str(e)}")
            raise
    
    def _generate_mock_daily_returns(self) -> List[float]:
        """Mock 일별 수익률 데이터 생성"""
        # Mock: 252일 데이터 (1년)
        import random
        random.seed(42)
        
        returns = []
        for _ in range(252):
            # 정규분포에서 수익률 생성 (평균 0.001, 표준편차 0.02)
            daily_return = random.gauss(0.001, 0.02)
            returns.append(daily_return)
        
        return returns
    
    def _generate_mock_daily_performance(self, start_date: Optional[date], 
                                       end_date: Optional[date]) -> List[DailyPerformance]:
        """Mock 일별 성과 데이터 생성"""
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
        
        daily_perf = []
        current_date = start_date
        equity = 1000000.0  # 초기 자산
        cumulative_return = 0.0
        
        while current_date <= end_date:
            # Mock 일별 변동
            daily_pnl = equity * 0.001  # 0.1% 일별 변동
            equity += daily_pnl
            daily_return = daily_pnl / (equity - daily_pnl) if (equity - daily_pnl) != 0 else 0.0
            cumulative_return += daily_return
            
            perf = DailyPerformance(
                date=current_date,
                total_equity=equity,
                daily_pnl=daily_pnl,
                daily_return=daily_return,
                cumulative_return=cumulative_return,
                volatility_20d=0.02,  # Mock 값
                high_watermark=max(equity, 1000000.0),
                drawdown=max(0, 1000000.0 - equity),
                mdd=0.05  # Mock 값
            )
            
            daily_perf.append(perf)
            current_date += timedelta(days=1)
        
        return daily_perf
    
    def _generate_mock_monthly_performance(self, year: int) -> List[MonthlyPerformance]:
        """Mock 월별 성과 데이터 생성"""
        monthly_perf = []
        
        for month in range(1, 13):
            # Mock 월별 수익률
            monthly_return = 0.01 + (month - 7) * 0.005  # -2% ~ 3%
            cumulative_return = sum([
                0.01 + (m - 7) * 0.005 for m in range(1, month + 1)
            ])
            
            perf = MonthlyPerformance(
                month=f"{year}-{month:02d}",
                monthly_return=monthly_return,
                cumulative_monthly_return=cumulative_return,
                mom_change=monthly_return - (0.01 + (month - 8) * 0.005) if month > 1 else 0.0,
                volatility=0.15,  # Mock 값
                sharpe_ratio=monthly_return / 0.15 if 0.15 != 0 else 0.0
            )
            
            monthly_perf.append(perf)
        
        return monthly_perf
    
    def _calculate_total_return(self, returns: List[float]) -> float:
        """총 수익률 계산"""
        if not returns:
            return 0.0
        
        total_return = 1.0
        for r in returns:
            total_return *= (1 + r)
        
        return total_return - 1.0
    
    def _calculate_max_drawdown_from_returns(self, returns: List[float]) -> float:
        """수익률로부터 최대 낙폭 계산"""
        if not returns:
            return 0.0
        
        peak = 0.0
        cumulative = 0.0
        max_dd = 0.0
        
        for r in returns:
            cumulative += r
            if cumulative > peak:
                peak = cumulative
            
            dd = (peak - cumulative) / peak if peak != 0 else 0.0
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _calculate_volatility(self, returns: List[float]) -> float:
        """변동성 계산 (연율화)"""
        if len(returns) < 2:
            return 0.0
        
        mean_return = statistics.mean(returns)
        variance = statistics.variance(returns)
        daily_vol = math.sqrt(variance)
        
        # 연율화
        annual_vol = daily_vol * math.sqrt(self._trading_days_per_year)
        return annual_vol
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """샤프 비율 계산"""
        if len(returns) < 2:
            return 0.0
        
        mean_return = statistics.mean(returns)
        volatility = self._calculate_volatility(returns)
        
        # 연율화
        annual_return = mean_return * self._trading_days_per_year
        
        if volatility == 0:
            return 0.0
        
        return (annual_return - self._risk_free_rate) / volatility
    
    def _calculate_trade_statistics(self, returns: List[float]) -> Tuple[float, float, float]:
        """거래 통계 계산"""
        if not returns:
            return 0.0, 0.0, 0.0
        
        positive_returns = [r for r in returns if r > 0]
        negative_returns = [r for r in returns if r < 0]
        
        win_rate = len(positive_returns) / len(returns) if returns else 0.0
        avg_win = statistics.mean(positive_returns) if positive_returns else 0.0
        avg_loss = statistics.mean(negative_returns) if negative_returns else 0.0
        
        return win_rate, avg_win, avg_loss
    
    def _calculate_max_consecutive_losses(self, returns: List[float]) -> int:
        """최대 연속 손실 계산"""
        max_consecutive = 0
        current_consecutive = 0
        
        for r in returns:
            if r < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _calculate_profit_factor(self, returns: List[float]) -> float:
        """수익 팩터 계산"""
        positive_returns = [r for r in returns if r > 0]
        negative_returns = [abs(r) for r in returns if r < 0]
        
        if not negative_returns:
            return float('inf') if positive_returns else 0.0
        
        total_profit = sum(positive_returns)
        total_loss = sum(negative_returns)
        
        return total_profit / total_loss if total_loss != 0 else float('inf')
    
    async def health_check(self) -> Dict[str, Any]:
        """
        성과 엔진 헬스체크
        
        Returns:
            Dict[str, Any]: 헬스체크 결과
        """
        base_health = await super().health_check()
        
        try:
            # 성과 특정 헬스체크
            performance_metrics = await self.calculate_performance_metrics()
            daily_performance = await self.get_daily_performance()
            
            performance_health = {
                'current_metrics': asdict(performance_metrics),
                'daily_performance_count': len(daily_performance),
                'cache_status': {
                    'last_update': self._last_cache_update.isoformat() if self._last_cache_update else None,
                    'metrics_cached': self._performance_cache is not None,
                    'daily_cached': len(self._daily_performance_cache),
                    'monthly_cached': len(self._monthly_performance_cache)
                },
                'data_quality': {
                    'has_performance_data': len(daily_performance) > 0,
                    'date_range': {
                        'start': daily_performance[0].date.isoformat() if daily_performance else None,
                        'end': daily_performance[-1].date.isoformat() if daily_performance else None
                    } if daily_performance else None
                }
            }
            
            base_health['performance_health'] = performance_health
            
            return base_health
            
        except Exception as e:
            base_health['performance_health_error'] = str(e)
            return base_health
