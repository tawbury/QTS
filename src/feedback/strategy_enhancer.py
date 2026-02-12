"""Strategy Enhancement — 피드백 기반 전략 파라미터 보정."""
from __future__ import annotations

import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def calculate_adjusted_entry_price(
    signal_price: Decimal,
    historical_slippage_bps: float,
    side: str,
) -> Decimal:
    """슬리피지 보정 진입가 계산.

    BUY: 슬리피지만큼 높은 가격 예상 → 제한가를 올림.
    SELL: 슬리피지만큼 낮은 가격 예상 → 제한가를 내림.
    """
    if signal_price <= 0:
        return signal_price

    slippage_factor = Decimal(str(historical_slippage_bps / 10000))

    if side.upper() == "BUY":
        return signal_price * (1 + slippage_factor)
    else:
        return signal_price * (1 - slippage_factor)


def adjust_qty_for_market_impact(
    target_qty: Decimal,
    estimated_impact_bps: float,
    max_acceptable_impact_bps: float = 20.0,
) -> Decimal:
    """시장 충격 기반 수량 조정.

    예상 충격이 허용치를 초과하면 수량을 비례 축소한다.
    """
    if target_qty <= 0:
        return target_qty

    if estimated_impact_bps <= max_acceptable_impact_bps:
        return target_qty

    reduction_ratio = max_acceptable_impact_bps / estimated_impact_bps
    adjusted = target_qty * Decimal(str(reduction_ratio))

    logger.warning(
        "Qty reduced due to market impact: %s → %s (impact=%.1f bps, max=%.1f bps)",
        target_qty, adjusted, estimated_impact_bps, max_acceptable_impact_bps,
    )
    return adjusted


def adjust_confidence(
    raw_confidence: float,
    quality_score: float,
) -> float:
    """실행 품질 기반 신뢰도 보정."""
    return max(0.0, min(1.0, raw_confidence * quality_score))
