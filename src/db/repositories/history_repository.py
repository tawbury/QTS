"""
History Repository

일별 성과(History) 시트의 데이터를 관리하는 리포지토리입니다.
Data Contract: date, total_equity, daily_pnl, daily_return, cumulative_return,
               volatility_20d, high_watermark, drawdown, mdd, note
               (docs/arch/04_Data_Contract_Spec.md).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base_repository import BaseSheetRepository
from ...shared.timezone_utils import now_kst


class HistoryRepository(BaseSheetRepository):
    """
    History 리포지토리

    일별 성과 데이터(table 타입, A:J 10개 컬럼).
    ID = date (날짜가 고유 키).
    """

    COLUMNS = [
        "date", "total_equity", "daily_pnl", "daily_return",
        "cumulative_return", "volatility_20d", "high_watermark",
        "drawdown", "mdd", "note",
    ]

    def __init__(self, client: Any, spreadsheet_id: str):
        super().__init__(client, spreadsheet_id, "History")
        self.required_fields = ["date"]
        self.logger.info(f"HistoryRepository initialized for sheet '{self.sheet_name}'")

    async def get_all(self) -> List[Dict[str, Any]]:
        """모든 일별 성과 데이터 조회"""
        try:
            headers = await self.get_headers()
            if not headers:
                headers = self.COLUMNS

            range_name = f"{self.sheet_name}!A{self.header_row + 1}:J"
            raw_data = await self.client.get_sheet_data(range_name)

            result = []
            for row in raw_data:
                if row and any(str(cell).strip() for cell in row):
                    record = self._row_to_dict(row, headers)
                    if record.get("date") is not None and record.get("date") != "":
                        result.append(record)

            self.logger.info(f"Retrieved {len(result)} History records")
            return result

        except Exception as e:
            self.logger.error(f"Failed to get History data: {str(e)}")
            raise

    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """date로 일별 성과 조회"""
        try:
            all_data = await self.get_all()
            for record in all_data:
                if str(record.get("date", "")) == str(record_id):
                    return record
            return None
        except Exception as e:
            self.logger.error(f"Failed to get History by date '{record_id}': {str(e)}")
            raise

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """일별 성과 레코드 생성"""
        try:
            self._validate_required_fields(data, self.required_fields)
            sanitized = self._sanitize_data(data)

            headers = await self.get_headers()
            if not headers:
                headers = self.COLUMNS
            row_data = self._dict_to_row(sanitized, headers)

            range_name = f"{self.sheet_name}!A:J"
            await self.client.append_sheet_data(range_name, [row_data])

            self.logger.info(f"Created History record: {sanitized.get('date')}")
            return sanitized

        except Exception as e:
            self.logger.error(f"Failed to create History record: {str(e)}")
            raise

    async def append_daily_record(self, daily_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        일별 성과 추가 (편의 메서드).

        이미 동일 날짜가 있으면 업데이트, 없으면 새로 생성.
        """
        today = daily_data.get("date") or now_kst().strftime("%Y-%m-%d")
        daily_data["date"] = today

        existing = await self.get_by_id(today)
        if existing:
            return await self.update(today, daily_data)
        else:
            return await self.create(daily_data)

    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """date 기준 일별 성과 업데이트"""
        try:
            existing = await self.get_by_id(record_id)
            if not existing:
                raise ValueError(f"History record for date '{record_id}' not found")

            updated = {**existing, **data}
            sanitized = self._sanitize_data(updated)

            row_number = await self._find_row_by_id(record_id, "date")
            if not row_number:
                raise ValueError(f"Row not found for date '{record_id}'")

            headers = await self.get_headers()
            if not headers:
                headers = self.COLUMNS
            row_data = self._dict_to_row(sanitized, headers)

            range_name = f"{self.sheet_name}!A{row_number}:J{row_number}"
            await self.client.update_sheet_data(range_name, [row_data])

            self.logger.info(f"Updated History record: {record_id}")
            return sanitized

        except Exception as e:
            self.logger.error(f"Failed to update History record '{record_id}': {str(e)}")
            raise

    async def delete(self, record_id: str) -> bool:
        """date 기준 일별 성과 삭제"""
        try:
            row_number = await self._find_row_by_id(record_id, "date")
            if not row_number:
                return False

            headers = await self.get_headers()
            if not headers:
                headers = self.COLUMNS
            empty_row = [""] * len(headers)

            range_name = f"{self.sheet_name}!A{row_number}:J{row_number}"
            await self.client.update_sheet_data(range_name, [empty_row])

            self.logger.info(f"Deleted History record: {record_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete History record '{record_id}': {str(e)}")
            raise

    async def exists(self, record_id: str) -> bool:
        """date 존재 여부 확인"""
        try:
            return await self.get_by_id(record_id) is not None
        except Exception as e:
            self.logger.error(f"Failed to check History existence '{record_id}': {str(e)}")
            return False

    async def get_latest(self, n: int = 1) -> List[Dict[str, Any]]:
        """최근 N일 성과 조회"""
        try:
            all_data = await self.get_all()
            return all_data[-n:] if all_data else []
        except Exception as e:
            self.logger.error(f"Failed to get latest History: {str(e)}")
            raise
