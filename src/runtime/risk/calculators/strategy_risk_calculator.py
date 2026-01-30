from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..policies.risk_policy import RiskPolicy, RiskStage

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RiskResult:
    stage: RiskStage
    allowed_qty: int
    reason: str = ""


class StrategyRiskCalculator:
    """
    Phase 6: Strategy Context를 인지하는 Calculator.
    Execution Context는 모른다.
    """

    def __init__(self, default_policy: Optional[RiskPolicy] = None) -> None:
        self._default = default_policy or RiskPolicy()
        self._per_strategy: Dict[str, RiskPolicy] = {}

    def set_policy(self, strategy_id: str, policy: RiskPolicy) -> None:
        self._per_strategy[strategy_id] = policy

    def get_policy(self, strategy_id: str) -> RiskPolicy:
        return self._per_strategy.get(strategy_id, self._default)

    def evaluate(self, *, strategy_id: str, intent: Any) -> RiskResult:
        """
        Intent의 qty 속성명을 확정할 수 없으므로,
        Phase 6에서는 '최소 호환' 방식으로 qty를 탐색한다.
        """
        policy = self.get_policy(strategy_id)

        qty = self._extract_qty(intent)
        if qty is None:
            # qty를 모르면 가장 보수적으로: block
            return RiskResult(stage=RiskStage.BLOCK, allowed_qty=0, reason="qty_missing")

        if qty <= policy.max_order_qty:
            return RiskResult(stage=policy.stage, allowed_qty=qty, reason="within_max")

        # max 초과면 단계별 처리
        if policy.stage == RiskStage.WARN:
            return RiskResult(stage=RiskStage.WARN, allowed_qty=policy.max_order_qty, reason="cap_warn")
        if policy.stage == RiskStage.REDUCE:
            return RiskResult(stage=RiskStage.REDUCE, allowed_qty=min(policy.reduce_to_qty, policy.max_order_qty), reason="reduce")
        return RiskResult(stage=RiskStage.BLOCK, allowed_qty=0, reason="block")

    def _extract_qty(self, intent: Any) -> Optional[int]:
        for key in ("qty", "quantity", "order_qty"):
            if hasattr(intent, key):
                v = getattr(intent, key)
                try:
                    iv = int(v)
                    return max(iv, 0)
                except Exception as e:
                    _log.debug("Failed to extract qty from %s.%s: %s", type(intent).__name__, key, e)
                    return None
        return None

    def apply_qty(self, intent: Any, allowed_qty: int) -> Any:
        """
        Reduce가 필요한 경우 qty를 조정한 Intent를 리턴.
        dataclass/immutable일 수 있으므로:
        - replace 메서드가 있으면 사용
        - 없으면 동일 객체의 qty 속성 수정 시도(가능한 경우)
        - 둘 다 안되면 원본 반환
        """
        if allowed_qty < 0:
            allowed_qty = 0

        if hasattr(intent, "replace"):
            try:
                return intent.replace(qty=allowed_qty)  # type: ignore[attr-defined]
            except Exception as e:
                _log.debug("intent.replace(qty=%d) failed: %s", allowed_qty, e)

        for key in ("qty", "quantity", "order_qty"):
            if hasattr(intent, key):
                try:
                    setattr(intent, key, allowed_qty)
                    return intent
                except Exception as e:
                    _log.debug("setattr(intent, %s, %d) failed: %s", key, allowed_qty, e)
                    return intent
        return intent
