"""Time-in-Trade Rule.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §3.3
- 포지션 보유 시간이 최대 허용 시간 초과 시 강제 청산
- 전략별 max_time: SCALP=3600s, SWING=604800s, PORTFOLIO=None
- 수익 중이면 연장 가능
"""
from __future__ import annotations

from typing import Optional

from src.micro_risk.contracts import (
    ActionType,
    MarketData,
    MicroRiskAction,
    PositionShadow,
    TimeInTradeConfig,
)


class TimeInTradeRule:
    """보유 시간 규칙 (§3.3.3)."""

    def __init__(self, config: TimeInTradeConfig) -> None:
        self.config = config

    def evaluate(
        self, shadow: PositionShadow, market_data: MarketData,
    ) -> Optional[MicroRiskAction]:
        max_time = self.config.get_max_time(shadow.strategy)
        if max_time is None:
            return None

        time_in_trade = shadow.time_in_trade_sec

        # 연장 조건 확인
        if self._can_extend(shadow):
            max_time += self.config.extension_time_sec

        # 시간 초과 → 전량 청산
        if time_in_trade >= max_time:
            return MicroRiskAction(
                action_type=ActionType.FULL_EXIT,
                symbol=shadow.symbol,
                payload={
                    "qty": shadow.qty,
                    "reason": "TIME_IN_TRADE_EXCEEDED",
                    "time_in_trade_sec": time_in_trade,
                    "max_time_sec": max_time,
                },
            )

        return None

    def is_warning(self, shadow: PositionShadow) -> bool:
        """경고 상태 여부 (GR072용)."""
        max_time = self.config.get_max_time(shadow.strategy)
        if max_time is None:
            return False

        if self._can_extend(shadow):
            max_time += self.config.extension_time_sec

        return shadow.time_in_trade_sec >= int(max_time * self.config.warning_at_pct)

    def _can_extend(self, shadow: PositionShadow) -> bool:
        """연장 조건 확인."""
        if self.config.extension_profitable:
            return shadow.unrealized_pnl > 0
        return False
