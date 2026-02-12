"""
Capital Guardrails & Fail-Safe.

근거: docs/arch/sub/14_Capital_Flow_Architecture.md §7
- GR050-GR055: Capital Guardrails
- FS080-FS085: Capital Fail-Safe
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from src.capital.contracts import (
    POOL_CONSTRAINTS,
    CapitalAlert,
    CapitalPoolContract,
    PoolId,
    PoolState,
)


def check_allocation_sum(
    pools: dict[PoolId, CapitalPoolContract],
) -> Optional[CapitalAlert]:
    """GR050: 풀 배분 합계 ≠ 100% 검증."""
    total_capital = sum(p.total_capital for p in pools.values())
    if total_capital == 0:
        return None
    pct_sum = sum(p.allocation_pct for p in pools.values())
    if abs(pct_sum - Decimal("1.0")) > Decimal("0.01"):
        return CapitalAlert(
            code="GR050",
            pool_id=None,
            message=f"풀 배분 합계 불일치: {pct_sum} (expected 1.0)",
            severity="WARNING",
        )
    return None


def check_min_allocation(
    pools: dict[PoolId, CapitalPoolContract],
    total_equity: Decimal,
) -> list[CapitalAlert]:
    """GR051: 풀 최소 비율 미달 검증."""
    alerts: list[CapitalAlert] = []
    if total_equity <= 0:
        return alerts
    for pool_id, pool in pools.items():
        constraints = POOL_CONSTRAINTS.get(pool_id)
        if constraints is None:
            continue
        actual_pct = pool.total_capital / total_equity
        if actual_pct < constraints.min_pct:
            alerts.append(
                CapitalAlert(
                    code="GR051",
                    pool_id=pool_id,
                    message=f"{pool_id.value} 배분 {actual_pct:.2%} < 최소 {constraints.min_pct:.2%}",
                    severity="WARNING",
                )
            )
    return alerts


def check_max_allocation(
    pools: dict[PoolId, CapitalPoolContract],
    total_equity: Decimal,
) -> list[CapitalAlert]:
    """GR052: 풀 최대 비율 초과 검증."""
    alerts: list[CapitalAlert] = []
    if total_equity <= 0:
        return alerts
    for pool_id, pool in pools.items():
        constraints = POOL_CONSTRAINTS.get(pool_id)
        if constraints is None:
            continue
        actual_pct = pool.total_capital / total_equity
        if actual_pct > constraints.max_pct:
            alerts.append(
                CapitalAlert(
                    code="GR052",
                    pool_id=pool_id,
                    message=f"{pool_id.value} 배분 {actual_pct:.2%} > 최대 {constraints.max_pct:.2%}",
                    severity="WARNING",
                )
            )
    return alerts


def check_transfer_exceeds_available(
    pool: CapitalPoolContract,
    transfer_amount: Decimal,
) -> Optional[CapitalAlert]:
    """GR053: 이전액 > 가용 자본 검증."""
    if transfer_amount > pool.available_capital:
        return CapitalAlert(
            code="GR053",
            pool_id=pool.pool_id,
            message=f"이전액 {transfer_amount} > 가용 {pool.available_capital}",
            severity="WARNING",
        )
    return None


def check_drift(
    pools: dict[PoolId, CapitalPoolContract],
    total_equity: Decimal,
    threshold: Decimal = Decimal("0.10"),
) -> list[CapitalAlert]:
    """GR055: 드리프트 > threshold 검증."""
    alerts: list[CapitalAlert] = []
    if total_equity <= 0:
        return alerts
    for pool_id, pool in pools.items():
        actual_pct = pool.total_capital / total_equity
        drift = abs(actual_pct - pool.target_allocation_pct)
        if drift > threshold:
            alerts.append(
                CapitalAlert(
                    code="GR055",
                    pool_id=pool_id,
                    message=f"{pool_id.value} 드리프트 {drift:.2%} > {threshold:.2%}",
                    severity="WARNING",
                )
            )
    return alerts


# --- Fail-Safe ---


def check_total_capital_zero(
    total_equity: Decimal,
) -> Optional[CapitalAlert]:
    """FS080: 총 자본 <= 0."""
    if total_equity <= 0:
        return CapitalAlert(
            code="FS080",
            pool_id=None,
            message=f"총 자본 {total_equity} <= 0. LOCKDOWN 필요.",
            severity="CRITICAL",
        )
    return None


def check_negative_pool_capital(
    pools: dict[PoolId, CapitalPoolContract],
) -> list[CapitalAlert]:
    """FS081: 풀 자본 음수."""
    alerts: list[CapitalAlert] = []
    for pool_id, pool in pools.items():
        if pool.total_capital < 0:
            alerts.append(
                CapitalAlert(
                    code="FS081",
                    pool_id=pool_id,
                    message=f"{pool_id.value} 자본 음수: {pool.total_capital}",
                    severity="CRITICAL",
                )
            )
    return alerts


def check_pool_mdd_critical(
    pool_id: PoolId,
    mdd: float,
    threshold: float = 0.20,
) -> Optional[CapitalAlert]:
    """FS082: 풀 MDD > threshold."""
    if mdd > threshold:
        return CapitalAlert(
            code="FS082",
            pool_id=pool_id,
            message=f"{pool_id.value} MDD {mdd:.2%} > {threshold:.2%}. 풀 잠금 필요.",
            severity="CRITICAL",
        )
    return None


def run_all_guardrails(
    pools: dict[PoolId, CapitalPoolContract],
    total_equity: Decimal,
) -> list[CapitalAlert]:
    """모든 가드레일 실행."""
    alerts: list[CapitalAlert] = []

    # FS080
    fs080 = check_total_capital_zero(total_equity)
    if fs080:
        alerts.append(fs080)

    # FS081
    alerts.extend(check_negative_pool_capital(pools))

    # GR050
    gr050 = check_allocation_sum(pools)
    if gr050:
        alerts.append(gr050)

    # GR051
    alerts.extend(check_min_allocation(pools, total_equity))

    # GR052
    alerts.extend(check_max_allocation(pools, total_equity))

    # GR055
    alerts.extend(check_drift(pools, total_equity))

    return alerts
