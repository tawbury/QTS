"""
History 리포지토리

히스토리(History) 시트의 데이터를 관리하는 리포지토리입니다.
일일 성과 및 히스토리 데이터를 관리합니다.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging

from .base_repository import BaseSheetRepository
from ..google_sheets_client import ValidationError


class HistoryRepository(BaseSheetRepository):
    """
    History 리포지토리
    
    히스토리 데이터를 관리하는 리포지토리 클래스입니다.
    """
    
    def __init__(self, client, spreadsheet_id: str):
        """
        HistoryRepository 초기화
        
        Args:
            client: Google Sheets 클라이언트
            spreadsheet_id: 스프레드시트 ID
        """
        super().__init__(client, spreadsheet_id, "History")
        
        # 필수 필드 정의
        self.required_fields = [
            'Date', 'Total_Equity', 'Daily_PnL', 'Daily_Return', 'Cumulative_Return'
        ]
        
        self.logger.info(f"HistoryRepository initialized for sheet '{self.sheet_name}'")
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """모든 히스토리 데이터 조회"""
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
            
            # 날짜순 정렬
            result.sort(key=lambda x: x.get('Date', ''))
            
            self.logger.info(f"Retrieved {len(result)} history records")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get all history: {str(e)}")
            raise
    
    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 히스토리 조회
        
        Args:
            record_id: 히스토리 ID (Date 기반)
            
        Returns:
            Optional[Dict[str, Any]]: 히스토리 기록 또는 None
        """
        try:
            all_history = await self.get_all()
            
            for record in all_history:
                if str(record.get('Date', '')) == str(record_id):
                    return record
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get history by ID '{record_id}': {str(e)}")
            raise
    
    async def get_execution_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        실행 히스토리 조회
        
        Args:
            days: 조회할 일수
            
        Returns:
            List[Dict[str, Any]]: 실행 히스토리
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - datetime.timedelta(days=days)
            
            all_history = await self.get_all()
            filtered_history = []
            
            for record in all_history:
                date_str = record.get('Date', '')
                if date_str:
                    try:
                        record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        if start_date <= record_date <= end_date:
                            filtered_history.append(record)
                    except ValueError:
                        continue
            
            self.logger.info(f"Retrieved {len(filtered_history)} execution history records for last {days} days")
            return filtered_history
            
        except Exception as e:
            self.logger.error(f"Failed to get execution history: {str(e)}")
            raise
    
    async def get_error_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        에러 히스토리 조회
        
        Args:
            days: 조회할 일수
            
        Returns:
            List[Dict[str, Any]]: 에러 히스토리
        """
        try:
            # History 시트에는 에러 정보가 없으므로 빈 리스트 반환
            # 실제 에러 로그는 별도 시트나 로그 시스템에서 관리해야 함
            self.logger.info(f"No error history found in History sheet for last {days} days")
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get error history: {str(e)}")
            raise
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        새 히스토리 기록 생성
        
        Args:
            data: 히스토리 데이터
            
        Returns:
            Dict[str, Any]: 생성된 히스토리 기록
        """
        try:
            # 필수 필드 검증
            self._validate_required_fields(data, self.required_fields)
            
            # Date가 없으면 현재 날짜로 설정
            if 'Date' not in data:
                data['Date'] = datetime.now().strftime('%Y-%m-%d')
            
            # 데이터 정제
            sanitized_data = self._sanitize_data(data)
            
            # 시트에 추가
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized_data, headers)
            
            range_name = f"{self.sheet_name}!A:Z"
            await self.client.append_sheet_data(range_name, [row_data])
            
            self.logger.info(f"Created new history record: {sanitized_data.get('Date')}")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to create history record: {str(e)}")
            raise
    
    async def log_execution(
        self,
        total_equity: float,
        daily_pnl: float,
        daily_return: float,
        cumulative_return: float,
        volatility: float = None,
        high_watermark: float = None,
        drawdown: float = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        실행 기록 로깅 (편의 메서드)
        
        Args:
            total_equity: 총 자산
            daily_pnl: 일일 손익
            daily_return: 일일 수익률
            cumulative_return: 누적 수익률
            volatility: 변동성
            high_watermark: 최고 자산
            drawdown: 낙폭
            **kwargs: 추가 필드
            
        Returns:
            Dict[str, Any]: 생성된 히스토리 기록
        """
        history_data = {
            'Date': datetime.now().strftime('%Y-%m-%d'),
            'Total_Equity': total_equity,
            'Daily_PnL': daily_pnl,
            'Daily_Return': f"{daily_return:.2f}%",
            'Cumulative_Return': f"{cumulative_return:.2f}%",
            'Volatility_20D': f"{volatility:.2f}%" if volatility else None,
            'High_Watermark': high_watermark,
            'Drawdown': f"{drawdown:.2f}%" if drawdown else None,
            **kwargs
        }
        
        return await self.create(history_data)
    
    async def log_error(self, error_message: str, error_type: str = "ERROR", **kwargs) -> Dict[str, Any]:
        """
        에러 로깅 (편의 메서드)
        
        Args:
            error_message: 에러 메시지
            error_type: 에러 타입
            **kwargs: 추가 필드
            
        Returns:
            Dict[str, Any]: 생성된 에러 기록
        """
        # History 시트는 성과 데이터용이므로 에러 로그는 별도로 처리해야 함
        self.logger.warning(f"Error logging requested but History sheet is for performance data: {error_message}")
        
        # 임시로 날짜만 기록
        error_data = {
            'Date': datetime.now().strftime('%Y-%m-%d'),
            'Total_Equity': 0,
            'Daily_PnL': 0,
            'Daily_Return': f"ERROR: {error_type}",
            'Cumulative_Return': error_message,
            **kwargs
        }
        
        return await self.create(error_data)
    
    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        히스토리 기록 업데이트
        
        Args:
            record_id: 히스토리 ID (Date)
            data: 업데이트할 데이터
            
        Returns:
            Dict[str, Any]: 업데이트된 히스토리 기록
        """
        try:
            # 기존 데이터 조회
            existing_record = await self.get_by_id(record_id)
            if not existing_record:
                raise ValueError(f"History record with date '{record_id}' not found")
            
            # 데이터 병합
            updated_data = {**existing_record, **data}
            
            # 데이터 정제
            sanitized_data = self._sanitize_data(updated_data)
            
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id, 'Date')
            if not row_number:
                raise ValueError(f"Could not find row for history date '{record_id}'")
            
            # 시트 업데이트
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized_data, headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [row_data])
            
            self.logger.info(f"Updated history record: {record_id}")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to update history record '{record_id}': {str(e)}")
            raise
    
    async def delete(self, record_id: str) -> bool:
        """
        히스토리 기록 삭제
        
        Args:
            record_id: 히스토리 ID (Date)
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id, 'Date')
            if not row_number:
                return False
            
            # 행 삭제 (빈 값으로 업데이트)
            headers = await self.get_headers()
            empty_row = [''] * len(headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [empty_row])
            
            self.logger.info(f"Deleted history record: {record_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete history record '{record_id}': {str(e)}")
            raise
    
    async def exists(self, record_id: str) -> bool:
        """
        히스토리 기록 존재 여부 확인
        
        Args:
            record_id: 히스토리 ID (Date)
            
        Returns:
            bool: 존재 여부
        """
        try:
            existing_record = await self.get_by_id(record_id)
            return existing_record is not None
        except Exception as e:
            self.logger.error(f"Failed to check history existence '{record_id}': {str(e)}")
            return False
    
    async def get_performance_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        성과 지표 조회
        
        Args:
            days: 조회할 일수
            
        Returns:
            Dict[str, Any]: 성과 지표
        """
        try:
            history_data = await self.get_execution_history(days)
            
            if not history_data:
                return {
                    'period_days': days,
                    'total_records': 0,
                    'total_pnl': 0,
                    'avg_daily_pnl': 0,
                    'best_day': None,
                    'worst_day': None,
                    'win_days': 0,
                    'loss_days': 0
                }
            
            # 성과 계산
            total_pnl = 0
            daily_pnls = []
            
            for record in history_data:
                try:
                    daily_pnl_str = record.get('Daily_PnL', '0')
                    # 쉼표 제거하고 숫자로 변환
                    daily_pnl = float(str(daily_pnl_str).replace(',', ''))
                    total_pnl += daily_pnl
                    daily_pnls.append(daily_pnl)
                except (ValueError, TypeError):
                    continue
            
            # 통계 계산
            win_days = len([pnl for pnl in daily_pnls if pnl > 0])
            loss_days = len([pnl for pnl in daily_pnls if pnl < 0])
            avg_daily_pnl = total_pnl / len(daily_pnls) if daily_pnls else 0
            
            # 최고/최저일
            best_day = max(history_data, key=lambda x: float(str(x.get('Daily_PnL', '0')).replace(',', ''))) if history_data else None
            worst_day = min(history_data, key=lambda x: float(str(x.get('Daily_PnL', '0')).replace(',', ''))) if history_data else None
            
            metrics = {
                'period_days': days,
                'total_records': len(history_data),
                'total_pnl': total_pnl,
                'avg_daily_pnl': avg_daily_pnl,
                'best_day': best_day,
                'worst_day': worst_day,
                'win_days': win_days,
                'loss_days': loss_days,
                'win_rate': (win_days / len(daily_pnls) * 100) if daily_pnls else 0,
                'calculation_time': datetime.now().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {str(e)}")
            raise
