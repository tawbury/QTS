"""
Broker configuration for Multi-Broker selection (Phase 8).

Config 시트/환경 기반 broker_id 및 optional fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class BrokerConfig:
    """
    Broker selection config.

    - broker_id: primary broker (e.g. 'kis', 'kiwoom').
    - fallback_broker_id: optional; used when primary fails (future).
    - kwargs: passed to get_broker(broker_id, **kwargs).
    """

    broker_id: str
    fallback_broker_id: Optional[str] = None
    kwargs: tuple[tuple[str, Any], ...] = ()

    def to_kwargs(self) -> dict[str, Any]:
        """Return kwargs dict for get_broker(broker_id, **kwargs)."""
        return dict(self.kwargs)


def broker_id_from_config(
    sheet_broker_id: Optional[str] = None,
    env_broker_id: Optional[str] = None,
    default: str = "kis",
) -> str:
    """
    Resolve broker_id from config sheet and/or env.

    Precedence: env_broker_id > sheet_broker_id > default.
    """
    return (env_broker_id or sheet_broker_id or default).strip().lower() or default
