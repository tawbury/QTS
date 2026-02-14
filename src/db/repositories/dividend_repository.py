"""
Dividend 리포지토리

배당금(Dividend) 시트의 데이터를 관리하는 리포지토리입니다.
연도별 배당금 데이터를 관리합니다.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_repository import BaseSheetRepository


class DividendRepository(BaseSheetRepository):
    """
    Dividend 리포지토리
    
    배당금 데이터를 관리하는 리포지토리 클래스입니다.
    """
    
    def __init__(self, client, spreadsheet_id: str):
        """
        DividendRepository 초기화
        
        Args:
            client: Google Sheets 클라이언트
            spreadsheet_id: 스프레드시트 ID
        """
        super().__init__(client, spreadsheet_id, "Dividend")
        
        # 필수 필드 정의
        self.required_fields = ['Year']
        
        self.logger.info(f"DividendRepository initialized for sheet '{self.sheet_name}'")
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """모든 배당금 데이터 조회"""
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
            
            self.logger.info(f"Retrieved {len(result)} dividend records")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get all dividend data: {str(e)}")
            raise
    
    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 배당금 데이터 조회
        
        Args:
            record_id: 배당금 데이터 ID (Year 기반)
            
        Returns:
            Optional[Dict[str, Any]]: 배당금 데이터 또는 None
        """
        try:
            all_dividends = await self.get_all()
            
            for dividend in all_dividends:
                if str(dividend.get('Year', '')) == str(record_id):
                    return dividend
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get dividend data by ID '{record_id}': {str(e)}")
            raise
    
    async def get_dividend_by_year(self, year: int) -> Optional[Dict[str, Any]]:
        """
        연도별 배당금 조회
        
        Args:
            year: 연도
            
        Returns:
            Optional[Dict[str, Any]]: 연도별 배당금 데이터 또는 None
        """
        return await self.get_by_id(str(year))
    
    async def get_dividend_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """
        티커별 배당금 조회
        
        Args:
            ticker: 티커
            
        Returns:
            List[Dict[str, Any]]: 티커별 배당금 데이터
        """
        try:
            all_dividends = await self.get_all()
            ticker_dividends = []
            
            for dividend in all_dividends:
                # 모든 컬럼에서 티커 검색
                for key, value in dividend.items():
                    if key != 'Year' and str(value).upper() == ticker.upper():
                        ticker_dividends.append(dividend)
                        break
            
            self.logger.info(f"Found {len(ticker_dividends)} dividend records for ticker '{ticker}'")
            return ticker_dividends
            
        except Exception as e:
            self.logger.error(f"Failed to get dividends by ticker '{ticker}': {str(e)}")
            raise
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        새 배당금 데이터 생성
        
        Args:
            data: 배당금 데이터
            
        Returns:
            Dict[str, Any]: 생성된 배당금 데이터
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
            
            self.logger.info(f"Created new dividend record: {sanitized_data.get('Year')}")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to create dividend record: {str(e)}")
            raise
    
    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        배당금 데이터 업데이트
        
        Args:
            record_id: 배당금 데이터 ID (Year)
            data: 업데이트할 데이터
            
        Returns:
            Dict[str, Any]: 업데이트된 배당금 데이터
        """
        try:
            # 기존 데이터 조회
            existing_record = await self.get_by_id(record_id)
            if not existing_record:
                raise ValueError(f"Dividend record for year '{record_id}' not found")
            
            # 데이터 병합
            updated_data = {**existing_record, **data}
            
            # 데이터 정제
            sanitized_data = self._sanitize_data(updated_data)
            
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id, 'Year')
            if not row_number:
                raise ValueError(f"Could not find row for dividend year '{record_id}'")
            
            # 시트 업데이트
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized_data, headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [row_data])
            
            self.logger.info(f"Updated dividend record: {record_id}")
            return sanitized_data
            
        except Exception as e:
            self.logger.error(f"Failed to update dividend record '{record_id}': {str(e)}")
            raise
    
    async def update_dividend_data(
        self,
        year: int,
        month_data: Dict[str, float],
        **kwargs
    ) -> Dict[str, Any]:
        """
        배당금 데이터 업데이트 (편의 메서드)
        
        Args:
            year: 연도
            month_data: 월별 배당금 데이터 {'Jan': 1000, 'Feb': 1500, ...}
            **kwargs: 추가 필드
            
        Returns:
            Dict[str, Any]: 업데이트된 배당금 데이터
        """
        update_data = {'Year': year}
        update_data.update(month_data)
        update_data.update(kwargs)
        
        return await self.update(str(year), update_data)
    
    async def delete(self, record_id: str) -> bool:
        """
        배당금 데이터 삭제
        
        Args:
            record_id: 배당금 데이터 ID (Year)
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 행 번호 찾기
            row_number = await self._find_row_by_id(record_id, 'Year')
            if not row_number:
                return False
            
            # 행 삭제 (빈 값으로 업데이트)
            headers = await self.get_headers()
            empty_row = [''] * len(headers)
            
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [empty_row])
            
            self.logger.info(f"Deleted dividend record: {record_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete dividend record '{record_id}': {str(e)}")
            raise
    
    async def exists(self, record_id: str) -> bool:
        """
        배당금 데이터 존재 여부 확인
        
        Args:
            record_id: 배당금 데이터 ID (Year)
            
        Returns:
            bool: 존재 여부
        """
        try:
            existing_record = await self.get_by_id(record_id)
            return existing_record is not None
        except Exception as e:
            self.logger.error(f"Failed to check dividend existence '{record_id}': {str(e)}")
            return False
    
    async def get_yearly_dividend_summary(self, start_year: int = None, end_year: int = None) -> Dict[str, Any]:
        """
        연도별 배당금 요약 조회
        
        Args:
            start_year: 시작 연도 (선택사항)
            end_year: 종료 연도 (선택사항)
            
        Returns:
            Dict[str, Any]: 연도별 배당금 요약
        """
        try:
            all_dividends = await self.get_all()
            
            # 연도 필터링
            if start_year or end_year:
                filtered_dividends = []
                for dividend in all_dividends:
                    try:
                        year = int(dividend.get('Year', 0))
                        if start_year and year < start_year:
                            continue
                        if end_year and year > end_year:
                            continue
                        filtered_dividends.append(dividend)
                    except (ValueError, TypeError):
                        continue
                all_dividends = filtered_dividends
            
            # 연도별 총계 계산
            yearly_totals = {}
            monthly_totals = {}
            
            for dividend in all_dividends:
                year = dividend.get('Year', 'Unknown')
                yearly_totals[year] = 0
                
                # 월별 데이터 합계
                for key, value in dividend.items():
                    if key != 'Year' and key not in monthly_totals:
                        monthly_totals[key] = 0
                    
                    try:
                        if key != 'Year' and value and str(value) != '#N/A':
                            amount = float(str(value).replace(',', ''))
                            yearly_totals[year] += amount
                            monthly_totals[key] += amount
                    except (ValueError, TypeError):
                        continue
            
            summary = {
                'total_years': len(yearly_totals),
                'yearly_totals': yearly_totals,
                'monthly_totals': monthly_totals,
                'total_dividend': sum(yearly_totals.values()),
                'average_yearly': sum(yearly_totals.values()) / len(yearly_totals) if yearly_totals else 0,
                'period': f"{start_year or 'earliest'}-{end_year or 'latest'}",
                'calculation_time': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get yearly dividend summary: {str(e)}")
            raise
    
    async def get_monthly_dividend_trend(self, years: int = 5) -> Dict[str, Any]:
        """
        월별 배당금 트렌드 조회
        
        Args:
            years: 조회할 연도 수
            
        Returns:
            Dict[str, Any]: 월별 배당금 트렌드
        """
        try:
            current_year = datetime.now().year
            start_year = current_year - years + 1
            
            summary = await self.get_yearly_dividend_summary(start_year, current_year)
            
            # 월별 트렌드 데이터 구성
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            monthly_trend = {}
            for month in months:
                monthly_trend[month] = []
            
            # 연도별 월 데이터 수집
            all_dividends = await self.get_all()
            for dividend in all_dividends:
                try:
                    year = int(dividend.get('Year', 0))
                    if start_year <= year <= current_year:
                        for month in months:
                            value = dividend.get(month, 0)
                            if value and str(value) != '#N/A':
                                try:
                                    amount = float(str(value).replace(',', ''))
                                    monthly_trend[month].append({
                                        'year': year,
                                        'amount': amount
                                    })
                                except (ValueError, TypeError):
                                    continue
                except (ValueError, TypeError):
                    continue
            
            trend_analysis = {
                'monthly_trend': monthly_trend,
                'years_analyzed': years,
                'monthly_totals': summary.get('monthly_totals', {}),
                'total_dividend': summary.get('total_dividend', 0),
                'calculation_time': datetime.now().isoformat()
            }
            
            return trend_analysis
            
        except Exception as e:
            self.logger.error(f"Failed to get monthly dividend trend: {str(e)}")
            raise
    
    async def get_dividend_calendar(self, year: int = None) -> Dict[str, Any]:
        """
        배당금 캘린더 조회
        
        Args:
            year: 연도 (선택사항, 기본값: 현재 연도)
            
        Returns:
            Dict[str, Any]: 배당금 캘린더
        """
        try:
            if not year:
                year = datetime.now().year
            
            dividend_data = await self.get_dividend_by_year(year)
            
            if not dividend_data:
                return {
                    'year': year,
                    'months': {},
                    'total_dividend': 0,
                    'message': 'No dividend data found'
                }
            
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            monthly_data = {}
            total_dividend = 0
            
            for month in months:
                value = dividend_data.get(month, 0)
                if value and str(value) != '#N/A':
                    try:
                        amount = float(str(value).replace(',', ''))
                        monthly_data[month] = amount
                        total_dividend += amount
                    except (ValueError, TypeError):
                        monthly_data[month] = 0
                else:
                    monthly_data[month] = 0
            
            calendar = {
                'year': year,
                'months': monthly_data,
                'total_dividend': total_dividend,
                'average_monthly': total_dividend / 12,
                'highest_month': max(monthly_data.items(), key=lambda x: x[1]) if monthly_data else None,
                'lowest_month': min(monthly_data.items(), key=lambda x: x[1]) if monthly_data else None,
                'calculation_time': datetime.now().isoformat()
            }
            
            return calendar
            
        except Exception as e:
            self.logger.error(f"Failed to get dividend calendar: {str(e)}")
            raise
