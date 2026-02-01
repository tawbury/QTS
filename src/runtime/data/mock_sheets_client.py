"""
Mock Google Sheets Client for local-only mode.

GoogleSheetsClient와 동일한 인터페이스를 제공하지만,
실제 API 호출 없이 빈 데이터 또는 mock 데이터를 반환합니다.
--local-only 모드에서 API 의존성 없이 파이프라인을 테스트할 수 있습니다.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional


class MockSheetsClient:
    """
    Mock Google Sheets Client

    GoogleSheetsClient와 동일한 인터페이스를 제공하지만,
    실제 Google API 호출 없이 동작합니다.
    """

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        spreadsheet_id: Optional[str] = None,
    ):
        """
        MockSheetsClient 초기화

        Args:
            credentials_path: (무시됨) 호환성을 위해 유지
            spreadsheet_id: (무시됨) 호환성을 위해 유지
        """
        self.credentials_path = credentials_path or "mock_credentials"
        self.spreadsheet_id = spreadsheet_id or "mock_spreadsheet_id"
        self.logger = logging.getLogger(__name__)

        # Mock 데이터 저장소
        self._mock_data: Dict[str, List[List[Any]]] = {}

        self.logger.info(
            f"MockSheetsClient initialized (spreadsheet_id: {self.spreadsheet_id})"
        )

    async def authenticate(self) -> bool:
        """Mock 인증 (항상 성공)"""
        self.logger.info("MockSheetsClient: authenticate() - always succeeds")
        return True

    async def get_spreadsheet_info(self) -> Dict[str, Any]:
        """Mock 스프레드시트 정보 반환"""
        return {
            "title": "Mock Spreadsheet",
            "spreadsheet_id": self.spreadsheet_id,
            "worksheets": [
                {"title": "Position", "row_count": 100, "col_count": 26},
                {"title": "Portfolio", "row_count": 100, "col_count": 26},
                {"title": "T_Ledger", "row_count": 100, "col_count": 26},
                {"title": "History", "row_count": 100, "col_count": 26},
                {"title": "Performance", "row_count": 100, "col_count": 26},
            ],
        }

    async def get_sheet_data(
        self,
        range_name: str,
        max_retries: int = None,
    ) -> List[List[Any]]:
        """
        Mock 시트 데이터 반환

        Args:
            range_name: 조회 범위 (예: "Position!A:Z")
            max_retries: (무시됨)

        Returns:
            빈 리스트 또는 미리 설정된 mock 데이터
        """
        self.logger.debug(f"MockSheetsClient: get_sheet_data({range_name})")

        # range_name에서 시트명 추출
        sheet_name = range_name.split("!")[0] if "!" in range_name else range_name

        # 미리 설정된 mock 데이터가 있으면 반환
        if sheet_name in self._mock_data:
            return self._mock_data[sheet_name]

        # 기본: 빈 데이터 반환
        return []

    async def update_sheet_data(
        self,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> Dict[str, Any]:
        """Mock 시트 데이터 업데이트 (로그만 출력)"""
        self.logger.debug(
            f"MockSheetsClient: update_sheet_data({range_name}, {len(values)} rows)"
        )
        return {
            "updatedRows": len(values),
            "updatedColumns": len(values[0]) if values else 0,
            "updatedCells": sum(len(row) for row in values),
        }

    async def append_sheet_data(
        self,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> Dict[str, Any]:
        """Mock 시트 데이터 추가 (로그만 출력)"""
        self.logger.debug(
            f"MockSheetsClient: append_sheet_data({range_name}, {len(values)} rows)"
        )
        return {
            "updates": {
                "updatedRows": len(values),
                "updatedColumns": len(values[0]) if values else 0,
                "updatedCells": sum(len(row) for row in values),
            }
        }

    async def clear_sheet_data(self, range_name: str) -> Dict[str, Any]:
        """Mock 시트 데이터 삭제 (로그만 출력)"""
        self.logger.debug(f"MockSheetsClient: clear_sheet_data({range_name})")
        return {"clearedRows": 0, "clearedColumns": 0, "clearedCells": 0}

    async def get_worksheet_by_title(self, title: str):
        """Mock 워크시트 반환"""
        self.logger.debug(f"MockSheetsClient: get_worksheet_by_title({title})")
        return _MockWorksheet(title)

    async def health_check(self) -> Dict[str, Any]:
        """Mock 헬스체크 (항상 healthy)"""
        from datetime import datetime
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "google_sheets": "mock (not connected)",
            "spreadsheet_title": "Mock Spreadsheet",
            "worksheet_count": 5,
        }

    def set_mock_data(self, sheet_name: str, data: List[List[Any]]) -> None:
        """
        테스트용 mock 데이터 설정

        Args:
            sheet_name: 시트명
            data: mock 데이터 (2D list)
        """
        self._mock_data[sheet_name] = data
        self.logger.debug(f"MockSheetsClient: set_mock_data({sheet_name}, {len(data)} rows)")


class _MockWorksheet:
    """Mock gspread.Worksheet 객체"""

    def __init__(self, title: str):
        self.title = title
        self.row_count = 100
        self.col_count = 26
