"""
Symbol Detail Rendering Unit.

UI Contract symbols 블록 → R_Dash 주요 종목 상세 영역(A12:D40)용 행 데이터.
docs/arch/06_UI_Architecture.md §3.2, §8.2, §8.3.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ._display import cell_value


def render_symbol_detail(symbols: List[Dict[str, Any]]) -> List[List[Any]]:
    """
    symbols 배열을 R_Dash 종목 상세용 행 리스트로 변환.

    Args:
        symbols: UI Contract §3.2 (symbol, price, qty, ...)

    Returns:
        행 리스트. 첫 행 헤더, 이후 종목별 행. 최대 29행 데이터(헤더 제외).
    """
    headers = ["symbol", "price", "qty", "exposure_value", "unrealized_pnl", "strategy_signal", "risk_approved", "final_qty"]
    rows = [headers]

    for sym in (symbols or [])[:29]:  # A12:D40 → 헤더 1 + 데이터 최대 29
        row = [
            cell_value(sym.get("symbol")),
            cell_value(sym.get("price")),
            cell_value(sym.get("qty")),
            cell_value(sym.get("exposure_value")),
            cell_value(sym.get("unrealized_pnl")),
            cell_value(sym.get("strategy_signal")),
            cell_value(sym.get("risk_approved")),
            cell_value(sym.get("final_qty")),
        ]
        rows.append(row)

    return rows
