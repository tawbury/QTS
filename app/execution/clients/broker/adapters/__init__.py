"""
Multi-Broker Adapter layer (Phase 8).

- BaseBrokerAdapter: standard interface (OrderAdapter + broker_id).
- Registry: register_broker(broker_id, factory), get_broker(broker_id, **kwargs).
- KIS: registered via runtime.broker.adapters.kis_adapter.KISOrderAdapter.
- Kiwoom: KiwoomOrderAdapter (adapters/kiwoom_adapter).
- get_broker_for_config: select adapter by BrokerConfig (primary + optional fallback).
"""

from __future__ import annotations

from app.execution.clients.broker.adapters.base_adapter import BaseBrokerAdapter
from app.execution.clients.broker.adapters.registry import (
    get_broker,
    has_broker,
    list_broker_ids,
    register_broker,
)
from app.execution.clients.broker.adapters.kis_adapter import KISOrderAdapter
from app.execution.clients.broker.adapters.kiwoom_adapter import KiwoomOrderAdapter
from app.execution.clients.broker.adapters.protocols import OrderClientProtocol
from app.execution.clients.broker.config import BrokerConfig
from app.execution.clients.broker.order_base import OrderAdapter


def get_broker_for_config(config: BrokerConfig) -> OrderAdapter:
    """
    Return OrderAdapter for config (primary broker).
    On failure, optional fallback_broker_id can be used by caller.
    """
    kwargs = config.to_kwargs()
    return get_broker(config.broker_id, **kwargs)


__all__ = [
    "BaseBrokerAdapter",
    "BrokerConfig",
    "KISOrderAdapter",
    "KiwoomOrderAdapter",
    "OrderClientProtocol",
    "get_broker",
    "get_broker_for_config",
    "has_broker",
    "list_broker_ids",
    "register_broker",
]
