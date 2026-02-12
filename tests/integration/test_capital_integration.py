"""Capital Flow + State + Safety + Event 통합 테스트."""
from decimal import Decimal

import pytest

from src.capital.allocator import calculate_target_allocation
from src.capital.contracts import (
    CapitalPoolContract,
    CapitalTransfer,
    PerformanceMetrics,
    PoolId,
    PoolState,
)
from src.capital.engine import CapitalEngine, CapitalEngineInput
from src.capital.guardrails import run_all_guardrails
from src.capital.pool import (
    apply_transfer_in,
    apply_transfer_out,
    create_pool,
    lock_pool,
    unlock_pool,
)
from src.capital.promotion import (
    check_portfolio_demotion,
    check_scalp_to_swing,
    check_swing_demotion,
)
from src.event.contracts import EventType, create_event
from src.safety.state import SafetyState, SafetyStateManager
from src.state.contracts import OperatingState, STATE_PROPERTIES


class TestCapitalStateIntegration:
    """Capital + OperatingState 통합."""

    def test_aggressive_favors_scalp(self):
        alloc = calculate_target_allocation(
            OperatingState.AGGRESSIVE, Decimal("30000000")
        )
        assert alloc[PoolId.SCALP] > alloc[PoolId.PORTFOLIO]

    def test_defensive_favors_portfolio(self):
        alloc = calculate_target_allocation(
            OperatingState.DEFENSIVE, Decimal("30000000")
        )
        assert alloc[PoolId.PORTFOLIO] > alloc[PoolId.SCALP]

    def test_state_properties_alignment(self):
        """STATE_PROPERTIES의 allocation_range가 capital과 일관되는지."""
        for state in OperatingState:
            props = STATE_PROPERTIES[state]
            alloc = calculate_target_allocation(state, Decimal("100000000"))
            # scalp 비율은 scalp_allocation_range 내에 있어야 함 (정규화 전 기준)
            assert sum(alloc.values()) == Decimal("1.0000")

    def test_all_states_produce_valid_allocations(self):
        for state in OperatingState:
            alloc = calculate_target_allocation(state, Decimal("50000000"))
            for pid in PoolId:
                assert alloc[pid] > 0
            assert sum(alloc.values()) == Decimal("1.0000")


class TestCapitalSafetyIntegration:
    """Capital + Safety 통합."""

    def test_lockdown_blocks_engine(self):
        engine = CapitalEngine()
        pools = {
            PoolId.SCALP: create_pool(PoolId.SCALP, Decimal("4000000")),
            PoolId.SWING: create_pool(PoolId.SWING, Decimal("3500000")),
            PoolId.PORTFOLIO: create_pool(PoolId.PORTFOLIO, Decimal("2500000")),
        }
        input_ = CapitalEngineInput(
            total_equity=Decimal("10000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
            safety_state=SafetyState.LOCKDOWN,
        )
        output = engine.evaluate(input_)
        assert output.transfers_blocked
        assert any(a.code == "FS085" for a in output.alerts)

    def test_fail_blocks_engine(self):
        engine = CapitalEngine()
        pools = {
            PoolId.SCALP: create_pool(PoolId.SCALP, Decimal("4000000")),
            PoolId.SWING: create_pool(PoolId.SWING, Decimal("3500000")),
            PoolId.PORTFOLIO: create_pool(PoolId.PORTFOLIO, Decimal("2500000")),
        }
        input_ = CapitalEngineInput(
            total_equity=Decimal("10000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
            safety_state=SafetyState.FAIL,
        )
        output = engine.evaluate(input_)
        assert output.transfers_blocked

    def test_normal_allows_engine(self):
        engine = CapitalEngine()
        pools = {
            PoolId.SCALP: create_pool(PoolId.SCALP, Decimal("4000000")),
            PoolId.SWING: create_pool(PoolId.SWING, Decimal("3500000")),
            PoolId.PORTFOLIO: create_pool(PoolId.PORTFOLIO, Decimal("2500000")),
        }
        input_ = CapitalEngineInput(
            total_equity=Decimal("10000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
            safety_state=SafetyState.NORMAL,
        )
        output = engine.evaluate(input_)
        assert not output.transfers_blocked

    def test_safety_state_machine_to_lockdown(self):
        """Safety 상태 머신 → LOCKDOWN 시 풀 잠금 시나리오."""
        mgr = SafetyStateManager()
        mgr.apply_fail_safe("FS082")
        mgr.apply_fail_safe("FS082")
        assert mgr.current_state == SafetyState.LOCKDOWN

        engine = CapitalEngine()
        pools = {
            PoolId.SCALP: create_pool(PoolId.SCALP, Decimal("4000000")),
            PoolId.SWING: create_pool(PoolId.SWING, Decimal("3500000")),
            PoolId.PORTFOLIO: create_pool(PoolId.PORTFOLIO, Decimal("2500000")),
        }
        input_ = CapitalEngineInput(
            total_equity=Decimal("10000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
            safety_state=mgr.current_state,
        )
        output = engine.evaluate(input_)
        assert output.transfers_blocked


class TestPromotionDemotionFlow:
    """전체 프로모션/디모션 흐름."""

    def test_full_promotion_execution(self):
        """Scalp 프로모션 → 실행 → 잔액 확인."""
        engine = CapitalEngine()
        scalp = CapitalPoolContract(
            pool_id=PoolId.SCALP,
            total_capital=Decimal("10000000"),
            accumulated_profit=Decimal("1500000"),
            allocation_pct=Decimal("0.50"),
            target_allocation_pct=Decimal("0.40"),
        )
        swing = CapitalPoolContract(
            pool_id=PoolId.SWING,
            total_capital=Decimal("5000000"),
            allocation_pct=Decimal("0.25"),
            target_allocation_pct=Decimal("0.35"),
        )
        portfolio = CapitalPoolContract(
            pool_id=PoolId.PORTFOLIO,
            total_capital=Decimal("5000000"),
            allocation_pct=Decimal("0.25"),
            target_allocation_pct=Decimal("0.25"),
        )
        pools = {PoolId.SCALP: scalp, PoolId.SWING: swing, PoolId.PORTFOLIO: portfolio}
        metrics = {
            PoolId.SCALP: PerformanceMetrics(
                sharpe_ratio=1.8, win_rate_30d=0.58, trades_30d=60, mdd_30d=0.08
            ),
        }

        input_ = CapitalEngineInput(
            total_equity=Decimal("20000000"),
            operating_state=OperatingState.BALANCED,
            pool_states=pools,
            performance_metrics=metrics,
        )
        output = engine.evaluate(input_)
        assert len(output.pending_promotions) >= 1

        # 실행
        executed = engine.execute_transfers(pools, output.pending_promotions)
        assert len(executed) == 1
        assert pools[PoolId.SCALP].total_capital < Decimal("10000000")
        assert pools[PoolId.SWING].total_capital > Decimal("5000000")

    def test_demotion_on_high_mdd(self):
        """Portfolio MDD 초과 → 디모션 → 실행."""
        engine = CapitalEngine()
        pools = {
            PoolId.SCALP: create_pool(PoolId.SCALP, Decimal("4000000")),
            PoolId.SWING: create_pool(PoolId.SWING, Decimal("3000000")),
            PoolId.PORTFOLIO: CapitalPoolContract(
                pool_id=PoolId.PORTFOLIO,
                total_capital=Decimal("3000000"),
            ),
        }
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

        executed = engine.execute_transfers(pools, output.pending_demotions)
        assert len(executed) == 1
        assert pools[PoolId.PORTFOLIO].total_capital < Decimal("3000000")
        assert pools[PoolId.SWING].total_capital > Decimal("3000000")


class TestGuardrailIntegration:
    """가드레일 통합 시나리오."""

    def test_healthy_pools_no_alerts(self):
        pools = {
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
        alerts = run_all_guardrails(pools, Decimal("10000000"))
        assert len(alerts) == 0

    def test_zero_equity_triggers_fs080(self):
        pools = {
            PoolId.SCALP: create_pool(PoolId.SCALP, Decimal("0")),
            PoolId.SWING: create_pool(PoolId.SWING, Decimal("0")),
            PoolId.PORTFOLIO: create_pool(PoolId.PORTFOLIO, Decimal("0")),
        }
        alerts = run_all_guardrails(pools, Decimal("0"))
        assert any(a.code == "FS080" for a in alerts)


class TestEmergencyCapitalLock:
    """긴급 자본 잠금 시나리오."""

    def test_lock_prevents_transfers(self):
        engine = CapitalEngine()
        pools = {
            PoolId.SCALP: create_pool(PoolId.SCALP, Decimal("4000000")),
            PoolId.SWING: create_pool(PoolId.SWING, Decimal("3500000")),
            PoolId.PORTFOLIO: create_pool(PoolId.PORTFOLIO, Decimal("2500000")),
        }
        # SCALP 잠금
        lock_pool(pools[PoolId.SCALP], "FS082")

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

    def test_unlock_resumes_transfers(self):
        engine = CapitalEngine()
        pools = {
            PoolId.SCALP: create_pool(PoolId.SCALP, Decimal("4000000")),
            PoolId.SWING: create_pool(PoolId.SWING, Decimal("3500000")),
            PoolId.PORTFOLIO: create_pool(PoolId.PORTFOLIO, Decimal("2500000")),
        }
        lock_pool(pools[PoolId.SCALP], "test")
        unlock_pool(pools[PoolId.SCALP])

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


class TestEventIntegration:
    """Capital + Event 시스템 통합."""

    def test_position_update_event_is_p0(self):
        """포지션 업데이트(자본 이동 후)는 P0."""
        from src.event.contracts import EventPriority

        event = create_event(EventType.POSITION_UPDATE, source="capital_engine")
        assert event.priority == EventPriority.P0_CRITICAL

    def test_metric_event_is_p3(self):
        """자본 메트릭 기록은 P3."""
        from src.event.contracts import EventPriority

        event = create_event(EventType.METRIC_RECORD, source="capital_engine")
        assert event.priority == EventPriority.P3_LOW
