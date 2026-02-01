"""
Broker adapter registry: register and select by broker_id (Phase 8).

Arch §10.1: 공통 인터페이스 기반 브로커 추가 절차 — Adapter 등록 및 선택.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from runtime.broker.order_base import OrderAdapter


# broker_id -> factory(**kwargs) -> OrderAdapter
_BROKER_REGISTRY: Dict[str, Callable[..., OrderAdapter]] = {}
_DEFAULTS_REGISTERED = False


def _ensure_defaults_registered() -> None:
    global _DEFAULTS_REGISTERED
    if _DEFAULTS_REGISTERED or "kis" in _BROKER_REGISTRY:
        _DEFAULTS_REGISTERED = True
        return
    from runtime.broker.kis.order_adapter import KISOrderAdapter
    from runtime.broker.adapters.kiwoom_adapter import KiwoomOrderAdapter

    def _kis_factory(*, broker, cano="", acnt_prdt_cd="01"):
        return KISOrderAdapter(broker, cano=cano, acnt_prdt_cd=acnt_prdt_cd)

    def _kiwoom_factory(*, client=None, acnt_no="", market="0", **kwargs):
        return KiwoomOrderAdapter(client=client, acnt_no=acnt_no, market=market)

    register_broker("kis", _kis_factory)
    register_broker("kiwoom", _kiwoom_factory)
    _DEFAULTS_REGISTERED = True


def register_broker(broker_id: str, factory: Callable[..., OrderAdapter]) -> None:
    """Register a broker adapter factory. factory(**kwargs) must return an OrderAdapter."""
    _BROKER_REGISTRY[broker_id] = factory


def get_broker(broker_id: str, **kwargs: Any) -> OrderAdapter:
    """Return an OrderAdapter for the given broker_id. Raises KeyError if unknown."""
    _ensure_defaults_registered()
    if broker_id not in _BROKER_REGISTRY:
        raise KeyError(f"Unknown broker_id: {broker_id}. Registered: {list_broker_ids()}")
    return _BROKER_REGISTRY[broker_id](**kwargs)


def list_broker_ids() -> tuple[str, ...]:
    """Return registered broker ids."""
    _ensure_defaults_registered()
    return tuple(_BROKER_REGISTRY.keys())


def has_broker(broker_id: str) -> bool:
    """Return True if broker_id is registered."""
    _ensure_defaults_registered()
    return broker_id in _BROKER_REGISTRY
