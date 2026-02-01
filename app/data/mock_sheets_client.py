"""
MockSheetsClient — Google Sheets API 없이 동작하는 Mock 클라이언트.

--local-only 모드에서 ETEDA 파이프라인 테스트용.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional


class MockSheetsClient:
    """Google Sheets API 호출 없이 빈/고정 데이터 반환."""

    def __init__(self, spreadsheet_id: str = "mock-spreadsheet-id"):
        self._spreadsheet_id = spreadsheet_id
        self._logger = logging.getLogger(__name__)
        self._logger.info("MockSheetsClient initialized")

    @property
    def spreadsheet_id(self) -> str:
        return self._spreadsheet_id
