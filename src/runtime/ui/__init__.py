"""
UI Layer — Contract-driven rendering (Zero-Formula).

UI는 Raw/Calc를 직접 읽지 않고 UI Contract만으로 R_Dash를 렌더링한다.
Contract 생성은 UIContractBuilder, 갱신은 R_DashWriter에서만 수행한다.

참조: docs/arch/UI_Contract_Schema.md, docs/arch/06_UI_Architecture.md
"""

from .contract_schema import UIContractVersion, get_expected_contract_version
from .contract_builder import UIContractBuilder
from .r_dash_writer import R_DashWriter
from .zero_formula_base import BlockRenderer

__all__ = [
    "UIContractVersion",
    "get_expected_contract_version",
    "UIContractBuilder",
    "R_DashWriter",
    "BlockRenderer",
]
