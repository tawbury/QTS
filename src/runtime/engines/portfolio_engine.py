"""
Portfolio Engine

포트폴리오 관리, 포지션 추적, 자산 배분 등 포트폴리오 관련 비즈니스 로직을 구현합니다.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass, asdict
import asyncio

from .base_engine import BaseEngine, EngineState, EngineMetrics
from ..config.config_models import UnifiedConfig
from ..data.repositories.enhanced_portfolio_repository import EnhancedPortfolioRepository
from ..data.repositories.position_repository import PositionRepository
from ..data.repositories.t_ledger_repository import T_LedgerRepository


@dataclass
class Position:
    """포지션 정보"""
    symbol: str
    name: str
    market: str
    quantity: float
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    strategy: str
    sector: str


@dataclass
class PortfolioSummary:
    """포트폴리오 요약 정보"""
    total_equity: float
    daily_pnl: float
    exposure: float
    cash_ratio: float
    holdings_count: int
    killswitch_status: str
    sector_allocation: Dict[str, float]
    strategy_allocation: Dict[str, float]


class PortfolioEngine(BaseEngine):
    """
    포트폴리오 엔진
    
    포지션 관리, 자산 배분, 리스크 모니터링 등 포트폴리오 관련 기능을 제공합니다.
    """
    
    def __init__(
        self,
        config: UnifiedConfig,
        position_repo: PositionRepository,
        portfolio_repo: EnhancedPortfolioRepository,
        t_ledger_repo: T_LedgerRepository
    ):
        """
        PortfolioEngine 초기화
        
        Args:
            config: 통합 설정 객체
            position_repo: Position 리포지토리
            portfolio_repo: Enhanced Portfolio 리포지토리
            t_ledger_repo: T_Ledger 리포지토리
        """
        super().__init__(config)
        
        # 리포지토리 인스턴스 (의존성 주입)
        self._portfolio_repo: EnhancedPortfolioRepository = portfolio_repo
        self._position_repo: PositionRepository = position_repo
        self._t_ledger_repo: T_LedgerRepository = t_ledger_repo
        
        # 캐시
        self._positions_cache: Dict[str, Position] = {}
        self._portfolio_summary_cache: Optional[PortfolioSummary] = None
        self._last_cache_update: Optional[datetime] = None
        
        self.logger.info("PortfolioEngine created with injected repositories")
    
    async def initialize(self) -> bool:
        """
        포트폴리오 엔진 초기화
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            self.logger.info("Initializing PortfolioEngine...")
            
            # 리포지토리는 생성자에서 주입됨
            # 리포지토리 유효성 검사
            if not self._position_repo or not self._portfolio_repo or not self._t_ledger_repo:
                raise ValueError("All repositories must be provided via constructor")
            
            self._update_state(is_running=False)
            self.logger.info("PortfolioEngine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PortfolioEngine: {str(e)}")
            self._update_state(is_running=False, error=str(e))
            return False
    
    async def start(self) -> bool:
        """
        포트폴리오 엔진 시작
        
        Returns:
            bool: 시작 성공 여부
        """
        try:
            self.logger.info("Starting PortfolioEngine...")
            
            # 초기화 확인
            if not self._portfolio_repo:
                await self.initialize()
            
            self._update_state(is_running=True)
            await self._emit_event('engine_started', {'engine': 'PortfolioEngine'})
            
            self.logger.info("PortfolioEngine started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start PortfolioEngine: {str(e)}")
            self._update_state(is_running=False, error=str(e))
            return False
    
    async def stop(self) -> bool:
        """
        포트폴리오 엔진 중지
        
        Returns:
            bool: 중지 성공 여부
        """
        try:
            self.logger.info("Stopping PortfolioEngine...")
            
            self._update_state(is_running=False)
            await self._emit_event('engine_stopped', {'engine': 'PortfolioEngine'})
            
            self.logger.info("PortfolioEngine stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop PortfolioEngine: {str(e)}")
            return False
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        포트폴리오 엔진 실행
        
        Args:
            data: 실행 데이터
            
        Returns:
            Dict[str, Any]: 실행 결과
        """
        start_time = datetime.now()
        
        try:
            operation = data.get('operation')
            
            if operation == 'get_portfolio_summary':
                result = await self.get_portfolio_summary()
            elif operation == 'get_positions':
                result = await self.get_positions()
            elif operation == 'update_portfolio_kpi':
                result = await self.update_portfolio_kpi(data.get('kpi_data', {}))
            elif operation == 'calculate_exposure':
                result = await self.calculate_exposure()
            elif operation == 'get_sector_allocation':
                result = await self.get_sector_allocation()
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
    
    async def get_portfolio_summary(self) -> PortfolioSummary:
        """
        포트폴리오 요약 정보 조회
        
        Returns:
            PortfolioSummary: 포트폴리오 요약
        """
        try:
            # 실제 데이터로 요약 생성
            positions = await self.get_positions()
            
            # 기본 지표 계산
            total_market_value = sum(pos.market_value for pos in positions)
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
            total_equity = float(self.config.get('BASE_EQUITY', 1000000.0))
            
            # Exposure 계산
            exposure = await self.calculate_exposure()
            
            # Cash ratio 계산
            cash_ratio = 1.0 - exposure if exposure <= 1.0 else 0.0
            
            # 섹터/전략 배분
            sector_allocation = await self.get_sector_allocation()
            strategy_allocation = await self.get_strategy_allocation()
            
            # Killswitch 상태 (config에서 가져오기)
            killswitch_status = self.config.get('KILLSWITCH_STATUS', 'ACTIVE')
            
            summary = PortfolioSummary(
                total_equity=total_equity,
                daily_pnl=total_unrealized_pnl,  # 일일 PnL은 별도 계산 필요
                exposure=exposure,
                cash_ratio=cash_ratio,
                holdings_count=len(positions),
                killswitch_status=killswitch_status,
                sector_allocation=sector_allocation,
                strategy_allocation=strategy_allocation
            )
            
            self._portfolio_summary_cache = summary
            self._last_cache_update = datetime.now()
            
            await self._emit_event('portfolio_summary_updated', asdict(summary))
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get portfolio summary: {str(e)}")
            raise
    
    async def get_positions(self) -> List[Position]:
        """
        현재 포지션 목록 조회
        
        Returns:
            List[Position]: 포지션 목록
        """
        try:
            # PositionRepository를 통해 실제 데이터 조회
            raw_positions = await self._position_repo.get_all()
            
            positions = []
            for raw_pos in raw_positions:
                try:
                    # 데이터 변환 및 검증
                    qty = float(raw_pos.get('Qty', 0))
                    avg_price = float(raw_pos.get('Avg_Price(Current_Currency)', 0))
                    current_price = float(raw_pos.get('Current_Price(Current_Currency)', 0))
                    
                    # 수량이 0이면 스킵
                    if qty == 0:
                        continue
                    
                    # 미실현 손익 계산
                    market_value = current_price * qty
                    unrealized_pnl = (current_price - avg_price) * qty
                    unrealized_pnl_pct = ((current_price - avg_price) / avg_price) if avg_price != 0 else 0.0
                    
                    position = Position(
                        symbol=raw_pos.get('Symbol', ''),
                        name=raw_pos.get('Name', ''),
                        market=raw_pos.get('Market', ''),
                        quantity=qty,
                        avg_price=avg_price,
                        current_price=current_price,
                        market_value=market_value,
                        unrealized_pnl=unrealized_pnl,
                        unrealized_pnl_pct=unrealized_pnl_pct,
                        strategy=raw_pos.get('Strategy', ''),
                        sector=raw_pos.get('Sector', '')
                    )
                    
                    positions.append(position)
                    
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Failed to parse position {raw_pos.get('Symbol', 'UNKNOWN')}: {str(e)}")
                    continue
            
            # 캐시 업데이트
            self._positions_cache = {pos.symbol: pos for pos in positions}
            
            await self._emit_event('positions_updated', {
                'positions': [asdict(pos) for pos in positions],
                'count': len(positions)
            })
            
            return positions
            
        except Exception as e:
            self.logger.error(f"Failed to get positions: {str(e)}")
            raise
    
    async def update_portfolio_kpi(self, kpi_data: Dict[str, Any]) -> bool:
        """
        포트폴리오 KPI 업데이트
        
        Args:
            kpi_data: KPI 데이터
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            # EnhancedPortfolioRepository를 통해 KPI 업데이트
            success = self._portfolio_repo.update_kpi_overview(kpi_data)
            
            if success:
                self.logger.info(f"Portfolio KPI updated successfully: {kpi_data}")
                await self._emit_event('portfolio_kpi_updated', kpi_data)
            else:
                self.logger.error("Failed to update portfolio KPI")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update portfolio KPI: {str(e)}")
            raise
    
    async def calculate_exposure(self) -> float:
        """
        노출 계산
        
        Returns:
            float: 노출 비율 (0-1)
        """
        try:
            positions = await self.get_positions()
            total_market_value = sum(pos.market_value for pos in positions)
            
            # 총 자산은 config에서 가져오거나 Portfolio sheet KPI에서 조회
            # 여기서는 config의 BASE_EQUITY 사용
            total_equity = float(self.config.get('BASE_EQUITY', 1000000.0))
            
            exposure = total_market_value / total_equity if total_equity > 0 else 0.0
            
            await self._emit_event('exposure_calculated', {'exposure': exposure})
            
            return min(exposure, 1.0)  # 1을 초과하지 않도록 제한
            
        except Exception as e:
            self.logger.error(f"Failed to calculate exposure: {str(e)}")
            raise
    
    async def get_sector_allocation(self) -> Dict[str, float]:
        """
        섹터별 자산 배분 조회
        
        Returns:
            Dict[str, float]: 섹터별 배분 비율
        """
        try:
            positions = await self.get_positions()
            sector_values = {}
            
            for position in positions:
                sector = position.sector
                if sector not in sector_values:
                    sector_values[sector] = 0.0
                sector_values[sector] += position.market_value
            
            total_value = sum(sector_values.values())
            allocation = {
                sector: value / total_value 
                for sector, value in sector_values.items()
            } if total_value > 0 else {}
            
            await self._emit_event('sector_allocation_updated', allocation)
            
            return allocation
            
        except Exception as e:
            self.logger.error(f"Failed to get sector allocation: {str(e)}")
            raise
    
    async def get_strategy_allocation(self) -> Dict[str, float]:
        """
        전략별 자산 배분 조회
        
        Returns:
            Dict[str, float]: 전략별 배분 비율
        """
        try:
            positions = await self.get_positions()
            strategy_values = {}
            
            for position in positions:
                strategy = position.strategy
                if strategy not in strategy_values:
                    strategy_values[strategy] = 0.0
                strategy_values[strategy] += position.market_value
            
            total_value = sum(strategy_values.values())
            allocation = {
                strategy: value / total_value 
                for strategy, value in strategy_values.items()
            } if total_value > 0 else {}
            
            await self._emit_event('strategy_allocation_updated', allocation)
            
            return allocation
            
        except Exception as e:
            self.logger.error(f"Failed to get strategy allocation: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        포트폴리오 엔진 헬스체크
        
        Returns:
            Dict[str, Any]: 헬스체크 결과
        """
        base_health = await super().health_check()
        
        try:
            # 포트폴리오 특정 헬스체크
            portfolio_summary = await self.get_portfolio_summary()
            positions = await self.get_positions()
            
            portfolio_health = {
                'portfolio_summary': asdict(portfolio_summary),
                'positions_count': len(positions),
                'total_market_value': sum(pos.market_value for pos in positions),
                'cache_status': {
                    'last_update': self._last_cache_update.isoformat() if self._last_cache_update else None,
                    'positions_cached': len(self._positions_cache),
                    'summary_cached': self._portfolio_summary_cache is not None
                }
            }
            
            base_health['portfolio_health'] = portfolio_health
            
            return base_health
            
        except Exception as e:
            base_health['portfolio_health_error'] = str(e)
            return base_health
