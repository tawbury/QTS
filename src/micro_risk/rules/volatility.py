"""Volatility Kill-Switch Rule.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §3.4
- 최우선 규칙: 시장 변동성 급등 시 포지션 축소/청산
- VIX 또는 실현 변동성 기반
- Kill: 전량 청산 (KILL_SWITCH)
- Critical: 50% 축소 (PARTIAL_EXIT)
- Warning: 로그만 (None 반환)
"""
from __future__ import annotations

from typing import Optional

from src.micro_risk.contracts import (
    ActionType,
    MarketData,
    MicroRiskAction,
    PositionShadow,
    VolatilityKillSwitchConfig,
)


class VolatilityKillSwitchRule:
    """변동성 킬스위치 규칙 (§3.4.3)."""

    def __init__(self, config: VolatilityKillSwitchConfig) -> None:
        self.config = config

    def evaluate(
        self, shadow: PositionShadow, market_data: MarketData,
    ) -> Optional[MicroRiskAction]:
        vix = market_data.vix
        realized_vol = market_data.realized_volatility

        # Kill 레벨
        if vix >= self.config.vix_kill_level or realized_vol >= self.config.realized_vol_kill:
            return MicroRiskAction(
                action_type=ActionType.KILL_SWITCH,
                symbol="ALL",
                payload={
                    "reason": "VOLATILITY_KILL_SWITCH",
                    "vix": vix,
                    "realized_vol": realized_vol,
                },
            )

        # Critical 레벨
        if vix >= self.config.vix_critical_level or realized_vol >= self.config.realized_vol_critical:
            partial_qty = int(shadow.qty * self.config.critical_exit_ratio)
            if partial_qty > 0:
                return MicroRiskAction(
                    action_type=ActionType.PARTIAL_EXIT,
                    symbol=shadow.symbol,
                    payload={
                        "qty": partial_qty,
                        "reason": "VOLATILITY_CRITICAL",
                        "vix": vix,
                        "realized_vol": realized_vol,
                    },
                )

        # Warning 레벨 — 로그만, 액션 없음
        return None
