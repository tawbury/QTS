"""
T_Ledger Repository

매매 거래 원장(T_Ledger) 시트의 데이터를 관리하는 리포지토리입니다.
Data Contract: timestamp, symbol, market, side, qty, price, amount_local,
               currency, fx_rate, amount_krw, fee_tax, net_amount_krw,
               order_id, strategy, position_after, hold_days, pnl, pnl_pct,
               tag, broker, note (docs/arch/04_Data_Contract_Spec.md).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base_repository import BaseSheetRepository
from ...shared.timezone_utils import now_kst


class T_LedgerRepository(BaseSheetRepository):
    """
    T_Ledger 리포지토리

    매매 거래 원장 데이터(table 타입, A:U 21개 컬럼).
    ID = order_id 또는 timestamp+symbol 복합키.
    """

    # gssheet.json 스키마 기반 컬럼 순서
    COLUMNS = [
        "timestamp", "symbol", "market", "side", "qty", "price",
        "amount_local", "currency", "fx_rate", "amount_krw", "fee_tax",
        "net_amount_krw", "order_id", "strategy", "position_after",
        "hold_days", "pnl", "pnl_pct", "tag", "broker", "note",
    ]

    def __init__(self, client: Any, spreadsheet_id: str):
        super().__init__(client, spreadsheet_id, "T_Ledger")
        self.required_fields = ["timestamp", "symbol", "side"]
        self.logger.info(f"T_LedgerRepository initialized for sheet '{self.sheet_name}'")

    async def get_all(self) -> List[Dict[str, Any]]:
        """모든 거래 원장 데이터 조회"""
        try:
            headers = await self.get_headers()
            if not headers:
                headers = self.COLUMNS

            range_name = f"{self.sheet_name}!A{self.header_row + 1}:U"
            raw_data = await self.client.get_sheet_data(range_name)

            result = []
            for row in raw_data:
                if row and any(str(cell).strip() for cell in row):
                    record = self._row_to_dict(row, headers)
                    if record.get("timestamp") is not None and record.get("timestamp") != "":
                        result.append(record)

            self.logger.info(f"Retrieved {len(result)} T_Ledger records")
            return result

        except Exception as e:
            self.logger.error(f"Failed to get T_Ledger data: {str(e)}")
            raise

    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """order_id로 거래 조회"""
        try:
            all_data = await self.get_all()
            for record in all_data:
                if str(record.get("order_id", "")) == str(record_id):
                    return record
            return None
        except Exception as e:
            self.logger.error(f"Failed to get T_Ledger by order_id '{record_id}': {str(e)}")
            raise

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """거래 원장 레코드 생성 (append)"""
        try:
            self._validate_required_fields(data, self.required_fields)
            sanitized = self._sanitize_data(data)

            headers = await self.get_headers()
            if not headers:
                headers = self.COLUMNS
            row_data = self._dict_to_row(sanitized, headers)

            range_name = f"{self.sheet_name}!A:U"
            await self.client.append_sheet_data(range_name, [row_data])

            self.logger.info(f"Created T_Ledger record: {sanitized.get('order_id', 'N/A')}")
            return sanitized

        except Exception as e:
            self.logger.error(f"Failed to create T_Ledger record: {str(e)}")
            raise

    async def append_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        매매 실행 결과를 T_Ledger에 추가 (편의 메서드).

        ETEDARunner._act() 결과를 T_Ledger 스키마에 맞게 변환 후 저장.
        """
        now = now_kst()
        record = {
            "timestamp": trade_data.get("timestamp") or now.isoformat(),
            "symbol": trade_data.get("symbol", ""),
            "market": trade_data.get("market", ""),
            "side": trade_data.get("side", trade_data.get("action", "")),
            "qty": trade_data.get("qty", trade_data.get("quantity", "")),
            "price": trade_data.get("price", ""),
            "amount_local": trade_data.get("amount_local", ""),
            "currency": trade_data.get("currency", "KRW"),
            "fx_rate": trade_data.get("fx_rate", "1"),
            "amount_krw": trade_data.get("amount_krw", ""),
            "fee_tax": trade_data.get("fee_tax", ""),
            "net_amount_krw": trade_data.get("net_amount_krw", ""),
            "order_id": trade_data.get("order_id", trade_data.get("intent_id", "")),
            "strategy": trade_data.get("strategy", ""),
            "position_after": trade_data.get("position_after", ""),
            "hold_days": trade_data.get("hold_days", ""),
            "pnl": trade_data.get("pnl", ""),
            "pnl_pct": trade_data.get("pnl_pct", ""),
            "tag": trade_data.get("tag", ""),
            "broker": trade_data.get("broker", ""),
            "note": trade_data.get("note", trade_data.get("mode", "")),
        }
        return await self.create(record)

    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """order_id 기준 거래 레코드 업데이트"""
        try:
            existing = await self.get_by_id(record_id)
            if not existing:
                raise ValueError(f"T_Ledger record for order_id '{record_id}' not found")

            updated = {**existing, **data}
            sanitized = self._sanitize_data(updated)

            row_number = await self._find_row_by_id(record_id, "order_id")
            if not row_number:
                raise ValueError(f"Row not found for order_id '{record_id}'")

            headers = await self.get_headers()
            if not headers:
                headers = self.COLUMNS
            row_data = self._dict_to_row(sanitized, headers)

            range_name = f"{self.sheet_name}!A{row_number}:U{row_number}"
            await self.client.update_sheet_data(range_name, [row_data])

            self.logger.info(f"Updated T_Ledger record: {record_id}")
            return sanitized

        except Exception as e:
            self.logger.error(f"Failed to update T_Ledger record '{record_id}': {str(e)}")
            raise

    async def delete(self, record_id: str) -> bool:
        """order_id 기준 거래 레코드 삭제"""
        try:
            row_number = await self._find_row_by_id(record_id, "order_id")
            if not row_number:
                return False

            headers = await self.get_headers()
            if not headers:
                headers = self.COLUMNS
            empty_row = [""] * len(headers)

            range_name = f"{self.sheet_name}!A{row_number}:U{row_number}"
            await self.client.update_sheet_data(range_name, [empty_row])

            self.logger.info(f"Deleted T_Ledger record: {record_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete T_Ledger record '{record_id}': {str(e)}")
            raise

    async def exists(self, record_id: str) -> bool:
        """order_id 존재 여부 확인"""
        try:
            return await self.get_by_id(record_id) is not None
        except Exception as e:
            self.logger.error(f"Failed to check T_Ledger existence '{record_id}': {str(e)}")
            return False

    async def get_by_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """종목별 거래 이력 조회"""
        try:
            all_data = await self.get_all()
            return [r for r in all_data if str(r.get("symbol", "")) == str(symbol)]
        except Exception as e:
            self.logger.error(f"Failed to get T_Ledger by symbol '{symbol}': {str(e)}")
            raise

    async def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """날짜 범위로 거래 이력 조회"""
        try:
            all_data = await self.get_all()
            return [
                r for r in all_data
                if start_date <= str(r.get("timestamp", ""))[:10] <= end_date
            ]
        except Exception as e:
            self.logger.error(f"Failed to get T_Ledger by date range: {str(e)}")
            raise
