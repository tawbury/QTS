"""Trailing Stop Rule.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §3.1
- 수익 발생 포지션에서 일정 비율 이익 보호
- 고점 대비 trail_distance_pct 아래에 스탑
- ratchet: 스탑은 위로만 이동
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.micro_risk.contracts import (
    ActionType,
    MarketData,
    MicroRiskAction,
    PositionShadow,
    TrailingStopConfig,
)


def should_activate_trailing_stop(
    shadow: PositionShadow, config: TrailingStopConfig,
) -> bool:
    """트레일링 스탑 활성화 조건 (§3.1.2)."""
    return (
        shadow.unrealized_pnl_pct >= config.activation_profit_pct
        and not shadow.trailing_stop_active
    )


def calculate_trailing_stop_price(
    shadow: PositionShadow, config: TrailingStopConfig,
) -> Decimal:
    """스탑 가격 계산 (§3.1.3)."""
    highest = shadow.highest_price_since_entry

    # 고점 대비 trail_distance 아래
    stop_price = highest * (1 - config.trail_distance_pct)

    # 최소 거리 보장
    min_stop = highest - config.min_trail_distance
    stop_price = max(stop_price, min_stop)

    # 래칫: 기존 스탑보다 높아야만 업데이트
    if config.ratchet_only and shadow.trailing_stop_price > 0:
        stop_price = max(stop_price, shadow.trailing_stop_price)

    return stop_price


class TrailingStopRule:
    """트레일링 스탑 규칙 (§3.1.4)."""

    def __init__(self, config: TrailingStopConfig) -> None:
        self.config = config

    def evaluate(
        self, shadow: PositionShadow, market_data: MarketData,
    ) -> Optional[MicroRiskAction]:
        # 활성화 체크
        if not shadow.trailing_stop_active:
            if should_activate_trailing_stop(shadow, self.config):
                # 활성화 + 초기 스탑 설정
                shadow.trailing_stop_active = True
                shadow.trailing_stop_price = calculate_trailing_stop_price(
                    shadow, self.config,
                )
                return MicroRiskAction(
                    action_type=ActionType.TRAILING_STOP_ADJUST,
                    symbol=shadow.symbol,
                    payload={
                        "old_stop": Decimal("0"),
                        "new_stop": shadow.trailing_stop_price,
                        "reason": "TRAILING_STOP_ACTIVATED",
                    },
                )
            return None

        # 스탑 히트 체크
        if shadow.current_price <= shadow.trailing_stop_price:
            return MicroRiskAction(
                action_type=ActionType.FULL_EXIT,
                symbol=shadow.symbol,
                payload={
                    "qty": shadow.qty,
                    "reason": "TRAILING_STOP_HIT",
                    "stop_price": shadow.trailing_stop_price,
                    "current_price": shadow.current_price,
                },
            )

        # 스탑 가격 조정
        new_stop = calculate_trailing_stop_price(shadow, self.config)
        if new_stop > shadow.trailing_stop_price:
            old_stop = shadow.trailing_stop_price
            shadow.trailing_stop_price = new_stop
            return MicroRiskAction(
                action_type=ActionType.TRAILING_STOP_ADJUST,
                symbol=shadow.symbol,
                payload={
                    "old_stop": old_stop,
                    "new_stop": new_stop,
                },
            )

        return None
