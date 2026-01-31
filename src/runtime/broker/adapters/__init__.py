"""
Multi-Broker Adapter layer (Phase 8).

- BaseBrokerAdapter: standard interface (OrderAdapter + broker_id).
- Registry: register_broker(broker_id, factory), get_broker(broker_id, **kwargs).
- KIS: registered via runtime.broker.kis.order_adapter.KISOrderAdapter.
- Kiwoom: skeleton adapter for extension.
- get_broker_for_config: select adapter by BrokerConfig (primary + optional fallback).
"""

from __future__ import annotations

from runtime.broker.adapters.base_adapter import BaseBrokerAdapter
from runtime.broker.adapters.registry import (
    get_broker,
    has_broker,
    list_broker_ids,
    register_broker,
)
from runtime.broker.adapters.kiwoom_adapter import KiwoomOrderAdapter
from runtime.broker.config import BrokerConfig
from runtime.broker.order_base import OrderAdapter


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
    "KiwoomOrderAdapter",
    "get_broker",
    "get_broker_for_config",
    "has_broker",
    "list_broker_ids",
    "register_broker",
]
