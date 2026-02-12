"""
자본 배분기.

근거: docs/arch/sub/14_Capital_Flow_Architecture.md §3
- OperatingState 기반 목표 배분 비율 계산
- 제약 조건 (min_pct, max_pct, min_amount) 적용
- 합계 100% 정규화
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from src.capital.contracts import (
    POOL_CONSTRAINTS,
    AllocationConstraints,
    PoolId,
)
from src.state.contracts import STATE_PROPERTIES, OperatingState


def _mid(range_: tuple[float, float]) -> Decimal:
    """범위의 중간값."""
    return Decimal(str((range_[0] + range_[1]) / 2))


def calculate_target_allocation(
    operating_state: OperatingState,
    total_equity: Decimal,
) -> dict[PoolId, Decimal]:
    """
    OperatingState 기반 목표 배분 비율 계산.

    STATE_PROPERTIES의 allocation_range 중간값을 사용하고
    합계가 1.0이 되도록 정규화한다.
    """
    props = STATE_PROPERTIES[operating_state]

    raw: dict[PoolId, Decimal] = {
        PoolId.SCALP: _mid(props.scalp_allocation_range),
        PoolId.SWING: _mid(props.swing_allocation_range),
        PoolId.PORTFOLIO: _mid(props.portfolio_allocation_range),
    }

    # 제약 조건 적용
    for pool_id, constraints in POOL_CONSTRAINTS.items():
        pct = raw[pool_id]
        pct = max(pct, constraints.min_pct)
        pct = min(pct, constraints.max_pct)
        raw[pool_id] = pct

    # 정규화 (합계 = 1.0)
    total = sum(raw.values())
    if total == 0:
        equal = Decimal("1") / Decimal("3")
        return {pid: equal for pid in PoolId}

    result: dict[PoolId, Decimal] = {}
    for pool_id in PoolId:
        normalized = (raw[pool_id] / total).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        result[pool_id] = normalized

    # 반올림 오차 보정: SCALP에 나머지 할당
    diff = Decimal("1.0000") - sum(result.values())
    result[PoolId.SCALP] += diff

    return result


def calculate_target_amounts(
    allocation: dict[PoolId, Decimal],
    total_equity: Decimal,
) -> dict[PoolId, Decimal]:
    """배분 비율 → 금액 변환."""
    amounts: dict[PoolId, Decimal] = {}
    for pool_id, pct in allocation.items():
        amount = (total_equity * pct).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        amounts[pool_id] = amount
    return amounts


def check_drift(
    current_pcts: dict[PoolId, Decimal],
    target_pcts: dict[PoolId, Decimal],
    threshold: Decimal = Decimal("0.10"),
) -> dict[PoolId, Decimal]:
    """
    드리프트 계산. 임계값 초과 풀 반환.

    Returns: {PoolId: drift_amount} (threshold 초과분만)
    """
    drifts: dict[PoolId, Decimal] = {}
    for pool_id in PoolId:
        current = current_pcts.get(pool_id, Decimal("0"))
        target = target_pcts.get(pool_id, Decimal("0"))
        drift = abs(current - target)
        if drift > threshold:
            drifts[pool_id] = drift
    return drifts
