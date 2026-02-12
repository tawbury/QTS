"""자본 흐름 데이터 계약 테스트."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.capital.contracts import (
    DEMOTION_RULES,
    POOL_CONSTRAINTS,
    SCALP_TO_SWING_CRITERIA,
    SWING_TO_PORTFOLIO_CRITERIA,
    AllocationConstraints,
    CapitalAlert,
    CapitalPoolContract,
    CapitalTransfer,
    DemotionRule,
    PerformanceMetrics,
    PoolId,
    PoolState,
    PromotionCriteria,
)


class TestPoolId:
    """PoolId enum."""

    def test_values(self):
        assert PoolId.SCALP.value == "SCALP"
        assert PoolId.SWING.value == "SWING"
        assert PoolId.PORTFOLIO.value == "PORTFOLIO"

    def test_count(self):
        assert len(PoolId) == 3


class TestPoolState:
    """PoolState enum."""

    def test_values(self):
        assert PoolState.ACTIVE.value == "ACTIVE"
        assert PoolState.PAUSED.value == "PAUSED"
        assert PoolState.LOCKED.value == "LOCKED"


class TestCapitalPoolContract:
    """CapitalPoolContract."""

    def test_available_capital(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("10000000"),
            invested_capital=Decimal("3000000"),
            reserved_capital=Decimal("500000"),
        )
        assert pool.available_capital == Decimal("6500000")

    def test_available_capital_zero_reserve(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SWING,
            total_capital=Decimal("5000000"),
            invested_capital=Decimal("2000000"),
        )
        assert pool.available_capital == Decimal("3000000")

    def test_is_active(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("1000000"),
        )
        assert pool.is_active
        assert not pool.is_locked

    def test_is_locked(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("1000000"),
            pool_state=PoolState.LOCKED,
        )
        assert pool.is_locked
        assert not pool.is_active

    def test_is_valid_normal(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("10000000"),
            invested_capital=Decimal("3000000"),
        )
        assert pool.is_valid()

    def test_is_valid_negative_total(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("-1000"),
        )
        assert not pool.is_valid()

    def test_is_valid_over_invested(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("10000000"),
            invested_capital=Decimal("15000000"),
        )
        assert not pool.is_valid()

    def test_is_valid_negative_invested(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("10000000"),
            invested_capital=Decimal("-1"),
        )
        assert not pool.is_valid()

    def test_defaults(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.PORTFOLIO,
            total_capital=Decimal("5000000"),
        )
        assert pool.realized_pnl == Decimal("0")
        assert pool.accumulated_profit == Decimal("0")
        assert pool.pool_state == PoolState.ACTIVE
        assert pool.last_promotion_at is None


class TestPoolConstraints:
    """풀별 제약 조건."""

    def test_all_pools_have_constraints(self):
        for pid in PoolId:
            assert pid in POOL_CONSTRAINTS

    def test_scalp_constraints(self):
        c = POOL_CONSTRAINTS[PoolId.SCALP]
        assert c.min_pct == Decimal("0.05")
        assert c.max_pct == Decimal("0.80")
        assert c.min_amount == Decimal("1000000")

    def test_swing_constraints(self):
        c = POOL_CONSTRAINTS[PoolId.SWING]
        assert c.min_pct == Decimal("0.10")
        assert c.max_pct == Decimal("0.50")

    def test_portfolio_constraints(self):
        c = POOL_CONSTRAINTS[PoolId.PORTFOLIO]
        assert c.min_pct == Decimal("0.05")
        assert c.max_pct == Decimal("0.80")
        assert c.min_amount == Decimal("3000000")


class TestPromotionCriteria:
    """프로모션 기준."""

    def test_scalp_to_swing(self):
        c = SCALP_TO_SWING_CRITERIA
        assert c.min_accumulated_profit == Decimal("1000000")
        assert c.min_sharpe_ratio == 1.5
        assert c.min_win_rate_30d == 0.55
        assert c.min_trades_30d == 50
        assert c.max_mdd == 0.10
        assert c.transfer_ratio == Decimal("0.50")

    def test_swing_to_portfolio(self):
        c = SWING_TO_PORTFOLIO_CRITERIA
        assert c.min_accumulated_profit == Decimal("5000000")
        assert c.min_sharpe_ratio == 1.2
        assert c.transfer_ratio == Decimal("0.30")


class TestDemotionRules:
    """디모션 규칙."""

    def test_portfolio_to_swing(self):
        r = DEMOTION_RULES["portfolio_to_swing"]
        assert r.trigger_mdd == 0.10
        assert r.transfer_ratio == Decimal("0.20")

    def test_swing_to_scalp(self):
        r = DEMOTION_RULES["swing_to_scalp"]
        assert r.trigger_mdd == 0.15
        assert r.transfer_ratio == Decimal("0.30")
        assert r.trigger_consecutive_losses == 5


class TestPerformanceMetrics:
    """PerformanceMetrics."""

    def test_defaults(self):
        m = PerformanceMetrics()
        assert m.sharpe_ratio == 0.0
        assert m.win_rate_30d == 0.0
        assert m.consecutive_losses == 0

    def test_custom(self):
        m = PerformanceMetrics(sharpe_ratio=1.8, win_rate_30d=0.58)
        assert m.sharpe_ratio == 1.8
        assert m.win_rate_30d == 0.58


class TestCapitalTransfer:
    """CapitalTransfer."""

    def test_create(self):
        t = CapitalTransfer(
            from_pool=PoolId.SCALP,
            to_pool=PoolId.SWING,
            amount=Decimal("500000"),
            reason="PROFIT_THRESHOLD_EXCEEDED",
        )
        assert t.from_pool == PoolId.SCALP
        assert t.to_pool == PoolId.SWING
        assert t.amount == Decimal("500000")
        assert t.timestamp is not None


class TestCapitalAlert:
    """CapitalAlert."""

    def test_create_warning(self):
        a = CapitalAlert(
            code="GR050",
            pool_id=None,
            message="test",
            severity="WARNING",
        )
        assert a.code == "GR050"
        assert a.severity == "WARNING"

    def test_create_critical(self):
        a = CapitalAlert(
            code="FS080",
            pool_id=PoolId.SCALP,
            message="critical",
            severity="CRITICAL",
        )
        assert a.severity == "CRITICAL"
        assert a.pool_id == PoolId.SCALP
