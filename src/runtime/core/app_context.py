from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AppContext:
    """
    전역 Runtime Context
    """
    runtime_flags: Dict[str, Any] = field(default_factory=dict)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)

    _observer: Optional[Any] = field(default=None, init=False, repr=False)

    def set_observer(self, observer: Any) -> None:
        self._observer = observer

    @property
    def observer(self) -> Any:
        if self._observer is None:
            raise RuntimeError("Observer is not registered in AppContext")
        return self._observer
