"""
Zero-Formula UI 기본 계약.

UI는 Contract만 입력받아 **값만** 출력한다. 시트에 수식을 넣지 않는다.
docs/arch/06_UI_Architecture.md §4 Zero Formula UI Architecture.
"""

from __future__ import annotations

from typing import Any, Dict, List, Protocol, runtime_checkable


@runtime_checkable
class BlockRenderer(Protocol):
    """
    Zero-Formula 블록 렌더러 프로토콜.

    - 입력: UI Contract 블록(dict)만 사용. Raw/Calc 직접 접근 금지.
    - 출력: 셀에 쓸 값의 2차원 리스트(행·열). 수식 없음.
    """

    def __call__(self, contract_block: Dict[str, Any]) -> List[List[Any]]:
        """
        Contract 블록을 R_Dash용 행 데이터로 변환.

        Args:
            contract_block: UI Contract의 한 블록(account, symbols, risk 등).

        Returns:
            셀 값의 행 리스트. 수식/참조 없이 값만.
        """
        ...
