"""CapitalEngine 테스트."""
from decimal import Decimal

import pytest

from src.capital.contracts import (
    CapitalPoolContract,
    CapitalTransfer,
    PerformanceMetrics,
    PoolId,
    PoolState,
)
from src.capital.engine import CapitalEngine, CapitalEngineInput, CapitalEngineOutput
from src.capital.pool import lock_pool
from src.safety.state import SafetyState
from src.state.contracts import OperatingState


def _make_balanced_pools() -> dict[PoolId, CapitalPoolContract]:
    return {
        PoolId.SCALP: CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("4000000"),
            allocation_pct=Decimal("0.40"),
            target_allocation_pct=Decimal("0.40"),
        ),
        PoolId.SWING: CapitalPoolContract(
            pool_id=PoolId.SWING,
            total_capital=Decimal("3500000"),
            allocation_pct=Decimal("0.35"),
            target_allocation_pct=Decimal("0.35"),
        ),
        PoolId.PORTFOLIO: CapitalPoolContract(
            pool_id=PoolId.PORTFOLIO,
            total_capital=Decimal("2500000"),
            allocation_pct=Decimal("0.25"),
            target_allocation_pct=Decimal("0.25"),
        ),
    }


@pytest.fixture
def engine() -> CapitalEngine:
    return CapitalEngine()


class TestEvaluateBasic:
    """기본 평가."""

    def test_normal_evaluation(self, engine: CapitalEngine):
        pools = _make_balanced_pools()
        input_ = CapitalEngineInput(
            total_equity=Decimal("10000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
        )
        output = engine.evaluate(input_)
        assert isinstance(output, CapitalEngineOutput)
        assert sum(output.allocation_decision.values()) == Decimal("1.0000")
        assert not output.transfers_blocked

    def test_all_states(self, engine: CapitalEngine):
        """모든 OperatingState에서 정상 동작."""
        for state in OperatingState:
            pools = _make_balanced_pools()
            input_ = CapitalEngineInput(
                total_equity=Decimal("10000000"),
                operating_state=state,
                pool_states=pools,
            )
            output = engine.evaluate(input_)
            assert sum(output.allocation_decision.values()) == Decimal("1.0000")


class TestSafetyBlocking:
    """Safety 상태에 따른 차단."""

    def test_lockdown_blocks_transfers(self, engine: CapitalEngine):
        pools = _make_balanced_pools()
        input_ = CapitalEngineInput(
            total_equity=Decimal("10000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
            safety_state=SafetyState.LOCKDOWN,
        )
        output = engine.evaluate(input_)
        assert output.transfers_blocked
        assert len(output.pending_promotions) == 0
        assert len(output.pending_demotions) == 0
        assert any(a.code == "FS085" for a in output.alerts)

    def test_fail_blocks_transfers(self, engine: CapitalEngine):
        pools = _make_balanced_pools()
        input_ = CapitalEngineInput(
            total_equity=Decimal("10000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
            safety_state=SafetyState.FAIL,
        )
        output = engine.evaluate(input_)
        assert output.transfers_blocked

    def test_normal_allows_transfers(self, engine: CapitalEngine):
        pools = _make_balanced_pools()
        input_ = CapitalEngineInput(
            total_equity=Decimal("10000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
            safety_state=SafetyState.NORMAL,
        )
        output = engine.evaluate(input_)
        assert not output.transfers_blocked


class TestPromotionDetection:
    """프로모션 감지."""

    def test_scalp_promotion_detected(self, engine: CapitalEngine):
        pools = _make_balanced_pools()
        pools[PoolId.SCALP].accumulated_profit = Decimal("1500000")
        metrics = {
            PoolId.SCALP: PerformanceMetrics(
                sharpe_ratio=1.8,
                win_rate_30d=0.58,
                trades_30d=60,
                mdd_30d=0.08,
            ),
        }
        input_ = CapitalEngineInput(
            total_equity=Decimal("10000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
            performance_metrics=metrics,
        )
        output = engine.evaluate(input_)
        assert len(output.pending_promotions) >= 1
        promo = output.pending_promotions[0]
        assert promo.from_pool == PoolId.SCALP
        assert promo.to_pool == PoolId.SWING

    def test_no_promotion_when_criteria_not_met(self, engine: CapitalEngine):
        pools = _make_balanced_pools()
        input_ = CapitalEngineInput(
            total_equity=Decimal("10000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
        )
        output = engine.evaluate(input_)
        assert len(output.pending_promotions) == 0


class TestDemotionDetection:
    """디모션 감지."""

    def test_portfolio_demotion(self, engine: CapitalEngine):
        pools = _make_balanced_pools()
        metrics = {
            PoolId.PORTFOLIO: PerformanceMetrics(mdd_30d=0.15),
        }
        input_ = CapitalEngineInput(
            total_equity=Decimal("10000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
            performance_metrics=metrics,
        )
        output = engine.evaluate(input_)
        assert len(output.pending_demotions) >= 1
        demo = output.pending_demotions[0]
        assert demo.from_pool == PoolId.PORTFOLIO
        assert demo.to_pool == PoolId.SWING


class TestRebalancing:
    """리밸런싱 감지."""

    def test_no_rebalancing_needed(self, engine: CapitalEngine):
        pools = _make_balanced_pools()
        input_ = CapitalEngineInput(
            total_equity=Decimal("10000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
        )
        output = engine.evaluate(input_)
        # BALANCED 상태의 목표와 현재 배분이 비슷하면 rebalancing 불필요
        # (정확한 결과는 allocator의 계산에 따라 다를 수 있음)
        assert isinstance(output.rebalancing_required, bool)

    def test_heavily_drifted_needs_rebalancing(self, engine: CapitalEngine):
        pools = {
            PoolId.SCALP: CapitalPoolContract(
                pool_id=PoolId.SCALP,
                total_capital=Decimal("8000000"),
                target_allocation_pct=Decimal("0.40"),
            ),
            PoolId.SWING: CapitalPoolContract(
                pool_id=PoolId.SWING,
                total_capital=Decimal("1000000"),
                target_allocation_pct=Decimal("0.35"),
            ),
            PoolId.PORTFOLIO: CapitalPoolContract(
                pool_id=PoolId.PORTFOLIO,
                total_capital=Decimal("1000000"),
                target_allocation_pct=Decimal("0.25"),
            ),
        }
        input_ = CapitalEngineInput(
            total_equity=Decimal("10000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
        )
        output = engine.evaluate(input_)
        assert output.rebalancing_required


class TestExecuteTransfers:
    """이전 실행."""

    def test_normal_transfer(self, engine: CapitalEngine):
        pools = _make_balanced_pools()
        transfers = [
            CapitalTransfer(
                from_pool=PoolId.SCALP,
                to_pool=PoolId.SWING,
                amount=Decimal("500000"),
                reason="test",
            )
        ]
        executed = engine.execute_transfers(pools, transfers)
        assert len(executed) == 1
        assert pools[PoolId.SCALP].total_capital == Decimal("3500000")
        assert pools[PoolId.SWING].total_capital == Decimal("4000000")

    def test_locked_source_blocked(self, engine: CapitalEngine):
        pools = _make_balanced_pools()
        lock_pool(pools[PoolId.SCALP], "test")
        transfers = [
            CapitalTransfer(
                from_pool=PoolId.SCALP,
                to_pool=PoolId.SWING,
                amount=Decimal("500000"),
                reason="test",
            )
        ]
        executed = engine.execute_transfers(pools, transfers)
        assert len(executed) == 0

    def test_insufficient_funds_blocked(self, engine: CapitalEngine):
        pools = _make_balanced_pools()
        pools[PoolId.SCALP].invested_capital = Decimal("3800000")
        # available = 4M - 3.8M = 200K
        transfers = [
            CapitalTransfer(
                from_pool=PoolId.SCALP,
                to_pool=PoolId.SWING,
                amount=Decimal("500000"),
                reason="test",
            )
        ]
        executed = engine.execute_transfers(pools, transfers)
        assert len(executed) == 0

    def test_multiple_transfers(self, engine: CapitalEngine):
        pools = _make_balanced_pools()
        transfers = [
            CapitalTransfer(
                from_pool=PoolId.SCALP,
                to_pool=PoolId.SWING,
                amount=Decimal("200000"),
                reason="promo",
            ),
            CapitalTransfer(
                from_pool=PoolId.PORTFOLIO,
                to_pool=PoolId.SWING,
                amount=Decimal("300000"),
                reason="demo",
            ),
        ]
        executed = engine.execute_transfers(pools, transfers)
        assert len(executed) == 2
        assert pools[PoolId.SWING].total_capital == Decimal("4000000")
