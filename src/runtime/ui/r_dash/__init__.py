"""
R_Dash 시각화 컴포넌트 — Data Contract 기반, Zero-Formula.

- Writer: UI Contract → R_Dash 시트 갱신
- Renderers: Contract 블록별 → 행 데이터(값만, 수식 없음)

docs/arch/06_UI_Architecture.md §8.1, §4.
"""

from ..r_dash_writer import (
    R_DASH_ACCOUNT,
    R_DASH_META,
    R_DASH_PERFORMANCE,
    R_DASH_PIPELINE,
    R_DASH_RISK,
    R_DASH_SYMBOLS,
    R_DashWriter,
)
from ..renderers import (
    render_account_summary,
    render_meta_block,
    render_performance,
    render_pipeline_status,
    render_risk_monitor,
    render_symbol_detail,
)

__all__ = [
    "R_DashWriter",
    "R_DASH_ACCOUNT",
    "R_DASH_SYMBOLS",
    "R_DASH_RISK",
    "R_DASH_PERFORMANCE",
    "R_DASH_PIPELINE",
    "R_DASH_META",
    "render_account_summary",
    "render_symbol_detail",
    "render_risk_monitor",
    "render_performance",
    "render_pipeline_status",
    "render_meta_block",
]
