"""
DT_Report 리포지토리

일일 리포트(DT_Report) 시트를 관리합니다.
Performance Engine의 Daily Report → DT_Report 시트 기록 (docs/arch/02_Engine_Core §8.6).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .base_repository import BaseSheetRepository


class DT_ReportRepository(BaseSheetRepository):
    """
    DT_Report 리포지토리

    일별 리포트 데이터. ID = Date(일자).
    """

    def __init__(self, client, spreadsheet_id: str):
        super().__init__(client, spreadsheet_id, "DT_Report")
        self.required_fields = ["Date"]
        self.logger.info(f"DT_ReportRepository initialized for sheet '{self.sheet_name}'")

    async def get_all(self) -> List[Dict[str, Any]]:
        try:
            headers = await self.get_headers()
            if not headers:
                return []
            range_name = f"{self.sheet_name}!A{self.header_row + 1}:Z"
            raw_data = await self.client.get_sheet_data(range_name)
            result = []
            for row in raw_data:
                if row and any(str(cell).strip() for cell in row):
                    record = self._row_to_dict(row, headers)
                    if record.get("Date"):
                        result.append(record)
            self.logger.info(f"Retrieved {len(result)} DT_Report records")
            return result
        except Exception as e:
            self.logger.error(f"Failed to get DT_Report data: {str(e)}")
            raise

    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        try:
            all_data = await self.get_all()
            for record in all_data:
                if str(record.get("Date", "")) == str(record_id):
                    return record
            return None
        except Exception as e:
            self.logger.error(f"Failed to get DT_Report by date '{record_id}': {str(e)}")
            raise

    async def get_report_by_date(self, report_date: str) -> Optional[Dict[str, Any]]:
        """일자별 리포트 조회."""
        return await self.get_by_id(report_date)

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if "Date" not in data or not data["Date"]:
                data = {**data, "Date": datetime.now().strftime("%Y-%m-%d")}
            self._validate_required_fields(data, self.required_fields)
            sanitized = self._sanitize_data(data)
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized, headers)
            range_name = f"{self.sheet_name}!A:Z"
            await self.client.append_sheet_data(range_name, [row_data])
            self.logger.info(f"Created DT_Report record: {sanitized.get('Date')}")
            return sanitized
        except Exception as e:
            self.logger.error(f"Failed to create DT_Report record: {str(e)}")
            raise

    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            existing = await self.get_by_id(record_id)
            if not existing:
                raise ValueError(f"DT_Report record for date '{record_id}' not found")
            updated = {**existing, **data}
            sanitized = self._sanitize_data(updated)
            row_number = await self._find_row_by_id(record_id, "Date")
            if not row_number:
                raise ValueError(f"Row not found for date '{record_id}'")
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized, headers)
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [row_data])
            self.logger.info(f"Updated DT_Report record: {record_id}")
            return sanitized
        except Exception as e:
            self.logger.error(f"Failed to update DT_Report record '{record_id}': {str(e)}")
            raise

    async def delete(self, record_id: str) -> bool:
        try:
            row_number = await self._find_row_by_id(record_id, "Date")
            if not row_number:
                return False
            headers = await self.get_headers()
            empty_row = [""] * len(headers)
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [empty_row])
            self.logger.info(f"Deleted DT_Report record: {record_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete DT_Report record '{record_id}': {str(e)}")
            raise

    async def exists(self, record_id: str) -> bool:
        try:
            return await self.get_by_id(record_id) is not None
        except Exception as e:
            self.logger.error(f"Failed to check DT_Report existence '{record_id}': {str(e)}")
            return False
