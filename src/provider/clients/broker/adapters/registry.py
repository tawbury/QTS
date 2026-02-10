"""
Broker adapter registry: register and select by broker_id (Phase 8).
"""
from __future__ import annotations
from typing import Any, Callable, Dict, Any
from src.provider.clients.broker.order_base import OrderAdapter

# 전역 레지스트리
_BROKER_REGISTRY: Dict[str, Callable[..., OrderAdapter]] = {}
_DEFAULTS_REGISTERED = False

def get_broker_adapter(broker_id: str, config: Any = None, **kwargs: Any) -> OrderAdapter:
    _ensure_defaults_registered()
    
    # kis_VTS 등으로 들어올 경우 앞글자만 따서 kis로 매핑
    normalized_id = broker_id.lower().split('_')[0] 
    
    if normalized_id not in _BROKER_REGISTRY:
        if broker_id not in _BROKER_REGISTRY:
            raise KeyError(f"Unknown broker_id: {broker_id}. Registered: {list_broker_ids()}")
        normalized_id = broker_id

    factory = _BROKER_REGISTRY[normalized_id]
    
    # [수정 핵심] config가 객체(BrokerConfig)인 경우와 딕셔너리인 경우 모두 대응
    if config is not None:
        acc_no = getattr(config, "account_no", "") or getattr(config, "acnt_no", "")
        if not acc_no and isinstance(config, dict):
            acc_no = config.get("account_no", config.get("acnt_no", ""))
            
        prod_cd = getattr(config, "acnt_prdt_cd", "01")
        if prod_cd == "01" and isinstance(config, dict):
            prod_cd = config.get("acnt_prdt_cd", "01")

        if normalized_id == "kis":
            return factory(client=None, acnt_no=acc_no, acnt_prdt_cd=prod_cd)
        elif normalized_id == "kiwoom":
            mkt = getattr(config, "market", "0")
            if mkt == "0" and isinstance(config, dict):
                mkt = config.get("market", "0")
            return factory(client=None, acnt_no=acc_no, market=mkt)
            
    return factory(**kwargs)

def _ensure_defaults_registered() -> None:
    global _DEFAULTS_REGISTERED
    if _DEFAULTS_REGISTERED: return
    try:
        from src.provider.clients.broker.adapters.kis_adapter import KISOrderAdapter
        from src.provider.clients.broker.adapters.kiwoom_adapter import KiwoomOrderAdapter
        register_broker("kis", lambda **k: KISOrderAdapter(**k))
        register_broker("kiwoom", lambda **k: KiwoomOrderAdapter(**k))
        _DEFAULTS_REGISTERED = True
    except ImportError: pass

def register_broker(broker_id: str, factory: Callable[..., OrderAdapter]) -> None:
    _BROKER_REGISTRY[broker_id] = factory

def list_broker_ids() -> tuple[str, ...]:
    _ensure_defaults_registered()
    return tuple(_BROKER_REGISTRY.keys())

# [중요] 임포트 에러 해결을 위한 함수 추가
def has_broker(broker_id: str) -> bool:
    """Return True if broker_id is registered."""
    _ensure_defaults_registered()
    normalized_id = broker_id.lower().split('_')[0]
    return normalized_id in _BROKER_REGISTRY or broker_id in _BROKER_REGISTRY

def get_broker(broker_id: str, config: Any = None, **kwargs: Any) -> OrderAdapter:
    return get_broker_adapter(broker_id, config, **kwargs)