"""
T_Ledger 리포지토리

거래 원장(T_Ledger) 시트의 데이터를 관리하는 리포지토리입니다.
모든 거래 기록의 CRUD 오퍼레이션을 담당합니다.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging

from .base_repository import BaseSheetRepository
from ..google_sheets_client import ValidationError


class T_LedgerRepository(BaseSheetRepository):
    """
    T_Ledger 리포지토리
    
    거래 원장 데이터를 관리하는 리포지토리 클래스입니다.
    """
    
    def __init__(self, client, spreadsheet_id: str):
        """
        T_LedgerRepository 초기화
        
        Args:
            client: Google Sheets 클라이언트
            spreadsheet_id: 스프레드시트 ID
        """
        super().__init__(client, spreadsheet_id, "T_Ledger")
        
        # 필수 필드 정의
        self.required_fields = [
            'Timestamp', 'Symbol', 'Market', 'Side', 'Qty', 
            'Price', 'Amount_Local', 'Currency'
        ]
        
        self.logger.info(f"T_LedgerRepository initialized for sheet '{self.sheet_name}'")
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """모든 거래 기록 조회"""
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
            
            self.logger.info(f"Retrieved {len(result)} trade records")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get all trades: {str(e)}")
            raise
    
    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 거래 기록 조회
        
        Args:
            record_id: 거래 ID (Timestamp 기반)
            
        Returns:
            Optional[Dict[str, Any]]: 거래 기록 또는 None
        """
        try:
            all_trades = await self.get_all()
            
            for trade in all_trades:
                if str(trade.get('Timestamp', '')) == str(record_id):
                    return trade
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get trade by ID '{record_id}': {str(e)}")
            raise
    
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        날짜 범위로 거래 기록 조회
        
        Args:
            start_date: 시작일
            end_date: 종료일
            
        Returns:
            List[Dict[str, Any]]: 날짜 범위 내 거래 기록
        """
        try:
            all_trades = await self.get_all()
            filtered_trades = []
            
            for trade in all_trades:
                timestamp_str = trade.get('Timestamp', '')
                if timestamp_str:
                    try:
                        # Timestamp 형식: "2025-01-24 14:30:00"
                        trade_date = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').date()
                        
                        if start_date <= trade_date <= end_date:
                            filtered_trades.append(trade)
                            
                    except ValueError:
                        continue
            
            self.logger.info(f"Found {len(filtered_trades)} trades in date range {start_date} to {end_date}")
            return filtered_trades
            
        except Exception as e:
            self.logger.error(f"Failed to get trades by date range: {str(e)}")
            raise
    
    async def get_by_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """
        종목 코드로 거래 기록 조회
        
        Args:
            symbol: 종목 코드
            
        Returns:
            List[Dict[str, Any]]: 해당 종목의 거래 기록
        """
        try:
            all_trades = await self.get_all()
            symbol_trades = []
            
            for trade in all_trades:
                if trade.get('Symbol', '').upper() == symbol.upper():
                    symbol_trades.append(trade)
            
            self.logger.info(f"Found {len(symbol_trades)} trades for symbol '{symbol}'")
            return symbol_trades
            
        except Exception as e:
            self.logger.error(f"Failed to get trades by symbol '{symbol}': {str(e)}")
            raise
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        새 거래 기록 생성
        
        Args:
            data: 거래 데이터
            
        Returns:
            Dict[str, Any]: 생성된 거래 기록
        """
        try:
            # 필수 필드 검증
            self._validate_required_fields(data, self.required_fields)
            
            # Timestamp가 없으면 현재 시간으로 설정
            if 'Timestamp' not in data:
                data['Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 데이터 정제
            sanitized_data = self._sanitize_data(data)
            
            # 시트에 추가
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized_data, headers)
            
            range_name = f"{self.sheet_name}!A:Z"
            await self.client.append_sheet_data(range_name, [row_data])
            
            self.logger.info(f"Created new trade record: {sanitized_data.get('Symbol')} {sanitized_data.get('Side')}")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to create trade record: {str(e)}")
            raise
    
    async def create_trade(
        self,
        symbol: str,
        market: str,
        side: str,
        qty: int,
        price: float,
        amount_local: float,
        currency: str = "KRW",
        **kwargs
    ) -> Dict[str, Any]:
        """
        거래 생성 (편의 메서드)
        
        Args:
            symbol: 종목 코드
            market: 시장 (KOSPI/KOSDAQ)
            side: 매수/매도 (BUY/SELL)
            qty: 수량
            price: 가격
            amount_local: 현지 통화 금액
            currency: 통화
            **kwargs: 추가 필드
            
        Returns:
            Dict[str, Any]: 생성된 거래 기록
        """
        trade_data = {
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Symbol': symbol,
            'Market': market,
            'Side': side,
            'Qty': qty,
            'Price': price,
            'Amount_Local': amount_local,
            'Currency': currency,
            **kwargs
        }
        
        return await self.create(trade_data)
    
    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        거래 기록 업데이트
        
        Args:
            record_id: 거래 ID (Timestamp)
            data: 업데이트할 데이터
            
        Returns:
            Dict[str, Any]: 업데이트된 거래 기록
        """
        try:
            # 기존 데이터 조회
            existing_record = await self.get_by_id(record_id)
            if not existing_record:
                raise ValueError(f"Trade record with ID '{record_id}' not found")
            
            # 데이터 병합
            updated_data = {**existing_record, **data}
            
            # 데이터 정제
            sanitized_data = self._sanitize_data(updated_data)
            
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id, 'Timestamp')
            if not row_number:
                raise ValueError(f"Could not find row for trade ID '{record_id}'")
            
            # 시트 업데이트
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized_data, headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [row_data])
            
            self.logger.info(f"Updated trade record: {record_id}")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to update trade record '{record_id}': {str(e)}")
            raise
    
    async def delete(self, record_id: str) -> bool:
        """
        거래 기록 삭제
        
        Args:
            record_id: 거래 ID (Timestamp)
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id, 'Timestamp')
            if not row_number:
                return False
            
            # 행 삭제 (빈 값으로 업데이트)
            headers = await self.get_headers()
            empty_row = [''] * len(headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [empty_row])
            
            self.logger.info(f"Deleted trade record: {record_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete trade record '{record_id}': {str(e)}")
            raise
    
    async def exists(self, record_id: str) -> bool:
        """
        거래 기록 존재 여부 확인
        
        Args:
            record_id: 거래 ID (Timestamp)
            
        Returns:
            bool: 존재 여부
        """
        try:
            existing_record = await self.get_by_id(record_id)
            return existing_record is not None
        except Exception as e:
            self.logger.error(f"Failed to check trade existence '{record_id}': {str(e)}")
            return False
    
    async def get_trade_summary(self, symbol: str = None) -> Dict[str, Any]:
        """
        거래 요약 정보 조회
        
        Args:
            symbol: 종목 코드 (선택사항)
            
        Returns:
            Dict[str, Any]: 거래 요약 정보
        """
        try:
            trades = await self.get_all()
            
            if symbol:
                trades = [t for t in trades if t.get('Symbol', '').upper() == symbol.upper()]
            
            total_trades = len(trades)
            buy_trades = [t for t in trades if t.get('Side', '').upper() == 'BUY']
            sell_trades = [t for t in trades if t.get('Side', '').upper() == 'SELL']
            
            total_amount = sum(t.get('Amount_Local', 0) for t in trades if t.get('Amount_Local'))
            
            summary = {
                'total_trades': total_trades,
                'buy_trades': len(buy_trades),
                'sell_trades': len(sell_trades),
                'total_amount': total_amount,
                'symbol_filter': symbol,
                'latest_trade': None
            }
            
            if trades:
                # 최신 거래 찾기
                latest_trade = max(trades, key=lambda x: x.get('Timestamp', ''))
                summary['latest_trade'] = latest_trade
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get trade summary: {str(e)}")
            raise
