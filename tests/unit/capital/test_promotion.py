"""프로모션/디모션 엔진 테스트."""
from decimal import Decimal

import pytest

from src.capital.contracts import (
    SCALP_TO_SWING_CRITERIA,
    SWING_TO_PORTFOLIO_CRITERIA,
    CapitalPoolContract,
    PerformanceMetrics,
    PoolId,
    PoolState,
)
from src.capital.promotion import (
    check_portfolio_demotion,
    check_scalp_to_swing,
    check_swing_demotion,
    check_swing_to_portfolio,
)


@pytest.fixture
def scalp_pool() -> CapitalPoolContract:
    return CapitalPoolContract(
        pool_id=PoolId.SCALP,
        total_capital=Decimal("10000000"),
        accumulated_profit=Decimal("1500000"),
    )


@pytest.fixture
def good_scalp_metrics() -> PerformanceMetrics:
    return PerformanceMetrics(
        sharpe_ratio=1.8,
        win_rate_30d=0.58,
        trades_30d=60,
        mdd_30d=0.08,
    )


@pytest.fixture
def swing_pool() -> CapitalPoolContract:
    return CapitalPoolContract(
        pool_id=PoolId.SWING,
        total_capital=Decimal("8000000"),
        accumulated_profit=Decimal("6000000"),
    )


@pytest.fixture
def portfolio_pool() -> CapitalPoolContract:
    return CapitalPoolContract(
        pool_id=PoolId.PORTFOLIO,
        total_capital=Decimal("15000000"),
    )


class TestScalpToSwing:
    """Scalp→Swing 프로모션."""

    def test_promotion_criteria_met(
        self, scalp_pool: CapitalPoolContract, good_scalp_metrics: PerformanceMetrics
    ):
        amount = check_scalp_to_swing(scalp_pool, good_scalp_metrics)
        assert amount is not None
        # (1.5M - 1M) * 0.5 = 250K
        assert amount == Decimal("250000")

    def test_profit_below_threshold(self, good_scalp_metrics: PerformanceMetrics):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("10000000"),
            accumulated_profit=Decimal("500000"),  # < 1M
        )
        assert check_scalp_to_swing(pool, good_scalp_metrics) is None

    def test_sharpe_too_low(self, scalp_pool: CapitalPoolContract):
        metrics = PerformanceMetrics(
            sharpe_ratio=1.0,  # < 1.5
            win_rate_30d=0.58,
            trades_30d=60,
            mdd_30d=0.08,
        )
        assert check_scalp_to_swing(scalp_pool, metrics) is None

    def test_win_rate_too_low(self, scalp_pool: CapitalPoolContract):
        metrics = PerformanceMetrics(
            sharpe_ratio=1.8,
            win_rate_30d=0.40,  # < 0.55
            trades_30d=60,
            mdd_30d=0.08,
        )
        assert check_scalp_to_swing(scalp_pool, metrics) is None

    def test_too_few_trades(self, scalp_pool: CapitalPoolContract):
        metrics = PerformanceMetrics(
            sharpe_ratio=1.8,
            win_rate_30d=0.58,
            trades_30d=20,  # < 50
            mdd_30d=0.08,
        )
        assert check_scalp_to_swing(scalp_pool, metrics) is None

    def test_mdd_too_high(self, scalp_pool: CapitalPoolContract):
        metrics = PerformanceMetrics(
            sharpe_ratio=1.8,
            win_rate_30d=0.58,
            trades_30d=60,
            mdd_30d=0.15,  # > 0.10
        )
        assert check_scalp_to_swing(scalp_pool, metrics) is None

    def test_locked_pool(self, good_scalp_metrics: PerformanceMetrics):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("10000000"),
            accumulated_profit=Decimal("1500000"),
            pool_state=PoolState.LOCKED,
        )
        assert check_scalp_to_swing(pool, good_scalp_metrics) is None

    def test_large_profit_capped_by_available(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("2000000"),
            invested_capital=Decimal("1800000"),  # available = 200K
            accumulated_profit=Decimal("5000000"),
        )
        metrics = PerformanceMetrics(
            sharpe_ratio=2.0, win_rate_30d=0.60, trades_30d=100, mdd_30d=0.05
        )
        amount = check_scalp_to_swing(pool, metrics)
        # (5M-1M)*0.5 = 2M but capped at available 200K
        assert amount == Decimal("200000")


class TestSwingToPortfolio:
    """Swing→Portfolio 프로모션."""

    def test_promotion_criteria_met(self, swing_pool: CapitalPoolContract):
        metrics = PerformanceMetrics(sharpe_ratio=1.5, mdd_30d=0.10)
        amount = check_swing_to_portfolio(swing_pool, metrics)
        assert amount is not None
        # (6M - 5M) * 0.3 = 300K
        assert amount == Decimal("300000")

    def test_profit_below_threshold(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SWING,
            total_capital=Decimal("8000000"),
            accumulated_profit=Decimal("3000000"),  # < 5M
        )
        metrics = PerformanceMetrics(sharpe_ratio=1.5)
        assert check_swing_to_portfolio(pool, metrics) is None


class TestPortfolioDemotion:
    """Portfolio→Swing 디모션."""

    def test_mdd_triggers_demotion(self, portfolio_pool: CapitalPoolContract):
        metrics = PerformanceMetrics(mdd_30d=0.12)  # > 0.10
        amount = check_portfolio_demotion(portfolio_pool, metrics)
        assert amount is not None
        # 15M * 0.20 = 3M
        assert amount == Decimal("3000000")

    def test_mdd_below_threshold(self, portfolio_pool: CapitalPoolContract):
        metrics = PerformanceMetrics(mdd_30d=0.08)  # <= 0.10
        assert check_portfolio_demotion(portfolio_pool, metrics) is None

    def test_locked_pool(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.PORTFOLIO,
            total_capital=Decimal("15000000"),
            pool_state=PoolState.LOCKED,
        )
        metrics = PerformanceMetrics(mdd_30d=0.20)
        assert check_portfolio_demotion(pool, metrics) is None


class TestSwingDemotion:
    """Swing→Scalp 디모션."""

    def test_mdd_triggers(self, swing_pool: CapitalPoolContract):
        metrics = PerformanceMetrics(mdd_30d=0.20)  # > 0.15
        amount = check_swing_demotion(swing_pool, metrics)
        assert amount is not None
        # 8M * 0.30 = 2.4M
        assert amount == Decimal("2400000")

    def test_consecutive_losses_trigger(self, swing_pool: CapitalPoolContract):
        metrics = PerformanceMetrics(
            mdd_30d=0.05,  # MDD OK
            consecutive_losses=6,  # >= 5
        )
        amount = check_swing_demotion(swing_pool, metrics)
        assert amount is not None
        assert amount == Decimal("2400000")

    def test_no_trigger(self, swing_pool: CapitalPoolContract):
        metrics = PerformanceMetrics(mdd_30d=0.10, consecutive_losses=3)
        assert check_swing_demotion(swing_pool, metrics) is None

    def test_capped_by_available(self):
        pool = CapitalPoolContract(
            pool_id=PoolId.SWING,
            total_capital=Decimal("8000000"),
            invested_capital=Decimal("7000000"),  # available = 1M
        )
        metrics = PerformanceMetrics(mdd_30d=0.20)
        amount = check_swing_demotion(pool, metrics)
        # 8M * 0.30 = 2.4M but available = 1M
        assert amount == Decimal("1000000")
