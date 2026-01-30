from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AppContext:
    """
    전역 Runtime Context
    """
    runtime_flags: Dict[str, Any] = field(default_factory=dict)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
