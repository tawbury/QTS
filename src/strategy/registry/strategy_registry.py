from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Protocol


class StrategyLike(Protocol):
    @property
    def strategy_id(self) -> str: ...
    @property
    def name(self) -> str: ...
    def is_enabled(self) -> bool: ...


@dataclass(frozen=True)
class StrategyRef:
    strategy_id: str
    name: str


class StrategyRegistry:
    """
    Phase 6: 전략 다중화의 '등록/활성 상태'만 책임진다.
    실행/리스크/루프 관여 금지.
    """

    def __init__(self) -> None:
        self._items: Dict[str, StrategyLike] = {}

    def register(self, strategy: StrategyLike) -> None:
        sid = strategy.strategy_id
        if not sid or not isinstance(sid, str):
            raise ValueError("strategy.strategy_id must be non-empty str")
        self._items[sid] = strategy

    def unregister(self, strategy_id: str) -> None:
        self._items.pop(strategy_id, None)

    def get(self, strategy_id: str) -> Optional[StrategyLike]:
        return self._items.get(strategy_id)

    def list_all(self) -> List[StrategyRef]:
        return [StrategyRef(s.strategy_id, s.name) for s in self._items.values()]

    def active_strategies(self) -> List[StrategyLike]:
        return [s for s in self._items.values() if s.is_enabled()]

    def __len__(self) -> int:
        return len(self._items)
