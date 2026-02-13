"""Risk Rule Evaluator.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §2.4
- 우선순위 순서: VolatilityKillSwitch → MAE → TimeInTrade → TrailingStop
- 단락 평가: KILL_SWITCH 또는 FULL_EXIT 시 나머지 스킵
- 계정 수준 MAE: 전체 포지션 합산 손실이 임계값 초과 시 전량 청산
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.micro_risk.contracts import (
    ActionType,
    MarketData,
    MicroRiskAction,
    MicroRiskConfig,
    PositionShadow,
    SHORT_CIRCUIT_ACTIONS,
)
from src.micro_risk.rules.mae import MAERule
from src.micro_risk.rules.time_in_trade import TimeInTradeRule
from src.micro_risk.rules.trailing_stop import TrailingStopRule
from src.micro_risk.rules.volatility import VolatilityKillSwitchRule


class RiskRuleEvaluator:
    """리스크 규칙 평가기 (§2.4)."""

    def __init__(self, config: MicroRiskConfig) -> None:
        self.config = config
        self._rules = [
            VolatilityKillSwitchRule(config.volatility),
            MAERule(config.mae),
            TimeInTradeRule(config.time_in_trade),
            TrailingStopRule(config.trailing_stop),
        ]

    def evaluate(
        self, shadow: PositionShadow, market_data: MarketData,
    ) -> list[MicroRiskAction]:
        """모든 규칙 평가, 트리거된 액션 반환 (§2.4.3)."""
        actions: list[MicroRiskAction] = []

        for rule in self._rules:
            action = rule.evaluate(shadow, market_data)
            if action is not None:
                actions.append(action)

                # 단락 평가: KILL_SWITCH 또는 FULL_EXIT 시 나머지 스킵
                if action.action_type in SHORT_CIRCUIT_ACTIONS:
                    break

        return actions

    def evaluate_account_mae(
        self,
        shadows: list[PositionShadow],
        total_equity: Decimal,
    ) -> Optional[MicroRiskAction]:
        """계정 수준 MAE 평가.

        전체 포지션의 합산 미실현 손실이 account_mae_threshold_pct를 초과하면
        KILL_SWITCH 액션을 반환한다.

        Args:
            shadows: 모니터링 중인 전체 포지션 섀도우
            total_equity: 계정 총 자산 (원금 기준)

        Returns:
            임계값 초과 시 KILL_SWITCH 액션, 아니면 None
        """
        if total_equity <= 0:
            return None

        # 모든 포지션의 미실현 손실 합산 (음수 PnL만)
        total_unrealized_loss = sum(
            shadow.unrealized_pnl
            for shadow in shadows
            if shadow.qty != 0 and shadow.unrealized_pnl < 0
        )

        # 계정 수준 MAE 비율 (음수)
        account_mae_pct = total_unrealized_loss / total_equity

        threshold = self.config.account_mae_threshold_pct

        if abs(account_mae_pct) >= threshold:
            return MicroRiskAction(
                action_type=ActionType.KILL_SWITCH,
                symbol="ALL",
                payload={
                    "reason": "ACCOUNT_MAE_THRESHOLD_EXCEEDED",
                    "account_mae_pct": account_mae_pct,
                    "threshold": threshold,
                    "total_unrealized_loss": total_unrealized_loss,
                    "total_equity": total_equity,
                },
                priority="P0",
            )

        return None

    @property
    def rule_count(self) -> int:
        return len(self._rules)
