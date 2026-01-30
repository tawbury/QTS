"""
Strategy 리포지토리 (전략 파라미터)

전략 파라미터(Strategy) 시트를 관리합니다.
Data Contract: param_name, value, description (docs/arch/04_Data_Contract_Spec.md §2.2.5).
Strategy Engine 입력용 전략별 파라미터.
"""

from typing import List, Dict, Any, Optional
import logging

from .base_repository import BaseSheetRepository


class StrategyRepository(BaseSheetRepository):
    """
    Strategy 리포지토리 (파라미터)

    Strategy Contract: param_name, value, description.
    ID = param_name.
    """

    def __init__(self, client, spreadsheet_id: str):
        super().__init__(client, spreadsheet_id, "Strategy")
        self.required_fields = ["param_name", "value"]
        self.logger.info(f"StrategyRepository initialized for sheet '{self.sheet_name}'")

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
                    if record.get("param_name") is not None and record.get("param_name") != "":
                        result.append(record)
            self.logger.info(f"Retrieved {len(result)} strategy parameter records")
            return result
        except Exception as e:
            self.logger.error(f"Failed to get Strategy data: {str(e)}")
            raise

    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        try:
            all_data = await self.get_all()
            for record in all_data:
                if str(record.get("param_name", "")) == str(record_id):
                    return record
            return None
        except Exception as e:
            self.logger.error(f"Failed to get Strategy by param_name '{record_id}': {str(e)}")
            raise

    async def get_param(self, param_name: str) -> Optional[Any]:
        """파라미터 값만 조회."""
        record = await self.get_by_id(param_name)
        return record.get("value") if record else None

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._validate_required_fields(data, self.required_fields)
            sanitized = self._sanitize_data(data)
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized, headers)
            range_name = f"{self.sheet_name}!A:Z"
            await self.client.append_sheet_data(range_name, [row_data])
            self.logger.info(f"Created Strategy record: {sanitized.get('param_name')}")
            return sanitized
        except Exception as e:
            self.logger.error(f"Failed to create Strategy record: {str(e)}")
            raise

    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            existing = await self.get_by_id(record_id)
            if not existing:
                raise ValueError(f"Strategy record for param_name '{record_id}' not found")
            updated = {**existing, **data}
            sanitized = self._sanitize_data(updated)
            row_number = await self._find_row_by_id(record_id, "param_name")
            if not row_number:
                raise ValueError(f"Row not found for param_name '{record_id}'")
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized, headers)
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [row_data])
            self.logger.info(f"Updated Strategy record: {record_id}")
            return sanitized
        except Exception as e:
            self.logger.error(f"Failed to update Strategy record '{record_id}': {str(e)}")
            raise

    async def delete(self, record_id: str) -> bool:
        try:
            row_number = await self._find_row_by_id(record_id, "param_name")
            if not row_number:
                return False
            headers = await self.get_headers()
            empty_row = [""] * len(headers)
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [empty_row])
            self.logger.info(f"Deleted Strategy record: {record_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete Strategy record '{record_id}': {str(e)}")
            raise

    async def exists(self, record_id: str) -> bool:
        try:
            return await self.get_by_id(record_id) is not None
        except Exception as e:
            self.logger.error(f"Failed to check Strategy existence '{record_id}': {str(e)}")
            return False
