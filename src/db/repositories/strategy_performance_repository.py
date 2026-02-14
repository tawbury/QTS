"""
Strategy_Performance 리포지토리

전략 성과(Strategy) 시트의 데이터를 관리하는 리포지토리입니다.
각 트레이딩 전략의 성과 데이터를 관리합니다.
"""

from typing import List, Dict, Any, Optional

from .base_repository import BaseSheetRepository
from ...shared.timezone_utils import now_kst


class StrategyPerformanceRepository(BaseSheetRepository):
    """
    Strategy Performance 리포지토리
    
    전략 성과 데이터를 관리하는 리포지토리 클래스입니다.
    """
    
    def __init__(self, client, spreadsheet_id: str):
        """
        StrategyPerformanceRepository 초기화
        
        Args:
            client: Google Sheets 클라이언트
            spreadsheet_id: 스프레드시트 ID
        """
        super().__init__(client, spreadsheet_id, "Strategy")
        
        # 필수 필드 정의
        self.required_fields = [
            'Strategy', 'Trades', 'Win_Rate', 'Avg_PnL', 'Total_PnL'
        ]
        
        self.logger.info(f"StrategyPerformanceRepository initialized for sheet '{self.sheet_name}'")
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """모든 전략 성과 조회"""
        try:
            headers = await self.get_headers()
            if not headers:
                return []
            
            # 헤더 다음 행부터 모든 데이터 조회
            range_name = f"{self.sheet_name}!A{self.header_row + 1}:Z"
            raw_data = await self.client.get_sheet_data(range_name)
            
            result = []
            for row in raw_data:
                if row and any(cell.strip() for cell in row):  # 빈 행 제외
                    record = self._row_to_dict(row, headers)
                    result.append(record)
            
            self.logger.info(f"Retrieved {len(result)} strategy performance records")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get all strategy performance: {str(e)}")
            raise
    
    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 전략 성과 조회
        
        Args:
            record_id: 전략 성과 ID (Strategy 기반)
            
        Returns:
            Optional[Dict[str, Any]]: 전략 성과 정보 또는 None
        """
        try:
            all_strategies = await self.get_all()
            
            for strategy in all_strategies:
                if strategy.get('Strategy', '').upper() == record_id.upper():
                    return strategy
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get strategy performance by ID '{record_id}': {str(e)}")
            raise
    
    async def get_performance_by_strategy(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """
        전략 이름으로 성과 조회
        
        Args:
            strategy_name: 전략 이름
            
        Returns:
            Optional[Dict[str, Any]]: 전략 성과 정보 또는 None
        """
        return await self.get_by_id(strategy_name)
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        새 전략 성과 기록 생성
        
        Args:
            data: 전략 성과 데이터
            
        Returns:
            Dict[str, Any]: 생성된 전략 성과 기록
        """
        try:
            # 필수 필드 검증
            self._validate_required_fields(data, self.required_fields)
            
            # 데이터 정제
            sanitized_data = self._sanitize_data(data)
            
            # 시트에 추가
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized_data, headers)
            
            range_name = f"{self.sheet_name}!A:Z"
            await self.client.append_sheet_data(range_name, [row_data])
            
            self.logger.info(f"Created new strategy performance record: {sanitized_data.get('Strategy')}")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to create strategy performance record: {str(e)}")
            raise
    
    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        전략 성과 업데이트
        
        Args:
            record_id: 전략 성과 ID (Strategy)
            data: 업데이트할 데이터
            
        Returns:
            Dict[str, Any]: 업데이트된 전략 성과
        """
        try:
            # 기존 데이터 조회
            existing_record = await self.get_by_id(record_id)
            if not existing_record:
                raise ValueError(f"Strategy performance for '{record_id}' not found")
            
            # 데이터 병합
            updated_data = {**existing_record, **data}
            
            # 데이터 정제
            sanitized_data = self._sanitize_data(updated_data)
            
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id, 'Strategy')
            if not row_number:
                raise ValueError(f"Could not find row for strategy '{record_id}'")
            
            # 시트 업데이트
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized_data, headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [row_data])
            
            self.logger.info(f"Updated strategy performance: {record_id}")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to update strategy performance '{record_id}': {str(e)}")
            raise
    
    async def update_performance_metrics(
        self,
        strategy_name: str,
        trades: int = None,
        win_rate: float = None,
        avg_pnl: float = None,
        total_pnl: float = None,
        cumulative_ret: float = None,
        mdd: float = None,
        volatility: float = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        성과 지표 업데이트 (편의 메서드)
        
        Args:
            strategy_name: 전략 이름
            trades: 거래 횟수
            win_rate: 승률
            avg_pnl: 평균 손익
            total_pnl: 총 손익
            cumulative_ret: 누적 수익률
            mdd: 최대 낙폭
            volatility: 변동성
            **kwargs: 추가 필드
            
        Returns:
            Dict[str, Any]: 업데이트된 전략 성과
        """
        update_data = {}
        
        if trades is not None:
            update_data['Trades'] = trades
        if win_rate is not None:
            update_data['Win_Rate'] = f"{win_rate:.2f}%"
        if avg_pnl is not None:
            update_data['Avg_PnL'] = avg_pnl
        if total_pnl is not None:
            update_data['Total_PnL'] = total_pnl
        if cumulative_ret is not None:
            update_data['Cumulative_Ret'] = f"{cumulative_ret:.2f}%"
        if mdd is not None:
            update_data['MDD'] = f"{mdd:.2f}%"
        if volatility is not None:
            update_data['Volatility'] = f"{volatility:.2f}%"
        
        update_data.update(kwargs)
        
        return await self.update(strategy_name, update_data)
    
    async def delete(self, record_id: str) -> bool:
        """
        전략 성과 삭제
        
        Args:
            record_id: 전략 성과 ID (Strategy)
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id, 'Strategy')
            if not row_number:
                return False
            
            # 행 삭제 (빈 값으로 업데이트)
            headers = await self.get_headers()
            empty_row = [''] * len(headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [empty_row])
            
            self.logger.info(f"Deleted strategy performance: {record_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete strategy performance '{record_id}': {str(e)}")
            raise
    
    async def exists(self, record_id: str) -> bool:
        """
        전략 성과 존재 여부 확인
        
        Args:
            record_id: 전략 성과 ID (Strategy)
            
        Returns:
            bool: 존재 여부
        """
        try:
            existing_record = await self.get_by_id(record_id)
            return existing_record is not None
        except Exception as e:
            self.logger.error(f"Failed to check strategy performance existence '{record_id}': {str(e)}")
            return False
    
    async def calculate_returns(self, strategy_name: str = None) -> Dict[str, Any]:
        """
        수익률 계산
        
        Args:
            strategy_name: 전략 이름 (선택사항, None이면 전체)
            
        Returns:
            Dict[str, Any]: 수익률 정보
        """
        try:
            strategies = await self.get_all()
            
            if strategy_name:
                strategies = [s for s in strategies if s.get('Strategy', '').upper() == strategy_name.upper()]
            
            total_return = 0
            total_pnl = 0
            strategy_returns = []
            
            for strategy in strategies:
                try:
                    total_pnl_str = strategy.get('Total_PnL', '0')
                    cumulative_ret_str = strategy.get('Cumulative_Ret', '0%')
                    
                    # 쉼표 제거하고 숫자로 변환
                    total_pnl = float(str(total_pnl_str).replace(',', ''))
                    
                    # % 제거하고 숫자로 변환
                    cumulative_ret = float(str(cumulative_ret_str).replace('%', ''))
                    
                    strategy_return = {
                        'strategy': strategy.get('Strategy'),
                        'total_pnl': total_pnl,
                        'cumulative_return': cumulative_ret,
                        'trades': strategy.get('Trades', 0),
                        'win_rate': strategy.get('Win_Rate', '0%')
                    }
                    
                    strategy_returns.append(strategy_return)
                    total_pnl += total_pnl
                    total_return += cumulative_ret
                    
                except (ValueError, TypeError):
                    continue
            
            result = {
                'total_strategies': len(strategy_returns),
                'total_pnl': total_pnl,
                'average_return': total_return / len(strategy_returns) if strategy_returns else 0,
                'strategy_returns': strategy_returns,
                'strategy_filter': strategy_name,
                'calculation_time': now_kst().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to calculate returns: {str(e)}")
            raise
    
    async def get_strategy_ranking(self, sort_by: str = 'Total_PnL') -> List[Dict[str, Any]]:
        """
        전략 랭킹 조회
        
        Args:
            sort_by: 정렬 기준 ('Total_PnL', 'Win_Rate', 'Cumulative_Ret')
            
        Returns:
            List[Dict[str, Any]]: 정렬된 전략 리스트
        """
        try:
            strategies = await self.get_all()
            
            # 정렬 기준에 따라 숫자로 변환
            def get_sort_value(strategy):
                if sort_by == 'Total_PnL':
                    value = strategy.get('Total_PnL', '0')
                    return float(str(value).replace(',', ''))
                elif sort_by == 'Win_Rate':
                    value = strategy.get('Win_Rate', '0%')
                    return float(str(value).replace('%', ''))
                elif sort_by == 'Cumulative_Ret':
                    value = strategy.get('Cumulative_Ret', '0%')
                    return float(str(value).replace('%', ''))
                else:
                    return 0
            
            # 정렬
            sorted_strategies = sorted(strategies, key=get_sort_value, reverse=True)
            
            # 랭킹 추가
            ranked_strategies = []
            for i, strategy in enumerate(sorted_strategies, 1):
                strategy_with_rank = strategy.copy()
                strategy_with_rank['rank'] = i
                ranked_strategies.append(strategy_with_rank)
            
            self.logger.info(f"Retrieved strategy ranking sorted by {sort_by}")
            return ranked_strategies
            
        except Exception as e:
            self.logger.error(f"Failed to get strategy ranking: {str(e)}")
            raise
    
    async def get_best_performing_strategy(self) -> Optional[Dict[str, Any]]:
        """
        최고 성과 전략 조회
        
        Returns:
            Optional[Dict[str, Any]]: 최고 성과 전략 또는 None
        """
        try:
            rankings = await self.get_strategy_ranking('Total_PnL')
            return rankings[0] if rankings else None
            
        except Exception as e:
            self.logger.error(f"Failed to get best performing strategy: {str(e)}")
            raise
