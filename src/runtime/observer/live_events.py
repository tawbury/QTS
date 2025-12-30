from __future__ import annotations
from typing import Any, Dict


def emit(observer: Any, event_type: str, payload: Dict) -> None:
    if observer is None:
        return
    if hasattr(observer, "emit"):
        observer.emit(event_type, payload)
    elif hasattr(observer, "on_event"):
        observer.on_event(event_type, payload)
