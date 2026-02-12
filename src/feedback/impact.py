"""Market Impact Estimation (Kyle's Lambda 단순화)."""
from __future__ import annotations

import math
from decimal import Decimal


def estimate_market_impact_bps(
    order_qty: Decimal,
    avg_daily_volume: int,
    spread_bps: float,
) -> float:
    """시장 충격 추정 (basis points).

    impact = spread_bps * sqrt(participation_rate) * 10
    """
    if avg_daily_volume <= 0 or order_qty <= 0:
        return 0.0

    participation_rate = float(order_qty) / avg_daily_volume
    impact_multiplier = math.sqrt(participation_rate)
    return spread_bps * impact_multiplier * 10.0
