"""
Performance Rendering Unit.

UI Contract performance 블록 → R_Dash Performance 요약 영역(J1:M20)용 행 데이터.
docs/arch/06_UI_Architecture.md §3.3, §8.6.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ._display import cell_value


def render_performance(performance: Dict[str, Any] | None) -> List[List[Any]]:
    """
    performance 블록을 R_Dash 성과 요약용 행 리스트로 변환.

    Args:
        performance: UI Contract §3.3 (mdd, cagr, win_rate, ...) 또는 None

    Returns:
        행 리스트. 헤더 + 데이터.
    """
    headers = ["daily_pnl_curve", "mdd", "cagr", "win_rate", "strategy_performance_table"]
    if not performance:
        return [headers, ["-", "-", "-", "-", "-"]]

    curve = performance.get("daily_pnl_curve")
    curve_str = str(curve)[:200] if isinstance(curve, list) else cell_value(curve)
    table = performance.get("strategy_performance_table")
    table_str = str(table)[:200] if table is not None else "-"

    row = [
        curve_str,
        cell_value(performance.get("mdd")),
        cell_value(performance.get("cagr")),
        cell_value(performance.get("win_rate")),
        table_str,
    ]
    return [headers, row]
