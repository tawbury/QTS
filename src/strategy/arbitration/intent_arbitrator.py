from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ..multiplexer.strategy_multiplexer import StrategyIntent


class IntentArbitrator:
    """
    Phase 6: 제한적 Arbitration.
    - 동일 symbol/side 중복이면 첫 번째만 남김(보수적).
    - 최적화/점수화/성과 비교 금지.
    """

    def arbitrate(self, intents: List[StrategyIntent]) -> List[StrategyIntent]:
        seen: Dict[Tuple[str, str], bool] = {}
        out: List[StrategyIntent] = []

        for si in intents:
            symbol = self._get_attr(si.intent, ("symbol", "ticker", "code"), default="")
            side = self._get_attr(si.intent, ("side", "direction"), default="")
            key = (str(symbol), str(side))

            if key in seen:
                continue
            seen[key] = True
            out.append(si)

        return out

    def _get_attr(self, obj: Any, keys: tuple[str, ...], default: Any) -> Any:
        for k in keys:
            if hasattr(obj, k):
                return getattr(obj, k)
        return default
