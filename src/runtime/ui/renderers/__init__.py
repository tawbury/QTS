"""
UI Rendering Units — Contract → R_Dash 셀 데이터.

각 렌더러는 UI Contract 블록만 받아 해당 영역용 행 데이터를 반환한다.
Raw/Calc를 직접 읽지 않는다. docs/arch/06_UI_Architecture.md §2.4, §8.
"""

from .account_summary import render_account_summary
from .symbol_detail import render_symbol_detail
from .risk_monitor import render_risk_monitor
from .performance import render_performance
from .pipeline_status import render_pipeline_status
from .meta_block import render_meta_block

__all__ = [
    "render_account_summary",
    "render_symbol_detail",
    "render_risk_monitor",
    "render_performance",
    "render_pipeline_status",
    "render_meta_block",
]
