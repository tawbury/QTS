"""MAE (Maximum Adverse Excursion) Rule.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §3.2
- 진입 후 최대 불리 이동 측정
- position_mae_threshold_pct 초과 시 전량 청산
- partial_exit_at_pct 초과 시 부분 청산
"""
from __future__ import annotations

from typing import Optional

from src.micro_risk.contracts import (
    ActionType,
    MAEConfig,
    MarketData,
    MicroRiskAction,
    PositionShadow,
)


class MAERule:
    """MAE 규칙 (§3.2.4)."""

    def __init__(self, config: MAEConfig) -> None:
        self.config = config

    def evaluate(
        self, shadow: PositionShadow, market_data: MarketData,
    ) -> Optional[MicroRiskAction]:
        mae_pct = shadow.mae_pct

        # 전량 청산 임계값
        if abs(mae_pct) >= self.config.position_mae_threshold_pct:
            return MicroRiskAction(
                action_type=ActionType.FULL_EXIT,
                symbol=shadow.symbol,
                payload={
                    "qty": shadow.qty,
                    "reason": "MAE_THRESHOLD_EXCEEDED",
                    "mae_pct": mae_pct,
                    "threshold": self.config.position_mae_threshold_pct,
                },
            )

        # 부분 청산 임계값
        if abs(mae_pct) >= self.config.partial_exit_at_pct:
            partial_qty = int(shadow.qty * self.config.partial_exit_ratio)
            if partial_qty > 0:
                return MicroRiskAction(
                    action_type=ActionType.PARTIAL_EXIT,
                    symbol=shadow.symbol,
                    payload={
                        "qty": partial_qty,
                        "reason": "MAE_PARTIAL_THRESHOLD",
                        "mae_pct": mae_pct,
                    },
                )

        return None
