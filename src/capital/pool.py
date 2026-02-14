"""
자본 풀 관리.

근거: docs/arch/sub/14_Capital_Flow_Architecture.md §2, §3.4
- 개별 풀 상태 관리
- 자본 이동 적용
- 긴급 잠금/해제
"""
from __future__ import annotations

from decimal import Decimal

from src.capital.contracts import (
    CapitalPoolContract,
    PoolId,
    PoolState,
)


def lock_pool(pool: CapitalPoolContract, reason: str) -> CapitalPoolContract:
    """풀 잠금. ACTIVE/PAUSED → LOCKED."""
    pool.pool_state = PoolState.LOCKED
    pool.lock_reason = reason
    return pool


def unlock_pool(pool: CapitalPoolContract) -> CapitalPoolContract:
    """풀 잠금 해제. LOCKED → ACTIVE."""
    pool.pool_state = PoolState.ACTIVE
    pool.lock_reason = ""
    return pool


def pause_pool(pool: CapitalPoolContract) -> CapitalPoolContract:
    """풀 일시 정지. ACTIVE → PAUSED."""
    pool.pool_state = PoolState.PAUSED
    return pool


def resume_pool(pool: CapitalPoolContract) -> CapitalPoolContract:
    """풀 재개. PAUSED → ACTIVE."""
    pool.pool_state = PoolState.ACTIVE
    return pool


def apply_transfer_out(
    pool: CapitalPoolContract, amount: Decimal
) -> bool:
    """풀에서 자본 출금. 가용 자본 부족 시 False."""
    if amount <= 0:
        return False
    if amount > pool.available_capital:
        return False
    if pool.is_locked:
        return False
    pool.total_capital -= amount
    return True


def apply_transfer_in(
    pool: CapitalPoolContract, amount: Decimal
) -> bool:
    """풀에 자본 입금."""
    if amount <= 0:
        return False
    if pool.is_locked:
        return False
    pool.total_capital += amount
    return True


def reset_accumulated_profit(
    pool: CapitalPoolContract, deduction: Decimal
) -> None:
    """프로모션 후 누적 수익 차감."""
    pool.accumulated_profit -= deduction
    if pool.accumulated_profit < 0:
        pool.accumulated_profit = Decimal("0")


def create_pool(
    pool_id: PoolId,
    total_capital: Decimal,
    allocation_pct: Decimal = Decimal("0"),
) -> CapitalPoolContract:
    """새 풀 생성 헬퍼."""
    return CapitalPoolContract(
        pool_id=pool_id,
        total_capital=total_capital,
        allocation_pct=allocation_pct,
        target_allocation_pct=allocation_pct,
    )
