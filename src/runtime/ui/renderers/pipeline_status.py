"""
Pipeline Status Rendering Unit.

UI Contract pipeline_status 블록 → R_Dash Pipeline Status 영역(F25:H33)용 행 데이터.
docs/arch/06_UI_Architecture.md §3.5, §8.7.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ._display import cell_value


def render_pipeline_status(pipeline_status: Dict[str, Any]) -> List[List[Any]]:
    """
    pipeline_status 블록을 R_Dash 파이프라인 상태용 행 리스트로 변환.

    Args:
        pipeline_status: UI Contract §3.5 (pipeline_state, last_cycle_duration, ...)

    Returns:
        행 리스트. 헤더 + 데이터.
    """
    headers = ["pipeline_state", "last_cycle_duration", "last_error_code", "cycle_timestamp"]
    if not pipeline_status:
        return [headers, ["-", "-", "-", "-"]]

    row = [
        cell_value(pipeline_status.get("pipeline_state")),
        cell_value(pipeline_status.get("last_cycle_duration")),
        cell_value(pipeline_status.get("last_error_code")),
        cell_value(pipeline_status.get("cycle_timestamp")),
    ]
    return [headers, row]
