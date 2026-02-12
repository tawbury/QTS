"""CapitalPool 관리 테스트."""
from decimal import Decimal

import pytest

from src.capital.contracts import CapitalPoolContract, PoolId, PoolState
from src.capital.pool import (
    apply_transfer_in,
    apply_transfer_out,
    create_pool,
    lock_pool,
    pause_pool,
    reset_accumulated_profit,
    resume_pool,
    unlock_pool,
)


@pytest.fixture
def scalp_pool() -> CapitalPoolContract:
    return CapitalPoolContract(
        pool_id=PoolId.SCALP,
        total_capital=Decimal("10000000"),
        invested_capital=Decimal("3000000"),
    )


class TestPoolStateTransitions:
    """풀 상태 전환."""

    def test_lock_pool(self, scalp_pool: CapitalPoolContract):
        lock_pool(scalp_pool, "FS082")
        assert scalp_pool.is_locked
        assert scalp_pool.lock_reason == "FS082"

    def test_unlock_pool(self, scalp_pool: CapitalPoolContract):
        lock_pool(scalp_pool, "test")
        unlock_pool(scalp_pool)
        assert scalp_pool.is_active
        assert scalp_pool.lock_reason == ""

    def test_pause_pool(self, scalp_pool: CapitalPoolContract):
        pause_pool(scalp_pool)
        assert scalp_pool.pool_state == PoolState.PAUSED

    def test_resume_pool(self, scalp_pool: CapitalPoolContract):
        pause_pool(scalp_pool)
        resume_pool(scalp_pool)
        assert scalp_pool.is_active


class TestTransferOut:
    """자본 출금."""

    def test_normal_transfer(self, scalp_pool: CapitalPoolContract):
        ok = apply_transfer_out(scalp_pool, Decimal("1000000"))
        assert ok
        assert scalp_pool.total_capital == Decimal("9000000")

    def test_exceeds_available(self, scalp_pool: CapitalPoolContract):
        # available = 10M - 3M = 7M
        ok = apply_transfer_out(scalp_pool, Decimal("8000000"))
        assert not ok
        assert scalp_pool.total_capital == Decimal("10000000")

    def test_exact_available(self, scalp_pool: CapitalPoolContract):
        ok = apply_transfer_out(scalp_pool, Decimal("7000000"))
        assert ok
        assert scalp_pool.total_capital == Decimal("3000000")

    def test_zero_amount(self, scalp_pool: CapitalPoolContract):
        ok = apply_transfer_out(scalp_pool, Decimal("0"))
        assert not ok

    def test_negative_amount(self, scalp_pool: CapitalPoolContract):
        ok = apply_transfer_out(scalp_pool, Decimal("-100"))
        assert not ok

    def test_locked_pool(self, scalp_pool: CapitalPoolContract):
        lock_pool(scalp_pool, "test")
        ok = apply_transfer_out(scalp_pool, Decimal("1000000"))
        assert not ok


class TestTransferIn:
    """자본 입금."""

    def test_normal_transfer(self, scalp_pool: CapitalPoolContract):
        ok = apply_transfer_in(scalp_pool, Decimal("500000"))
        assert ok
        assert scalp_pool.total_capital == Decimal("10500000")

    def test_zero_amount(self, scalp_pool: CapitalPoolContract):
        ok = apply_transfer_in(scalp_pool, Decimal("0"))
        assert not ok

    def test_locked_pool(self, scalp_pool: CapitalPoolContract):
        lock_pool(scalp_pool, "test")
        ok = apply_transfer_in(scalp_pool, Decimal("500000"))
        assert not ok


class TestResetProfit:
    """누적 수익 리셋."""

    def test_normal_deduction(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("10000000"),
            accumulated_profit=Decimal("1500000"),
        )
        reset_accumulated_profit(pool, Decimal("500000"))
        assert pool.accumulated_profit == Decimal("1000000")

    def test_over_deduction_floors_to_zero(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("10000000"),
            accumulated_profit=Decimal("100000"),
        )
        reset_accumulated_profit(pool, Decimal("500000"))
        assert pool.accumulated_profit == Decimal("0")


class TestCreatePool:
    """풀 생성 헬퍼."""

    def test_create(self):
        pool = create_pool(PoolId.SWING, Decimal("5000000"), Decimal("0.35"))
        assert pool.pool_id == PoolId.SWING
        assert pool.total_capital == Decimal("5000000")
        assert pool.allocation_pct == Decimal("0.35")
        assert pool.target_allocation_pct == Decimal("0.35")
        assert pool.is_active
