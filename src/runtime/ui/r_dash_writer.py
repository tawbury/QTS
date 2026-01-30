"""
R_Dash Writer — UI Contract → R_Dash 시트 갱신.

ETEDA와 분리: UI 갱신은 이 Writer에서만 수행하며, 비동기로 실행하여
ETEDA 실행을 블록하지 않는다. docs/arch/06_UI_Architecture.md §8.1, §4.3.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from ..data.google_sheets_client import GoogleSheetsClient
from .contract_schema import get_expected_contract_version
from .renderers import (
    render_account_summary,
    render_meta_block,
    render_performance,
    render_pipeline_status,
    render_risk_monitor,
    render_symbol_detail,
)

_log = logging.getLogger(__name__)

# R_Dash 셀 영역 (06_UI_Architecture §8.1)
R_DASH_ACCOUNT = "R_Dash!A1:E10"
R_DASH_SYMBOLS = "R_Dash!A12:H40"
R_DASH_RISK = "R_Dash!F1:I20"
R_DASH_PERFORMANCE = "R_Dash!J1:N20"
R_DASH_PIPELINE = "R_Dash!F25:I33"
R_DASH_META = "R_Dash!J25:N33"


class R_DashWriter:
    """
    UI Contract만 받아 R_Dash 시트를 갱신하는 Writer.

    - Contract 버전 불일치 시 갱신 중단 (06 §10.1, §10.4).
    - ETEDA를 블록하지 않도록 write()는 비동기이며, 호출 측에서
      asyncio.create_task(writer.write(contract)) 로 격리 실행 권장.
    """

    def __init__(self, client: GoogleSheetsClient):
        self._client = client
        if not getattr(client, "spreadsheet_id", None):
            raise ValueError("R_DashWriter requires client with spreadsheet_id")

    async def write(self, contract: Dict[str, Any]) -> None:
        """
        UI Contract로 R_Dash 영역들을 순차 갱신.

        Args:
            contract: UIContractBuilder.build(...) 출력. account, symbols, pipeline_status, meta 필수.

        Raises:
            ValueError: contract_version 불일치 또는 필수 블록 누락 시.
        """
        meta = contract.get("meta") or {}
        version = meta.get("contract_version")
        expected = get_expected_contract_version()
        if version != expected:
            _log.warning("UI Contract version mismatch: got %s, expected %s — skip R_Dash update", version, expected)
            return

        account = contract.get("account")
        pipeline_status = contract.get("pipeline_status")
        if not account or not pipeline_status:
            raise ValueError("contract must contain account and pipeline_status")

        updates: List[tuple[str, List[List[Any]]]] = [
            (R_DASH_ACCOUNT, render_account_summary(account)),
            (R_DASH_SYMBOLS, render_symbol_detail(contract.get("symbols") or [])),
            (R_DASH_RISK, render_risk_monitor(contract.get("risk"))),
            (R_DASH_PERFORMANCE, render_performance(contract.get("performance"))),
            (R_DASH_PIPELINE, render_pipeline_status(pipeline_status)),
            (R_DASH_META, render_meta_block(meta)),
        ]

        for range_name, rows in updates:
            if not rows:
                continue
            try:
                await self._client.update_sheet_data(range_name, rows)
            except Exception as e:
                _log.exception("R_Dash update failed for %s: %s", range_name, e)
                # UI 실패는 매매 중단 사유가 아님 (04_Data_Contract_Spec §7.4)
                raise

    def schedule_write(self, contract: Dict[str, Any]) -> asyncio.Task[None]:
        """
        ETEDA를 블록하지 않도록 write(contract)를 비동기 태스크로 실행.

        호출부는 await하지 않고 반환된 Task만 필요 시 나중에 취소/대기할 수 있다.

        Args:
            contract: UI Contract dict.

        Returns:
            asyncio.Task: write(contract)를 실행하는 태스크.
        """
        return asyncio.create_task(self.write(contract))
