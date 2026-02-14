"""
Capital Engine — 풀 수준 자본 배분 오케스트레이터.

근거: docs/arch/sub/14_Capital_Flow_Architecture.md §5, §6
- OperatingState 기반 배분
- 프로모션/디모션 판단 및 실행
- 리밸런싱 필요 여부 확인
- Safety 연계
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from src.capital.allocator import calculate_target_allocation, check_drift
from src.capital.contracts import (
    CapitalAlert,
    CapitalPoolContract,
    CapitalTransfer,
    PerformanceMetrics,
    PoolId,
)
from src.capital.guardrails import run_all_guardrails
from src.capital.pool import (
    apply_transfer_in,
    apply_transfer_out,
)
from src.capital.promotion import (
    check_portfolio_demotion,
    check_scalp_to_swing,
    check_swing_demotion,
    check_swing_to_portfolio,
)
from src.safety.state import SafetyState
from src.state.contracts import OperatingState


@dataclass(frozen=True)
class CapitalEngineInput:
    """Capital Engine 입력."""

    total_equity: Decimal
    operating_state: OperatingState
    pool_states: dict[PoolId, CapitalPoolContract]
    performance_metrics: dict[PoolId, PerformanceMetrics] = field(
        default_factory=dict
    )
    safety_state: SafetyState = SafetyState.NORMAL


@dataclass(frozen=True)
class CapitalEngineOutput:
    """Capital Engine 출력."""

    allocation_decision: dict[PoolId, Decimal]
    pending_promotions: list[CapitalTransfer]
    pending_demotions: list[CapitalTransfer]
    rebalancing_required: bool
    alerts: list[CapitalAlert]
    transfers_blocked: bool = False


class CapitalEngine:
    """
    Capital Engine (§5).

    역할:
    - 풀 자본 상태 관리
    - 배분 비율 계산
    - 프로모션/디모션 판단
    - 가드레일 검사
    """

    def __init__(self, allocation_config: dict[str, str] | None = None) -> None:
        self._allocation_config = allocation_config or {}

    def evaluate(self, input_: CapitalEngineInput) -> CapitalEngineOutput:
        """메인 평가 루프."""
        pools = input_.pool_states
        total = input_.total_equity

        # Safety LOCKDOWN 시 모든 이동 차단
        if input_.safety_state in (SafetyState.LOCKDOWN, SafetyState.FAIL):
            return CapitalEngineOutput(
                allocation_decision={pid: Decimal("0") for pid in PoolId},
                pending_promotions=[],
                pending_demotions=[],
                rebalancing_required=False,
                alerts=[
                    CapitalAlert(
                        code="FS085",
                        pool_id=None,
                        message=f"Safety {input_.safety_state.value}: 모든 자본 이동 차단",
                        severity="CRITICAL",
                    )
                ],
                transfers_blocked=True,
            )

        # 1. 목표 배분 계산
        target_alloc = calculate_target_allocation(
            input_.operating_state, total,
            config_overrides=self._allocation_config,
        )

        # 2. 프로모션 확인
        promotions = self._check_promotions(pools, input_.performance_metrics)

        # 3. 디모션 확인
        demotions = self._check_demotions(pools, input_.performance_metrics)

        # 4. 리밸런싱 필요 여부
        current_pcts = self._current_allocation_pcts(pools, total)
        drifts = check_drift(current_pcts, target_alloc)
        rebalancing_required = len(drifts) > 0

        # 5. 가드레일
        alerts = run_all_guardrails(pools, total)

        return CapitalEngineOutput(
            allocation_decision=target_alloc,
            pending_promotions=promotions,
            pending_demotions=demotions,
            rebalancing_required=rebalancing_required,
            alerts=alerts,
        )

    def execute_transfers(
        self,
        pools: dict[PoolId, CapitalPoolContract],
        transfers: list[CapitalTransfer],
    ) -> list[CapitalTransfer]:
        """
        이전 실행.

        Returns: 실제 실행된 이전 목록
        """
        executed: list[CapitalTransfer] = []
        for transfer in transfers:
            from_pool = pools.get(transfer.from_pool)
            to_pool = pools.get(transfer.to_pool)
            if from_pool is None or to_pool is None:
                continue
            if from_pool.is_locked or to_pool.is_locked:
                continue
            if apply_transfer_out(from_pool, transfer.amount):
                if apply_transfer_in(to_pool, transfer.amount):
                    executed.append(transfer)
                else:
                    # 롤백: 출금 취소
                    from_pool.total_capital += transfer.amount
        return executed

    def _check_promotions(
        self,
        pools: dict[PoolId, CapitalPoolContract],
        metrics: dict[PoolId, PerformanceMetrics],
    ) -> list[CapitalTransfer]:
        """프로모션 확인."""
        transfers: list[CapitalTransfer] = []

        # Scalp→Swing
        scalp = pools.get(PoolId.SCALP)
        scalp_metrics = metrics.get(PoolId.SCALP, PerformanceMetrics())
        if scalp:
            amount = check_scalp_to_swing(scalp, scalp_metrics)
            if amount is not None and amount > 0:
                transfers.append(
                    CapitalTransfer(
                        from_pool=PoolId.SCALP,
                        to_pool=PoolId.SWING,
                        amount=amount,
                        reason="PROFIT_THRESHOLD_EXCEEDED",
                    )
                )

        # Swing→Portfolio
        swing = pools.get(PoolId.SWING)
        swing_metrics = metrics.get(PoolId.SWING, PerformanceMetrics())
        if swing:
            amount = check_swing_to_portfolio(swing, swing_metrics)
            if amount is not None and amount > 0:
                transfers.append(
                    CapitalTransfer(
                        from_pool=PoolId.SWING,
                        to_pool=PoolId.PORTFOLIO,
                        amount=amount,
                        reason="PROFIT_THRESHOLD_EXCEEDED",
                    )
                )

        return transfers

    def _check_demotions(
        self,
        pools: dict[PoolId, CapitalPoolContract],
        metrics: dict[PoolId, PerformanceMetrics],
    ) -> list[CapitalTransfer]:
        """디모션 확인."""
        transfers: list[CapitalTransfer] = []

        # Portfolio→Swing
        portfolio = pools.get(PoolId.PORTFOLIO)
        port_metrics = metrics.get(PoolId.PORTFOLIO, PerformanceMetrics())
        if portfolio:
            amount = check_portfolio_demotion(portfolio, port_metrics)
            if amount is not None and amount > 0:
                transfers.append(
                    CapitalTransfer(
                        from_pool=PoolId.PORTFOLIO,
                        to_pool=PoolId.SWING,
                        amount=amount,
                        reason="MDD_THRESHOLD_EXCEEDED",
                    )
                )

        # Swing→Scalp
        swing = pools.get(PoolId.SWING)
        swing_metrics = metrics.get(PoolId.SWING, PerformanceMetrics())
        if swing:
            amount = check_swing_demotion(swing, swing_metrics)
            if amount is not None and amount > 0:
                transfers.append(
                    CapitalTransfer(
                        from_pool=PoolId.SWING,
                        to_pool=PoolId.SCALP,
                        amount=amount,
                        reason="MDD_THRESHOLD_EXCEEDED",
                    )
                )

        return transfers

    @staticmethod
    def _current_allocation_pcts(
        pools: dict[PoolId, CapitalPoolContract],
        total_equity: Decimal,
    ) -> dict[PoolId, Decimal]:
        """현재 실제 배분 비율."""
        if total_equity <= 0:
            return {pid: Decimal("0") for pid in PoolId}
        return {
            pid: pool.total_capital / total_equity
            for pid, pool in pools.items()
        }
