"""
Google Sheets API 클라이언트 모듈

QTS 시스템의 데이터 영속성 계층으로서 Google Sheets와의 통신을 담당합니다.
서비스 계정 인증, API 호출, 에러 처리, 재시도 로직을 포함합니다.
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheetsError(Exception):
    """Google Sheets 관련 기본 에러"""
    pass


class AuthenticationError(GoogleSheetsError):
    """인증 에러"""
    pass


class APIError(GoogleSheetsError):
    """API 호출 에러"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(APIError):
    """API 제한 초과 에러"""
    def __init__(self, retry_after: int = None):
        super().__init__("API rate limit exceeded")
        self.retry_after = retry_after


class ValidationError(GoogleSheetsError):
    """데이터 유효성 검사 에러"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field


class GoogleSheetsClient:
    """
    Google Sheets API v4 클라이언트
    
    QTS 시스템의 데이터 레이어로서 Google Sheets와의 통신을 관리합니다.
    """
    
    def __init__(self, credentials_path: str = None, spreadsheet_id: str = None):
        """
        GoogleSheetsClient 초기화
        
        Args:
            credentials_path: 서비스 계정 인증 파일 경로
            spreadsheet_id: Google 스프레드시트 ID
        """
        from dotenv import load_dotenv
        load_dotenv()
        
        self.credentials_path = credentials_path or os.getenv('GOOGLE_CREDENTIALS_FILE')
        self.spreadsheet_id = spreadsheet_id or os.getenv('GOOGLE_SHEET_KEY')
        
        if not self.credentials_path:
            raise ValueError("Google credentials file path is required")
        
        if not self.spreadsheet_id:
            raise ValueError("Google spreadsheet ID is required")
        
        self.service = None
        self.gspread_client = None
        self.spreadsheet = None
        self._token_cache = None
        self._token_expiry = None
        
        # 로거 설정
        self.logger = logging.getLogger(__name__)
        
        # API 제한 설정
        self.api_quota = int(os.getenv('GOOGLE_SHEETS_API_QUOTA', '100'))
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
        
        self.logger.info(f"GoogleSheetsClient initialized with spreadsheet_id: {self.spreadsheet_id}")
    
    async def authenticate(self) -> bool:
        """
        Google API 인증 수행
        
        Returns:
            bool: 인증 성공 여부
            
        Raises:
            AuthenticationError: 인증 실패 시
        """
        try:
            # 서비스 계정 인증 범위 설정
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # 서비스 계정 인증 정보 로드
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scopes
            )
            
            # Google Sheets API 서비스 생성
            self.service = build('sheets', 'v4', credentials=self.credentials)
            
            # gspread 클라이언트 생성
            self.gspread_client = gspread.authorize(self.credentials)
            
            # 스프레드시트 접속
            self.spreadsheet = self.gspread_client.open_by_key(self.spreadsheet_id)
            
            self.logger.info("Google Sheets authentication successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Google Sheets authentication failed: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    async def get_spreadsheet_info(self) -> Dict[str, Any]:
        """
        스프레드시트 정보 조회
        
        Returns:
            Dict[str, Any]: 스프레드시트 정보
        """
        if not self.spreadsheet:
            await self.authenticate()
        
        try:
            worksheets = self.spreadsheet.worksheets()
            
            return {
                'title': self.spreadsheet.title,
                'spreadsheet_id': self.spreadsheet_id,
                'worksheets': [
                    {
                        'title': ws.title,
                        'row_count': ws.row_count,
                        'col_count': ws.col_count
                    }
                    for ws in worksheets
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get spreadsheet info: {str(e)}")
            raise APIError(f"Failed to get spreadsheet info: {str(e)}")
    
    async def get_sheet_data(
        self, 
        range_name: str,
        max_retries: int = None
    ) -> List[List[Any]]:
        """
        시트 데이터 조회
        
        Args:
            range_name: 조회 범위 (예: "Sheet1!A:Z")
            max_retries: 최대 재시도 횟수
            
        Returns:
            List[List[Any]]: 시트 데이터
            
        Raises:
            APIError: API 호출 실패 시
            RateLimitError: API 제한 초과 시
        """
        if not self.service:
            await self.authenticate()
        
        max_retries = max_retries or self.max_retries
        
        for attempt in range(max_retries + 1):
            try:
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name
                ).execute()
                
                values = result.get('values', [])
                self.logger.info(f"Retrieved {len(values)} rows from range '{range_name}'")
                return values
                
            except HttpError as e:
                status_code = e.resp.status
                
                if status_code == 429:  # Rate limit exceeded
                    retry_after = int(e.resp.headers.get('Retry-After', 60))
                    if attempt == max_retries:
                        raise RateLimitError(retry_after)
                    
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    self.logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                    continue
                
                elif status_code == 401:  # Unauthorized
                    self.logger.error("Authentication failed, token may be expired")
                    raise AuthenticationError("Authentication failed")
                
                elif status_code == 403:  # Forbidden
                    self.logger.error("Access forbidden, check permissions")
                    raise APIError("Access forbidden", status_code)
                
                elif status_code == 404:  # Not found
                    self.logger.error(f"Range '{range_name}' not found")
                    raise APIError(f"Range '{range_name}' not found", status_code)
                
                else:  # Other API errors
                    if attempt == max_retries:
                        raise APIError(f"API error: {str(e)}", status_code)
                    
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    self.logger.warning(f"API error, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                    continue
            
            except Exception as e:
                if attempt == max_retries:
                    raise APIError(f"Unexpected error: {str(e)}")
                
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                self.logger.warning(f"Unexpected error, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
                continue
    
    async def update_sheet_data(
        self,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED"
    ) -> Dict[str, Any]:
        """
        시트 데이터 업데이트
        
        Args:
            range_name: 업데이트 범위
            values: 업데이트할 데이터
            value_input_option: 값 입력 옵션 ("USER_ENTERED" 또는 "RAW")
            
        Returns:
            Dict[str, Any]: 업데이트 결과
            
        Raises:
            APIError: API 호출 실패 시
            ValidationError: 데이터 유효성 검사 실패 시
        """
        if not self.service:
            await self.authenticate()
        
        if not values:
            raise ValidationError("No data to update")
        
        try:
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            
            updated_rows = result.get('updatedRows', 0)
            updated_columns = result.get('updatedColumns', 0)
            updated_cells = result.get('updatedCells', 0)
            
            self.logger.info(f"Updated {updated_rows} rows, {updated_columns} columns, {updated_cells} cells in range '{range_name}'")
            
            return result
            
        except HttpError as e:
            status_code = e.resp.status
            error_msg = f"Failed to update range '{range_name}': {str(e)}"
            self.logger.error(error_msg)
            raise APIError(error_msg, status_code)
        
        except Exception as e:
            error_msg = f"Unexpected error updating range '{range_name}': {str(e)}"
            self.logger.error(error_msg)
            raise APIError(error_msg)
    
    async def append_sheet_data(
        self,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED"
    ) -> Dict[str, Any]:
        """
        시트 데이터 추가
        
        Args:
            range_name: 추가할 범위
            values: 추가할 데이터
            value_input_option: 값 입력 옵션
            
        Returns:
            Dict[str, Any]: 추가 결과
        """
        if not self.service:
            await self.authenticate()
        
        if not values:
            raise ValidationError("No data to append")
        
        try:
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()
            
            updated_rows = result.get('updates', {}).get('updatedRows', 0)
            updated_columns = result.get('updates', {}).get('updatedColumns', 0)
            updated_cells = result.get('updates', {}).get('updatedCells', 0)
            
            self.logger.info(f"Appended {updated_rows} rows, {updated_columns} columns, {updated_cells} cells to range '{range_name}'")
            
            return result
            
        except HttpError as e:
            status_code = e.resp.status
            error_msg = f"Failed to append to range '{range_name}': {str(e)}"
            self.logger.error(error_msg)
            raise APIError(error_msg, status_code)
        
        except Exception as e:
            error_msg = f"Unexpected error appending to range '{range_name}': {str(e)}"
            self.logger.error(error_msg)
            raise APIError(error_msg)
    
    async def clear_sheet_data(self, range_name: str) -> Dict[str, Any]:
        """
        시트 데이터 삭제
        
        Args:
            range_name: 삭제할 범위
            
        Returns:
            Dict[str, Any]: 삭제 결과
        """
        if not self.service:
            await self.authenticate()
        
        try:
            result = self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            cleared_rows = result.get('clearedRows', 0)
            cleared_columns = result.get('clearedColumns', 0)
            cleared_cells = result.get('clearedCells', 0)
            
            self.logger.info(f"Cleared {cleared_rows} rows, {cleared_columns} columns, {cleared_cells} cells in range '{range_name}'")
            
            return result
            
        except HttpError as e:
            status_code = e.resp.status
            error_msg = f"Failed to clear range '{range_name}': {str(e)}"
            self.logger.error(error_msg)
            raise APIError(error_msg, status_code)
        
        except Exception as e:
            error_msg = f"Unexpected error clearing range '{range_name}': {str(e)}"
            self.logger.error(error_msg)
            raise APIError(error_msg)
    
    async def get_worksheet_by_title(self, title: str):
        """
        제목으로 워크시트 조회
        
        Args:
            title: 워크시트 제목
            
        Returns:
            gspread.Worksheet: 워크시트 객체
        """
        if not self.spreadsheet:
            await self.authenticate()
        
        try:
            return self.spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            raise APIError(f"Worksheet '{title}' not found")
        except Exception as e:
            raise APIError(f"Failed to get worksheet '{title}': {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        시스템 헬스체크
        
        Returns:
            Dict[str, Any]: 헬스체크 결과
        """
        try:
            # 인증 상태 확인
            if not self.spreadsheet:
                await self.authenticate()
            
            # 기본 API 호출 테스트
            spreadsheet_info = await self.get_spreadsheet_info()
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "google_sheets": "connected",
                "spreadsheet_title": spreadsheet_info['title'],
                "worksheet_count": len(spreadsheet_info['worksheets'])
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "google_sheets": "disconnected"
            }


# 전역 클라이언트 인스턴스 (싱글톤 패턴)
_client_instance: Optional[GoogleSheetsClient] = None


async def get_google_sheets_client() -> GoogleSheetsClient:
    """
    Google Sheets 클라이언트 싱글톤 인스턴스 조회
    
    Returns:
        GoogleSheetsClient: 클라이언트 인스턴스
    """
    global _client_instance
    
    if _client_instance is None:
        _client_instance = GoogleSheetsClient()
        await _client_instance.authenticate()
    
    return _client_instance


async def close_google_sheets_client():
    """Google Sheets 클라이언트 리소스 정리"""
    global _client_instance
    _client_instance = None
