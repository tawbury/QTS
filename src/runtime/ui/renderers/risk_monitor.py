"""
Risk Monitor Rendering Unit.

UI Contract risk 블록 → R_Dash 리스크 모니터 영역(F1:H20)용 행 데이터.
docs/arch/06_UI_Architecture.md §3.4, §8.4.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ._display import cell_value


def render_risk_monitor(risk: Dict[str, Any] | None) -> List[List[Any]]:
    """
    risk 블록을 R_Dash 리스크 모니터용 행 리스트로 변환.

    Args:
        risk: UI Contract §3.4 (exposure_limit_pct, risk_warnings, ...) 또는 None

    Returns:
        행 리스트. 헤더 + 데이터.
    """
    headers = ["exposure_limit_pct", "current_exposure_pct", "risk_warnings", "rejected_signals"]
    if not risk:
        return [headers, ["-", "-", "-", "-"]]

    warnings = risk.get("risk_warnings")
    w_str = "; ".join(str(x) for x in warnings) if isinstance(warnings, list) else cell_value(warnings)
    rejected = risk.get("rejected_signals")
    r_str = "; ".join(str(x) for x in rejected) if isinstance(rejected, list) else cell_value(rejected)

    row = [
        cell_value(risk.get("exposure_limit_pct")),
        cell_value(risk.get("current_exposure_pct")),
        w_str,
        r_str,
    ]
    return [headers, row]
