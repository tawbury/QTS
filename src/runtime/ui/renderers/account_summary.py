"""
Account Summary Rendering Unit.

UI Contract account 블록 → R_Dash 계좌 요약 영역(A1:D10)용 행 데이터.
docs/arch/06_UI_Architecture.md §3.1, §8.1.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ._display import cell_value


def render_account_summary(account: Dict[str, Any]) -> List[List[Any]]:
    """
    account 블록을 R_Dash 계좌 요약용 행 리스트로 변환.

    Args:
        account: UI Contract §3.1 (total_equity, daily_pnl, ...)

    Returns:
        행 리스트. 첫 행 헤더, 이후 데이터 행.
    """
    if not account:
        return [["total_equity", "daily_pnl", "realized_pnl", "unrealized_pnl", "exposure_pct"], ["-", "-", "-", "-", "-"]]

    headers = ["total_equity", "daily_pnl", "realized_pnl", "unrealized_pnl", "exposure_pct"]
    row = [
        cell_value(account.get("total_equity")),
        cell_value(account.get("daily_pnl")),
        cell_value(account.get("realized_pnl")),
        cell_value(account.get("unrealized_pnl")),
        cell_value(account.get("exposure_pct")),
    ]
    return [headers, row]
