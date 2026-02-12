"""Risk Rule Evaluator.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §2.4
- 우선순위 순서: VolatilityKillSwitch → MAE → TimeInTrade → TrailingStop
- 단락 평가: KILL_SWITCH 또는 FULL_EXIT 시 나머지 스킵
"""
from __future__ import annotations

from src.micro_risk.contracts import (
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

    @property
    def rule_count(self) -> int:
        return len(self._rules)
