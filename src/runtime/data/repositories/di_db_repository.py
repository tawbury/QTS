"""
DI_DB 리포지토리

가격/지표 데이터(DI_DB) 시트를 관리합니다.
전략 엔진에서 참조하는 symbol, price, change_pct, volatility, ma20, ma60, volume 등.
docs/arch/04_Data_Contract_Spec.md §2.2.3 DI_DB Contract.
"""

from typing import List, Dict, Any, Optional
import logging

from .base_repository import BaseSheetRepository


class DI_DBRepository(BaseSheetRepository):
    """
    DI_DB 리포지토리

    DI_DB Contract: symbol, price, change_pct, volatility, ma20, ma60, volume.
    ID = symbol.
    """

    def __init__(self, client, spreadsheet_id: str):
        super().__init__(client, spreadsheet_id, "DI_DB")
        self.required_fields = ["Symbol"]
        self.logger.info(f"DI_DBRepository initialized for sheet '{self.sheet_name}'")

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
                    if record.get("Symbol"):
                        result.append(record)
            self.logger.info(f"Retrieved {len(result)} DI_DB records")
            return result
        except Exception as e:
            self.logger.error(f"Failed to get DI_DB data: {str(e)}")
            raise

    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        try:
            all_data = await self.get_all()
            for record in all_data:
                if str(record.get("Symbol", "")).upper() == str(record_id).upper():
                    return record
            return None
        except Exception as e:
            self.logger.error(f"Failed to get DI_DB by symbol '{record_id}': {str(e)}")
            raise

    async def get_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """symbol로 종목 가격/지표 조회."""
        return await self.get_by_id(symbol)

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._validate_required_fields(data, self.required_fields)
            sanitized = self._sanitize_data(data)
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized, headers)
            range_name = f"{self.sheet_name}!A:Z"
            await self.client.append_sheet_data(range_name, [row_data])
            self.logger.info(f"Created DI_DB record: {sanitized.get('Symbol')}")
            return sanitized
        except Exception as e:
            self.logger.error(f"Failed to create DI_DB record: {str(e)}")
            raise

    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            existing = await self.get_by_id(record_id)
            if not existing:
                raise ValueError(f"DI_DB record for symbol '{record_id}' not found")
            updated = {**existing, **data}
            sanitized = self._sanitize_data(updated)
            row_number = await self._find_row_by_id(record_id, "Symbol")
            if not row_number:
                raise ValueError(f"Row not found for symbol '{record_id}'")
            headers = await self.get_headers()
            row_data = self._dict_to_row(sanitized, headers)
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [row_data])
            self.logger.info(f"Updated DI_DB record: {record_id}")
            return sanitized
        except Exception as e:
            self.logger.error(f"Failed to update DI_DB record '{record_id}': {str(e)}")
            raise

    async def delete(self, record_id: str) -> bool:
        try:
            row_number = await self._find_row_by_id(record_id, "Symbol")
            if not row_number:
                return False
            headers = await self.get_headers()
            empty_row = [""] * len(headers)
            range_name = f"{self.sheet_name}!A{row_number}:Z{row_number}"
            await self.client.update_sheet_data(range_name, [empty_row])
            self.logger.info(f"Deleted DI_DB record: {record_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete DI_DB record '{record_id}': {str(e)}")
            raise

    async def exists(self, record_id: str) -> bool:
        try:
            return await self.get_by_id(record_id) is not None
        except Exception as e:
            self.logger.error(f"Failed to check DI_DB existence '{record_id}': {str(e)}")
            return False
