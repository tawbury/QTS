"""
포트폴리오 리밸런싱 엔진.

근거: docs/arch/sub/18_System_State_Promotion_Architecture.md §5
- 드리프트 기반 리밸런싱: 현재 배분과 목표 배분의 차이 계산
- 초과 풀에서 부족 풀로 자금 이동
- max_daily_rebalance_pct: 일일 최대 리밸런싱 비율 제한
- min_trade_amount: 최소 거래 금액 필터
- drift_threshold_pct: 드리프트 임계값 이하 무시
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RebalancingConfig:
    """리밸런싱 설정."""

    max_daily_rebalance_pct: float = 0.05
    """일일 최대 리밸런싱 비율 (총 자본 대비)."""

    min_trade_amount: Decimal = Decimal("100000")
    """최소 거래 금액 (원). 이 금액 미만의 이동은 무시."""

    drift_threshold_pct: float = 0.10
    """드리프트 임계값. 이 비율 이하의 편차는 리밸런싱 대상에서 제외."""


@dataclass(frozen=True)
class RebalancingOrder:
    """리밸런싱 주문 1건."""

    from_pool: str
    """자금 출처 풀 ID."""

    to_pool: str
    """자금 도착 풀 ID."""

    amount: Decimal
    """이동 금액."""

    reason: str
    """이동 사유."""


class RebalancingEngine:
    """포트폴리오 리밸런싱 엔진.

    현재 배분과 목표 배분의 드리프트를 계산하고,
    초과 풀에서 부족 풀로 자금을 이동하는 주문 목록을 생성한다.
    """

    def __init__(self, config: Optional[RebalancingConfig] = None) -> None:
        self._config = config or RebalancingConfig()

    @property
    def config(self) -> RebalancingConfig:
        return self._config

    def calculate_rebalancing_orders(
        self,
        current_allocations: dict[str, Decimal],
        target_allocations: dict[str, Decimal],
        total_equity: Decimal,
    ) -> list[RebalancingOrder]:
        """목표 배분과 현재 배분의 차이에서 리밸런싱 주문을 계산.

        Args:
            current_allocations: 풀별 현재 배분 금액 (pool_id -> amount).
            target_allocations: 풀별 목표 배분 금액 (pool_id -> target amount).
            total_equity: 총 자본 (일일 리밸런싱 한도 계산에 사용).

        Returns:
            리밸런싱 주문 목록. 초과 풀 → 부족 풀 순서로 매칭.
        """
        if total_equity <= Decimal("0"):
            logger.warning("총 자본이 0 이하, 리밸런싱 건너뜀")
            return []

        # 풀별 드리프트 계산 (양수: 초과, 음수: 부족)
        all_pools = set(current_allocations.keys()) | set(target_allocations.keys())
        drifts: dict[str, Decimal] = {}

        for pool_id in all_pools:
            current = current_allocations.get(pool_id, Decimal("0"))
            target = target_allocations.get(pool_id, Decimal("0"))
            drift = current - target
            drifts[pool_id] = drift

        # 드리프트 임계값 필터: 총 자본 대비 비율이 임계값 이하면 무시
        threshold_amount = total_equity * Decimal(str(self._config.drift_threshold_pct))
        surplus_pools: list[tuple[str, Decimal]] = []  # (pool_id, 초과 금액)
        deficit_pools: list[tuple[str, Decimal]] = []  # (pool_id, 부족 금액)

        for pool_id, drift in drifts.items():
            if drift > Decimal("0") and drift >= threshold_amount:
                surplus_pools.append((pool_id, drift))
            elif drift < Decimal("0") and abs(drift) >= threshold_amount:
                deficit_pools.append((pool_id, abs(drift)))

        if not surplus_pools or not deficit_pools:
            return []

        # 일일 최대 리밸런싱 한도
        daily_limit = total_equity * Decimal(str(self._config.max_daily_rebalance_pct))
        remaining_budget = daily_limit

        # 초과 풀에서 부족 풀로 매칭 (큰 드리프트 우선)
        surplus_pools.sort(key=lambda x: x[1], reverse=True)
        deficit_pools.sort(key=lambda x: x[1], reverse=True)

        orders: list[RebalancingOrder] = []
        surplus_idx = 0
        deficit_idx = 0

        # 남은 금액 추적용
        surplus_remaining = [amount for _, amount in surplus_pools]
        deficit_remaining = [amount for _, amount in deficit_pools]

        while (
            surplus_idx < len(surplus_pools)
            and deficit_idx < len(deficit_pools)
            and remaining_budget > Decimal("0")
        ):
            available = min(
                surplus_remaining[surplus_idx],
                deficit_remaining[deficit_idx],
                remaining_budget,
            )

            # 최소 거래 금액 미만이면 건너뜀
            if available < self._config.min_trade_amount:
                # 현재 쌍에서 더 이상 의미 있는 금액이 안 나오면 다음으로
                if surplus_remaining[surplus_idx] <= deficit_remaining[deficit_idx]:
                    surplus_idx += 1
                else:
                    deficit_idx += 1
                continue

            from_pool = surplus_pools[surplus_idx][0]
            to_pool = deficit_pools[deficit_idx][0]

            order = RebalancingOrder(
                from_pool=from_pool,
                to_pool=to_pool,
                amount=available,
                reason=(
                    f"drift_rebalance: {from_pool}(초과 "
                    f"{surplus_remaining[surplus_idx]:,.0f}) → "
                    f"{to_pool}(부족 {deficit_remaining[deficit_idx]:,.0f})"
                ),
            )
            orders.append(order)

            surplus_remaining[surplus_idx] -= available
            deficit_remaining[deficit_idx] -= available
            remaining_budget -= available

            if surplus_remaining[surplus_idx] < self._config.min_trade_amount:
                surplus_idx += 1
            if deficit_remaining[deficit_idx] < self._config.min_trade_amount:
                deficit_idx += 1

        if orders:
            total_moved = sum(o.amount for o in orders)
            logger.info(
                "리밸런싱 주문 %d건 생성, 총 이동 금액: %s (한도: %s)",
                len(orders),
                f"{total_moved:,.0f}",
                f"{daily_limit:,.0f}",
            )

        return orders
