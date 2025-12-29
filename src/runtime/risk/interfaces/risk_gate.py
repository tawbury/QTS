from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: Optional[str] = None


class RiskGate(Protocol):
    def before_intent(self, ops_payload: Dict[str, Any]) -> RiskDecision: ...
    def before_route(self, ops_payload: Dict[str, Any]) -> RiskDecision: ...
    def after_response(self, ops_payload: Dict[str, Any]) -> RiskDecision: ...
