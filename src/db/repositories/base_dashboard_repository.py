"""
Dashboard 리포지토리 베이스 클래스

Dashboard 타입 시트(Portfolio, Performance)의 공통 셀 접근 로직을 제공합니다.
블록 단위 셀 주소 기반 읽기/쓰기를 지원합니다.
"""
from __future__ import annotations

from typing import Any
import logging


class BaseDashboardRepository:
    """
    Dashboard 리포지토리 베이스 클래스

    셀 주소 기반 읽기/쓰기 공통 메서드를 제공합니다.
    서브클래스는 SHEET_NAME을 정의해야 합니다.
    """

    SHEET_NAME: str = ""

    def __init__(self, client: Any, spreadsheet_id: str, project_root: Any = None):
        self._client = client
        self._sid = spreadsheet_id
        self._project_root = project_root
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _get_worksheet(self):
        """현재 시트의 gspread Worksheet 객체 획득"""
        spreadsheet = getattr(self._client, "spreadsheet", None)
        if spreadsheet is None:
            spreadsheet = self._client.gspread_client.open_by_key(self._sid)
        return spreadsheet.worksheet(self.SHEET_NAME)

    def _update_cell(self, cell_address: str, value: Any) -> bool:
        """개별 셀 업데이트"""
        try:
            ws = self._get_worksheet()
            ws.update([[value]], range_name=cell_address)
            self.logger.debug(f"Updated {self.SHEET_NAME}!{cell_address}: {value}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update {self.SHEET_NAME}!{cell_address}: {str(e)}")
            return False

    def _get_cell(self, cell_address: str) -> Any:
        """개별 셀 값 조회"""
        try:
            ws = self._get_worksheet()
            return ws.acell(cell_address).value
        except Exception as e:
            self.logger.error(f"Failed to get {self.SHEET_NAME}!{cell_address}: {str(e)}")
            return None
