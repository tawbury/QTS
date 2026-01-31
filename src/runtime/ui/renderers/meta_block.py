"""
Meta Block Rendering Unit.

UI Contract meta 블록 → R_Dash Meta 영역(J25:M33)용 행 데이터.
docs/arch/06_UI_Architecture.md §3.6, §8.1.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ._display import cell_value


def render_meta_block(meta: Dict[str, Any]) -> List[List[Any]]:
    """
    meta 블록을 R_Dash 메타 영역용 행 리스트로 변환.

    Args:
        meta: UI Contract §3.6 (contract_version, timestamp, ...)

    Returns:
        행 리스트. 헤더 + 데이터.
    """
    headers = ["contract_version", "schema_version", "qts_version", "broker_connected", "timestamp"]
    if not meta:
        return [headers, ["-", "-", "-", "-", "-"]]

    row = [
        cell_value(meta.get("contract_version")),
        cell_value(meta.get("schema_version")),
        cell_value(meta.get("qts_version")),
        cell_value(meta.get("broker_connected")),
        cell_value(meta.get("timestamp")),
    ]
    return [headers, row]
