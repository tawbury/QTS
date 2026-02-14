"""
Position Repository

보유 포지션(Position) 시트의 데이터를 관리하는 리포지토리입니다.
Data Contract: symbol, name, market, qty, avg_price_current_currency, ...
               (docs/arch/04_Data_Contract_Spec.md §2.2.3).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base_repository import BaseSheetRepository


class PositionRepository(BaseSheetRepository):
    """
    Position 리포지토리

    보유 포지션 데이터(table 타입, A:T 20개 컬럼).
    ID = symbol (종목 코드가 고유 키).
    """

    COLUMNS = [
        "symbol", "name", "market", "qty",
        "avg_price_current_currency", "current_price_current_currency",
        "avg_price_krw", "current_price_krw", "market_value_krw",
        "unrealized_pnl_krw", "unrealized_pnl_pct", "strategy",
        "atr", "atr_pct", "last_atr_pct", "atr_stop", "atr_target",
        "sector", "tag", "note",
    ]

    def __init__(self, client: Any, spreadsheet_id: str):
        super().__init__(client, spreadsheet_id, "Position")
        self.required_fields = ["symbol"]
        self.logger.info(f"PositionRepository initialized for sheet '{self.sheet_name}'")

    async def get_all(self) -> List[Dict[str, Any]]:
        """모든 보유 포지션 조회"""
        try:
            headers = await self.get_headers()
            if not headers:
                headers = self.COLUMNS

            range_name = f"{self.sheet_name}!A{self.header_row + 1}:T"
            raw_data = await self.client.get_sheet_data(range_name)

            result = []
            for row in raw_data:
                if row and any(str(cell).strip() for cell in row):
                    record = self._row_to_dict(row, headers)
                    if record.get("symbol") is not None and record.get("symbol") != "":
                        result.append(record)

            self.logger.info(f"Retrieved {len(result)} Position records")
            return result

        except Exception as e:
            self.logger.error(f"Failed to get Position data: {str(e)}")
            raise

    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """symbol로 포지션 조회"""
        try:
            all_data = await self.get_all()
            for record in all_data:
                if str(record.get("symbol", "")) == str(record_id):
                    return record
            return None
        except Exception as e:
            self.logger.error(f"Failed to get Position by symbol '{record_id}': {str(e)}")
            raise

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """포지션 레코드 생성"""
        try:
            self._validate_required_fields(data, self.required_fields)
            sanitized = self._sanitize_data(data)

            headers = await self.get_headers()
            if not headers:
                headers = self.COLUMNS
            row_data = self._dict_to_row(sanitized, headers)

            range_name = f"{self.sheet_name}!A:T"
            await self.client.append_sheet_data(range_name, [row_data])

            self.logger.info(f"Created Position record: {sanitized.get('symbol')}")
            return sanitized

        except Exception as e:
            self.logger.error(f"Failed to create Position record: {str(e)}")
            raise

    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """symbol 기준 포지션 업데이트"""
        try:
            existing = await self.get_by_id(record_id)
            if not existing:
                raise ValueError(f"Position record for symbol '{record_id}' not found")

            updated = {**existing, **data}
            sanitized = self._sanitize_data(updated)

            row_number = await self._find_row_by_id(record_id, "symbol")
            if not row_number:
                raise ValueError(f"Row not found for symbol '{record_id}'")

            headers = await self.get_headers()
            if not headers:
                headers = self.COLUMNS
            row_data = self._dict_to_row(sanitized, headers)

            range_name = f"{self.sheet_name}!A{row_number}:T{row_number}"
            await self.client.update_sheet_data(range_name, [row_data])

            self.logger.info(f"Updated Position record: {record_id}")
            return sanitized

        except Exception as e:
            self.logger.error(f"Failed to update Position record '{record_id}': {str(e)}")
            raise

    async def upsert_position(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        포지션 upsert (있으면 업데이트, 없으면 생성).

        매매 후 보유 포지션 동기화에 사용.
        """
        symbol = data.get("symbol", "")
        existing = await self.get_by_id(symbol)

        if existing:
            return await self.update(symbol, data)
        else:
            return await self.create(data)

    async def remove_position(self, symbol: str) -> bool:
        """포지션 완전 청산 시 행 삭제"""
        return await self.delete(symbol)

    async def delete(self, record_id: str) -> bool:
        """symbol 기준 포지션 삭제"""
        try:
            row_number = await self._find_row_by_id(record_id, "symbol")
            if not row_number:
                return False

            headers = await self.get_headers()
            if not headers:
                headers = self.COLUMNS
            empty_row = [""] * len(headers)

            range_name = f"{self.sheet_name}!A{row_number}:T{row_number}"
            await self.client.update_sheet_data(range_name, [empty_row])

            self.logger.info(f"Deleted Position record: {record_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete Position record '{record_id}': {str(e)}")
            raise

    async def exists(self, record_id: str) -> bool:
        """symbol 존재 여부 확인"""
        try:
            return await self.get_by_id(record_id) is not None
        except Exception as e:
            self.logger.error(f"Failed to check Position existence '{record_id}': {str(e)}")
            return False
