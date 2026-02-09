from __future__ import annotations

from typing import Any, Dict

from .interfaces.risk_gate import RiskDecision, RiskGate


class NoopRiskGate(RiskGate):
    def before_intent(self, ops_payload: Dict[str, Any]) -> RiskDecision:
        return RiskDecision(allowed=True)

    def before_route(self, ops_payload: Dict[str, Any]) -> RiskDecision:
        return RiskDecision(allowed=True)

    def after_response(self, ops_payload: Dict[str, Any]) -> RiskDecision:
        return RiskDecision(allowed=True)
