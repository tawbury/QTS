"""
R_Dash 셀 표시 규칙 (06_UI_Architecture §7.2).

None → "-", NaN → "ERR". 시트 내부 계산식 사용 금지.
"""

from __future__ import annotations

from typing import Any


def cell_value(value: Any) -> str:
    """Contract 값을 R_Dash 셀에 넣을 문자열로 변환."""
    if value is None:
        return "-"
    if isinstance(value, float) and value != value:  # NaN
        return "ERR"
    return str(value)
