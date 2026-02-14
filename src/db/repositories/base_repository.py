"""
시트 리포지토리 베이스 클래스

QTS 시스템의 모든 시트 리포지토리가 상속받는 추상 기본 클래스입니다.
CRUD 인터페이스와 공통 유틸리티 메서드를 제공합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

from ..google_sheets_client import GoogleSheetsClient
from ...shared.timezone_utils import now_kst


class BaseSheetRepository(ABC):
    """
    시트 리포지토리 베이스 클래스
    
    모든 시트 리포지토리가 상속받아야 하는 추상 클래스입니다.
    기본 CRUD 인터페이스와 공통 기능을 제공합니다.
    """
    
    def __init__(
        self, 
        client: GoogleSheetsClient, 
        spreadsheet_id: str, 
        sheet_name: str,
        header_row: int = 1
    ):
        """
        BaseSheetRepository 초기화
        
        Args:
            client: Google Sheets 클라이언트
            spreadsheet_id: 스프레드시트 ID
            sheet_name: 시트 이름
            header_row: 헤더 행 번호 (기본값: 1)
        """
        self.client = client
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.header_row = header_row
        self.range_name = f"{sheet_name}!A:Z"
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 캐싱
        self._headers_cache = None
        self._last_cache_update = None
        
        self.logger.info(f"Initialized {self.__class__.__name__} for sheet '{sheet_name}'")
    
    @abstractmethod
    async def get_all(self) -> List[Dict[str, Any]]:
        """
        모든 데이터 조회
        
        Returns:
            List[Dict[str, Any]]: 모든 데이터 리스트
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 데이터 조회
        
        Args:
            record_id: 레코드 ID
            
        Returns:
            Optional[Dict[str, Any]]: 조회된 데이터 또는 None
        """
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터 생성
        
        Args:
            data: 생성할 데이터
            
        Returns:
            Dict[str, Any]: 생성된 데이터
        """
        pass
    
    @abstractmethod
    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터 업데이트
        
        Args:
            record_id: 레코드 ID
            data: 업데이트할 데이터
            
        Returns:
            Dict[str, Any]: 업데이트된 데이터
        """
        pass
    
    @abstractmethod
    async def delete(self, record_id: str) -> bool:
        """
        데이터 삭제
        
        Args:
            record_id: 레코드 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        pass
    
    @abstractmethod
    async def exists(self, record_id: str) -> bool:
        """
        데이터 존재 여부 확인
        
        Args:
            record_id: 레코드 ID
            
        Returns:
            bool: 존재 여부
        """
        pass
    
    async def get_headers(self) -> List[str]:
        """
        시트 헤더 조회
        
        Returns:
            List[str]: 헤더 리스트
        """
        if self._headers_cache is None:
            try:
                # 헤더 행만 조회
                header_range = f"{self.sheet_name}!A{self.header_row}:Z{self.header_row}"
                header_data = await self.client.get_sheet_data(header_range)
                
                if header_data and len(header_data) > 0 and header_data[0]:
                    self._headers_cache = [str(cell).strip() for cell in header_data[0] if cell.strip()]
                else:
                    self._headers_cache = []

                self._last_cache_update = now_kst()
                self.logger.debug(f"Retrieved headers: {self._headers_cache}")
                
            except Exception as e:
                self.logger.error(f"Failed to get headers: {str(e)}")
                self._headers_cache = []
        
        return self._headers_cache
    
    async def clear_cache(self):
        """헤더 캐시 초기화"""
        self._headers_cache = None
        self._last_cache_update = None
        self.logger.debug("Headers cache cleared")
    
    def _row_to_dict(self, row: List[Any], headers: List[str]) -> Dict[str, Any]:
        """
        행 데이터를 딕셔너리로 변환
        
        Args:
            row: 행 데이터
            headers: 헤더 리스트
            
        Returns:
            Dict[str, Any]: 변환된 딕셔너리
        """
        result = {}
        for i, header in enumerate(headers):
            if i < len(row):
                value = row[i]
                # 데이터 타입 변환
                if value == "":
                    result[header] = None
                elif value.lower() in ["true", "false"]:
                    result[header] = value.lower() == "true"
                else:
                    try:
                        # 숫자 변환 시도
                        if "." in str(value):
                            result[header] = float(value)
                        else:
                            result[header] = int(value)
                    except (ValueError, TypeError):
                        result[header] = value
            else:
                result[header] = None
        
        return result
    
    def _dict_to_row(self, data: Dict[str, Any], headers: List[str]) -> List[Any]:
        """
        딕셔너리를 행 데이터로 변환
        
        Args:
            data: 딕셔너리 데이터
            headers: 헤더 리스트
            
        Returns:
            List[Any]: 변환된 행 데이터
        """
        row = []
        for header in headers:
            value = data.get(header, "")
            # None을 빈 문자열로 변환
            if value is None:
                value = ""
            # 불리언을 문자열로 변환
            elif isinstance(value, bool):
                value = "TRUE" if value else "FALSE"
            else:
                value = str(value)
            row.append(value)
        
        return row
    
    async def _find_row_by_id(self, record_id: str, id_column: str = "id") -> Optional[int]:
        """
        ID로 행 번호 찾기
        
        Args:
            record_id: 레코드 ID
            id_column: ID 컬럼 이름
            
        Returns:
            Optional[int]: 행 번호 (헤더 행 제외) 또는 None
        """
        try:
            # 모든 데이터 조회
            all_data = await self.get_all()
            
            # ID로 행 찾기
            for i, record in enumerate(all_data):
                if str(record.get(id_column, "")) == str(record_id):
                    # 헤더 행 다음부터 시작하므로 +2 (헤더 행 + 1-based index)
                    return i + self.header_row + 1
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find row by ID '{record_id}': {str(e)}")
            return None
    
    async def _get_next_empty_row(self) -> int:
        """
        다음 빈 행 번호 조회
        
        Returns:
            int: 다음 빈 행 번호
        """
        try:
            # 모든 데이터 조회
            all_data = await self.get_all()
            
            # 마지막 데이터 행 다음 번호 반환
            if all_data:
                return len(all_data) + self.header_row + 1
            else:
                # 데이터가 없으면 헤더 다음 행
                return self.header_row + 1
                
        except Exception as e:
            self.logger.error(f"Failed to get next empty row: {str(e)}")
            # 오류 시 헤더 다음 행 반환
            return self.header_row + 1
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """
        필수 필드 검증
        
        Args:
            data: 검증할 데이터
            required_fields: 필수 필드 리스트
            
        Raises:
            ValueError: 필수 필드 누락 시
        """
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터 정제 (보안 및 형식)
        
        Args:
            data: 정제할 데이터
            
        Returns:
            Dict[str, Any]: 정제된 데이터
        """
        sanitized = {}
        for key, value in data.items():
            if value is None:
                sanitized[key] = ""
            elif isinstance(value, str):
                # 문자열 길이 제한
                if len(value) > 50000:  # Google Sheets 셀 제한
                    sanitized[key] = value[:50000] + "..."
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def get_sheet_info(self) -> Dict[str, Any]:
        """
        시트 정보 조회
        
        Returns:
            Dict[str, Any]: 시트 정보
        """
        try:
            worksheet = await self.client.get_worksheet_by_title(self.sheet_name)
            
            return {
                'sheet_name': self.sheet_name,
                'row_count': worksheet.row_count,
                'col_count': worksheet.col_count,
                'header_row': self.header_row,
                'range_name': self.range_name
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get sheet info: {str(e)}")
            return {
                'sheet_name': self.sheet_name,
                'error': str(e)
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        시트 접근 상태 확인 (RepositoryManager.health_check에서 사용).
        
        Returns:
            Dict[str, Any]: status='healthy' 또는 status='unhealthy', error 포함
        """
        try:
            info = await self.get_sheet_info()
            if info.get("error"):
                return {"status": "unhealthy", "sheet_name": self.sheet_name, "error": info["error"]}
            return {"status": "healthy", "sheet_name": self.sheet_name, "info": info}
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {"status": "unhealthy", "sheet_name": self.sheet_name, "error": str(e)}
    
    async def count_records(self) -> int:
        """
        레코드 수 조회

        Returns:
            int: 레코드 수
        """
        try:
            all_data = await self.get_all()
            return len(all_data)
        except Exception as e:
            self.logger.error(f"Failed to count records: {str(e)}")
            return 0

    def _get_worksheet(self):
        """현재 시트의 gspread Worksheet 객체 획득"""
        spreadsheet = getattr(self.client, "spreadsheet", None) or \
            self.client.gspread_client.open_by_key(self.client.spreadsheet_id)
        return spreadsheet.worksheet(self.sheet_name)

    def update_cell(self, cell_address: str, value: Any) -> bool:
        """
        개별 셀 업데이트 (병합 영역 지원)
        
        Args:
            cell_address: 셀 주소 (예: 'A1', 'B2')
            value: 업데이트할 값
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            worksheet = self._get_worksheet()
            worksheet.update([[value]], range_name=cell_address)
            self.logger.debug(f"Updated cell {cell_address}: {value}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update cell {cell_address}: {str(e)}")
            return False
    
    def update_range(self, range_address: str, values: List[List[Any]]) -> bool:
        """
        범위 업데이트 (대량 데이터 지원)
        
        Args:
            range_address: 범위 주소 (예: 'A1:C10')
            values: 업데이트할 데이터 리스트
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            worksheet = self._get_worksheet()
            worksheet.update(values, range_name=range_address)
            self.logger.debug(f"Updated range {range_address} with {len(values)} rows")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update range {range_address}: {str(e)}")
            return False
    
    def get_cell_value(self, cell_address: str) -> Any:
        """
        개별 셀 값 조회
        
        Args:
            cell_address: 셀 주소 (예: 'A1', 'B2')
            
        Returns:
            Any: 셀 값
        """
        try:
            worksheet = self._get_worksheet()
            return worksheet.acell(cell_address).value
        except Exception as e:
            self.logger.error(f"Failed to get cell value {cell_address}: {str(e)}")
            return None
    
    def get_range_values(self, range_address: str) -> List[List[Any]]:
        """
        범위 값 조회
        
        Args:
            range_address: 범위 주소 (예: 'A1:C10')
            
        Returns:
            List[List[Any]]: 범위 데이터
        """
        try:
            worksheet = self._get_worksheet()
            return worksheet.get(range_address)
        except Exception as e:
            self.logger.error(f"Failed to get range values {range_address}: {str(e)}")
            return []
    
    def clear_range(self, range_address: str) -> bool:
        """
        범위 초기화
        
        Args:
            range_address: 범위 주소 (예: 'A1:C10')
            
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            worksheet = self._get_worksheet()
            worksheet.clear(range_address)
            self.logger.debug(f"Cleared range {range_address}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear range {range_address}: {str(e)}")
            return False
