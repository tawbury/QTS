"""
Position 리포지토리

포지션(Position) 시트의 데이터를 관리하는 리포지토리입니다.
현재 보유 중인 포지션 정보를 관리합니다.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .base_repository import BaseSheetRepository
from ..google_sheets_client import ValidationError


class PositionRepository(BaseSheetRepository):
    """
    Position 리포지토리
    
    포지션 데이터를 관리하는 리포지토리 클래스입니다.
    """
    
    def __init__(self, client, spreadsheet_id: str):
        """
        PositionRepository 초기화
        
        Args:
            client: Google Sheets 클라이언트
            spreadsheet_id: 스프레드시트 ID
        """
        super().__init__(client, spreadsheet_id, "Position")
        
        # 필수 필드 정의
        self.required_fields = [
            'Symbol', 'Name', 'Market', 'Qty', 'Avg_Price(Current_Currency)'
        ]
        
        self.logger.info(f"PositionRepository initialized for sheet '{self.sheet_name}'")
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """모든 포지션 조회"""
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
                    # 수량이 0이 아닌 포지션만 포함
                    if record.get('Qty', 0) != 0:
                        result.append(record)
            
            self.logger.info(f"Retrieved {len(result)} active positions")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get all positions: {str(e)}")
            raise
    
    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 포지션 조회
        
        Args:
            record_id: 포지션 ID (Symbol 기반)
            
        Returns:
            Optional[Dict[str, Any]]: 포지션 정보 또는 None
        """
        try:
            all_positions = await self.get_all()
            
            for position in all_positions:
                if position.get('Symbol', '').upper() == record_id.upper():
                    return position
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get position by ID '{record_id}': {str(e)}")
            raise
    
    async def get_current_positions(self) -> List[Dict[str, Any]]:
        """
        현재 보유 중인 포지션 조회
        
        Returns:
            List[Dict[str, Any]]: 현재 포지션 리스트
        """
        return await self.get_all()
    
    async def get_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        종목 코드로 포지션 조회
        
        Args:
            symbol: 종목 코드
            
        Returns:
            Optional[Dict[str, Any]]: 포지션 정보 또는 None
        """
        return await self.get_by_id(symbol)
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        새 포지션 생성
        
        Args:
            data: 포지션 데이터
            
        Returns:
            Dict[str, Any]: 생성된 포지션
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
            
            self.logger.info(f"Created new position: {sanitized_data.get('Symbol')}")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to create position: {str(e)}")
            raise
    
    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        포지션 업데이트
        
        Args:
            record_id: 포지션 ID (Symbol)
            data: 업데이트할 데이터
            
        Returns:
            Dict[str, Any]: 업데이트된 포지션
        """
        try:
            # 기존 데이터 조회
            existing_record = await self.get_by_id(record_id)
            if not existing_record:
                raise ValueError(f"Position with symbol '{record_id}' not found")
            
            # 데이터 병합
            updated_data = {**existing_record, **data}
            
            # 데이터 정제
            sanitized_data = self._sanitize_data(updated_data)
            
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id, 'Symbol')
            if not row_number:
                raise ValueError(f"Could not find row for position '{record_id}'")
            
            # 시트 업데이트
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized_data, headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [row_data])
            
            self.logger.info(f"Updated position: {record_id}")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to update position '{record_id}': {str(e)}")
            raise
    
    async def update_position(
        self,
        symbol: str,
        qty: int = None,
        avg_price: float = None,
        current_price: float = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        포지션 업데이트 (편의 메서드)
        
        Args:
            symbol: 종목 코드
            qty: 수량
            avg_price: 평균 가격
            current_price: 현재 가격
            **kwargs: 추가 필드
            
        Returns:
            Dict[str, Any]: 업데이트된 포지션
        """
        update_data = {}
        
        if qty is not None:
            update_data['Qty'] = qty
        if avg_price is not None:
            update_data['Avg_Price(Current_Currency)'] = avg_price
        if current_price is not None:
            update_data['Current_Price(Current_Currency)'] = current_price
        
        update_data.update(kwargs)
        
        return await self.update(symbol, update_data)
    
    async def delete(self, record_id: str) -> bool:
        """
        포지션 삭제
        
        Args:
            record_id: 포지션 ID (Symbol)
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id, 'Symbol')
            if not row_number:
                return False
            
            # 행 삭제 (빈 값으로 업데이트)
            headers = await self.get_headers()
            empty_row = [''] * len(headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [empty_row])
            
            self.logger.info(f"Deleted position: {record_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete position '{record_id}': {str(e)}")
            raise
    
    async def exists(self, record_id: str) -> bool:
        """
        포지션 존재 여부 확인
        
        Args:
            record_id: 포지션 ID (Symbol)
            
        Returns:
            bool: 존재 여부
        """
        try:
            existing_record = await self.get_by_id(record_id)
            return existing_record is not None
        except Exception as e:
            self.logger.error(f"Failed to check position existence '{record_id}': {str(e)}")
            return False
    
    async def calculate_unrealized_pnl(self, symbol: str = None) -> Dict[str, Any]:
        """
        미실현 손익 계산
        
        Args:
            symbol: 종목 코드 (선택사항, None이면 전체)
            
        Returns:
            Dict[str, Any]: 미실현 손익 정보
        """
        try:
            positions = await self.get_all()
            
            if symbol:
                positions = [p for p in positions if p.get('Symbol', '').upper() == symbol.upper()]
            
            total_unrealized_pnl = 0
            position_details = []
            
            for position in positions:
                try:
                    qty = position.get('Qty', 0)
                    avg_price = position.get('Avg_Price(Current_Currency)', 0)
                    current_price = position.get('Current_Price(Current_Currency)', 0)
                    
                    if qty != 0 and avg_price != 0 and current_price != 0:
                        # 미실현 손익 = (현재가 - 평균가) * 수량
                        unrealized_pnl = (current_price - avg_price) * qty
                        unrealized_pnl_pct = ((current_price - avg_price) / avg_price) * 100 if avg_price != 0 else 0
                        
                        position_detail = {
                            'symbol': position.get('Symbol'),
                            'qty': qty,
                            'avg_price': avg_price,
                            'current_price': current_price,
                            'unrealized_pnl': unrealized_pnl,
                            'unrealized_pnl_pct': unrealized_pnl_pct
                        }
                        
                        position_details.append(position_detail)
                        total_unrealized_pnl += unrealized_pnl
                        
                except Exception as e:
                    self.logger.warning(f"Failed to calculate PnL for position {position.get('Symbol')}: {str(e)}")
                    continue
            
            result = {
                'total_unrealized_pnl': total_unrealized_pnl,
                'position_count': len(position_details),
                'positions': position_details,
                'symbol_filter': symbol,
                'calculation_time': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to calculate unrealized PnL: {str(e)}")
            raise
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        포트폴리오 요약 정보 조회
        
        Returns:
            Dict[str, Any]: 포트폴리오 요약
        """
        try:
            positions = await self.get_all()
            
            total_positions = len(positions)
            total_investment = 0
            total_current_value = 0
            
            market_distribution = {}
            
            for position in positions:
                try:
                    qty = position.get('Qty', 0)
                    avg_price = position.get('Avg_Price(Current_Currency)', 0)
                    current_price = position.get('Current_Price(Current_Currency)', 0)
                    market = position.get('Market', 'Unknown')
                    
                    if qty != 0 and avg_price != 0:
                        investment = avg_price * qty
                        current_value = current_price * qty if current_price != 0 else investment
                        
                        total_investment += investment
                        total_current_value += current_value
                        
                        # 시장별 분포
                        if market not in market_distribution:
                            market_distribution[market] = {'count': 0, 'value': 0}
                        market_distribution[market]['count'] += 1
                        market_distribution[market]['value'] += current_value
                        
                except Exception as e:
                    self.logger.warning(f"Failed to process position {position.get('Symbol')}: {str(e)}")
                    continue
            
            total_pnl = total_current_value - total_investment
            total_pnl_pct = (total_pnl / total_investment * 100) if total_investment != 0 else 0
            
            summary = {
                'total_positions': total_positions,
                'total_investment': total_investment,
                'total_current_value': total_current_value,
                'total_pnl': total_pnl,
                'total_pnl_pct': total_pnl_pct,
                'market_distribution': market_distribution,
                'calculation_time': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get portfolio summary: {str(e)}")
            raise
