"""
프로모션/디모션 엔진.

근거: docs/arch/sub/14_Capital_Flow_Architecture.md §4
- Scalp→Swing 프로모션 (주간)
- Swing→Portfolio 프로모션 (분기)
- Portfolio→Swing 디모션 (MDD 기반)
- Swing→Scalp 디모션 (MDD/연패 기반)
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.capital.contracts import (
    DEMOTION_RULES,
    SCALP_TO_SWING_CRITERIA,
    SWING_TO_PORTFOLIO_CRITERIA,
    CapitalPoolContract,
    PerformanceMetrics,
    PromotionCriteria,
)


def _meets_promotion_criteria(
    pool: CapitalPoolContract,
    metrics: PerformanceMetrics,
    criteria: PromotionCriteria,
) -> bool:
    """프로모션 조건 충족 여부 확인."""
    if pool.accumulated_profit < criteria.min_accumulated_profit:
        return False
    if metrics.sharpe_ratio < criteria.min_sharpe_ratio:
        return False
    if criteria.min_win_rate_30d > 0 and metrics.win_rate_30d < criteria.min_win_rate_30d:
        return False
    if criteria.min_trades_30d > 0 and metrics.trades_30d < criteria.min_trades_30d:
        return False
    if criteria.max_mdd < 1.0 and metrics.mdd_30d > criteria.max_mdd:
        return False
    if not pool.is_active:
        return False
    return True


def _calculate_transfer_amount(
    accumulated_profit: Decimal,
    criteria: PromotionCriteria,
) -> Decimal:
    """이전 금액 계산: (초과 수익) × transfer_ratio."""
    excess = accumulated_profit - criteria.min_accumulated_profit
    if excess <= 0:
        return Decimal("0")
    amount = excess * criteria.transfer_ratio
    amount = max(amount, criteria.min_transfer_amount)
    amount = min(amount, criteria.max_transfer_amount)
    return amount


def check_scalp_to_swing(
    pool: CapitalPoolContract,
    metrics: PerformanceMetrics,
    criteria: PromotionCriteria = SCALP_TO_SWING_CRITERIA,
) -> Optional[Decimal]:
    """
    Scalp→Swing 프로모션 확인.

    Returns: 이전 금액 (None이면 조건 미충족)
    """
    if not _meets_promotion_criteria(pool, metrics, criteria):
        return None
    amount = _calculate_transfer_amount(pool.accumulated_profit, criteria)
    if amount <= 0:
        return None
    # 가용 자본 초과 방지
    if amount > pool.available_capital:
        amount = pool.available_capital
    return amount


def check_swing_to_portfolio(
    pool: CapitalPoolContract,
    metrics: PerformanceMetrics,
    criteria: PromotionCriteria = SWING_TO_PORTFOLIO_CRITERIA,
) -> Optional[Decimal]:
    """
    Swing→Portfolio 프로모션 확인.

    Returns: 이전 금액 (None이면 조건 미충족)
    """
    if not _meets_promotion_criteria(pool, metrics, criteria):
        return None
    amount = _calculate_transfer_amount(pool.accumulated_profit, criteria)
    if amount <= 0:
        return None
    if amount > pool.available_capital:
        amount = pool.available_capital
    return amount


def check_portfolio_demotion(
    pool: CapitalPoolContract,
    metrics: PerformanceMetrics,
) -> Optional[Decimal]:
    """
    Portfolio→Swing 디모션 확인.

    Returns: 이전 금액 (None이면 조건 미충족)
    """
    rule = DEMOTION_RULES["portfolio_to_swing"]
    if not pool.is_active:
        return None
    if metrics.mdd_30d <= rule.trigger_mdd:
        return None
    amount = pool.total_capital * rule.transfer_ratio
    if amount > pool.available_capital:
        amount = pool.available_capital
    if amount <= 0:
        return None
    return amount


def check_swing_demotion(
    pool: CapitalPoolContract,
    metrics: PerformanceMetrics,
) -> Optional[Decimal]:
    """
    Swing→Scalp 디모션 확인.

    MDD 초과 또는 연패 기준 충족 시 디모션.
    Returns: 이전 금액 (None이면 조건 미충족)
    """
    rule = DEMOTION_RULES["swing_to_scalp"]
    if not pool.is_active:
        return None

    mdd_triggered = metrics.mdd_30d > rule.trigger_mdd
    loss_triggered = (
        rule.trigger_consecutive_losses > 0
        and metrics.consecutive_losses >= rule.trigger_consecutive_losses
    )

    if not mdd_triggered and not loss_triggered:
        return None

    amount = pool.total_capital * rule.transfer_ratio
    if amount > pool.available_capital:
        amount = pool.available_capital
    if amount <= 0:
        return None
    return amount
