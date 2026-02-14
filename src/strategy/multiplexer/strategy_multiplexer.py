from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List, Optional, Sequence, Set

from ..registry.strategy_registry import StrategyRegistry, StrategyLike

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class StrategyIntent:
    """
    Intent에 Strategy Context를 붙인 래퍼.
    Execution Loop는 최종적으로 `intent`만 받도록 유지한다.
    """
    strategy_id: str
    strategy_name: str
    intent: Any  # runtime.execution.models.intent.Intent 를 직접 import하지 않음(결합 최소화)


class StrategyMultiplexer:
    """
    Phase 6: 다중 Strategy를 순회하며 Intent를 수집.
    - 전략 간 상호 인지 금지
    - 단일 전략 실패는 전체 실패로 전파하지 않음
    """

    def __init__(self, registry: StrategyRegistry) -> None:
        self._registry = registry
        self._disabled_prefixes: Set[str] = set()

    def set_engine_state(
        self, *, scalp_enabled: bool = True, swing_enabled: bool = True
    ) -> None:
        """Operating State 기반 엔진 활성화/비활성화."""
        self._disabled_prefixes.clear()
        if not scalp_enabled:
            self._disabled_prefixes.add("scalp")
        if not swing_enabled:
            self._disabled_prefixes.add("swing")

    def _is_strategy_allowed(self, strategy: StrategyLike) -> bool:
        """disabled_prefixes에 해당하는 전략은 건너뜀."""
        if not self._disabled_prefixes:
            return True
        name = strategy.name.lower()
        return not any(name.startswith(prefix) for prefix in self._disabled_prefixes)

    def collect(self, snapshot: Any) -> List[StrategyIntent]:
        out: List[StrategyIntent] = []

        for s in self._registry.active_strategies():
            if not self._is_strategy_allowed(s):
                _log.info("Strategy %s skipped (disabled prefix)", s.name)
                continue
            try:
                intents = self._generate_intents(s, snapshot)
                for it in intents:
                    out.append(StrategyIntent(s.strategy_id, s.name, it))
            except Exception as e:
                # Phase 6 원칙: 한 Strategy의 실패가 전체를 깨지 않음
                _log.warning("Strategy %s (id=%s) failed: %s", s.name, s.strategy_id, e)
                continue

        return out

    def _generate_intents(self, strategy: StrategyLike, snapshot: Any) -> Sequence[Any]:
        """
        Strategy 구현체의 실제 메서드명에 의존하지 않기 위해
        관용적으로 다음 중 하나를 지원:
        - generate_intents(snapshot)
        - generate(snapshot)
        - __call__(snapshot)
        """
        if hasattr(strategy, "generate_intents"):
            return list(strategy.generate_intents(snapshot))  # type: ignore[attr-defined]
        if hasattr(strategy, "generate"):
            return list(strategy.generate(snapshot))  # type: ignore[attr-defined]
        if callable(strategy):
            return list(strategy(snapshot))  # type: ignore[misc]
        raise AttributeError("Strategy must implement generate_intents/generate or be callable")
