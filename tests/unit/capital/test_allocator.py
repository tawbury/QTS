"""CapitalAllocator 테스트."""
from decimal import Decimal

import pytest

from src.capital.allocator import (
    calculate_target_allocation,
    calculate_target_amounts,
    check_drift,
)
from src.capital.contracts import PoolId
from src.state.contracts import OperatingState


class TestCalculateTargetAllocation:
    """목표 배분 비율 계산."""

    def test_aggressive_allocation(self):
        alloc = calculate_target_allocation(
            OperatingState.AGGRESSIVE, Decimal("30000000")
        )
        assert sum(alloc.values()) == Decimal("1.0000")
        # AGGRESSIVE: scalp 높고 portfolio 낮음
        assert alloc[PoolId.SCALP] > alloc[PoolId.PORTFOLIO]

    def test_defensive_allocation(self):
        alloc = calculate_target_allocation(
            OperatingState.DEFENSIVE, Decimal("30000000")
        )
        assert sum(alloc.values()) == Decimal("1.0000")
        # DEFENSIVE: portfolio 높고 scalp 낮음
        assert alloc[PoolId.PORTFOLIO] > alloc[PoolId.SCALP]

    def test_balanced_allocation(self):
        alloc = calculate_target_allocation(
            OperatingState.BALANCED, Decimal("30000000")
        )
        assert sum(alloc.values()) == Decimal("1.0000")
        # BALANCED: 비교적 균등
        for pid in PoolId:
            assert alloc[pid] > Decimal("0.10")

    def test_all_states_sum_to_one(self):
        for state in OperatingState:
            alloc = calculate_target_allocation(state, Decimal("10000000"))
            assert sum(alloc.values()) == Decimal("1.0000")

    def test_all_pools_present(self):
        alloc = calculate_target_allocation(
            OperatingState.BALANCED, Decimal("10000000")
        )
        for pid in PoolId:
            assert pid in alloc
            assert alloc[pid] > 0

    def test_respects_min_constraints(self):
        """모든 상태에서 최소 비율 준수."""
        for state in OperatingState:
            alloc = calculate_target_allocation(state, Decimal("100000000"))
            assert alloc[PoolId.SCALP] >= Decimal("0.05")
            assert alloc[PoolId.SWING] >= Decimal("0.10")
            assert alloc[PoolId.PORTFOLIO] >= Decimal("0.05")


class TestCalculateTargetAmounts:
    """배분 금액 계산."""

    def test_simple(self):
        alloc = {
            PoolId.SCALP: Decimal("0.40"),
            PoolId.SWING: Decimal("0.35"),
            PoolId.PORTFOLIO: Decimal("0.25"),
        }
        amounts = calculate_target_amounts(alloc, Decimal("10000000"))
        assert amounts[PoolId.SCALP] == Decimal("4000000")
        assert amounts[PoolId.SWING] == Decimal("3500000")
        assert amounts[PoolId.PORTFOLIO] == Decimal("2500000")

    def test_rounding(self):
        alloc = {
            PoolId.SCALP: Decimal("0.3333"),
            PoolId.SWING: Decimal("0.3334"),
            PoolId.PORTFOLIO: Decimal("0.3333"),
        }
        amounts = calculate_target_amounts(alloc, Decimal("10000000"))
        # 반올림 결과
        assert amounts[PoolId.SCALP] == Decimal("3333000")


class TestCheckDrift:
    """드리프트 계산."""

    def test_no_drift(self):
        current = {
            PoolId.SCALP: Decimal("0.40"),
            PoolId.SWING: Decimal("0.35"),
            PoolId.PORTFOLIO: Decimal("0.25"),
        }
        target = {
            PoolId.SCALP: Decimal("0.40"),
            PoolId.SWING: Decimal("0.35"),
            PoolId.PORTFOLIO: Decimal("0.25"),
        }
        drifts = check_drift(current, target)
        assert len(drifts) == 0

    def test_with_drift(self):
        current = {
            PoolId.SCALP: Decimal("0.55"),
            PoolId.SWING: Decimal("0.35"),
            PoolId.PORTFOLIO: Decimal("0.10"),
        }
        target = {
            PoolId.SCALP: Decimal("0.40"),
            PoolId.SWING: Decimal("0.35"),
            PoolId.PORTFOLIO: Decimal("0.25"),
        }
        drifts = check_drift(current, target)
        assert PoolId.SCALP in drifts
        assert PoolId.PORTFOLIO in drifts
        assert PoolId.SWING not in drifts

    def test_custom_threshold(self):
        current = {
            PoolId.SCALP: Decimal("0.42"),
            PoolId.SWING: Decimal("0.35"),
            PoolId.PORTFOLIO: Decimal("0.23"),
        }
        target = {
            PoolId.SCALP: Decimal("0.40"),
            PoolId.SWING: Decimal("0.35"),
            PoolId.PORTFOLIO: Decimal("0.25"),
        }
        # 기본 threshold 10%에서는 드리프트 없음
        assert len(check_drift(current, target)) == 0
        # threshold 1%로 낮추면 감지
        drifts = check_drift(current, target, Decimal("0.01"))
        assert len(drifts) == 2
