"""슬리피지 계산."""
from __future__ import annotations

from decimal import Decimal


def calculate_slippage_bps(
    decision_price: Decimal,
    avg_fill_price: Decimal,
) -> float:
    """슬리피지 계산 (basis points).

    양수 = 불리(매수 시 높은 체결가), 음수 = 유리.
    """
    if decision_price == 0:
        return 0.0
    slippage = (avg_fill_price - decision_price) / decision_price
    return float(slippage * 10000)
