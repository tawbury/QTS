"""
Kiwoom REST API integration (META-240523-03).

- payload_mapping: OrderRequest/Response normalization, error→Fail-Safe mapping.
- auth: OAuth 2.0 (client credentials). Stateless adapter, TokenCache 소유는 Runtime.
- OrderAdapter: adapters/kiwoom_adapter.KiwoomOrderAdapter (BaseBrokerAdapter 상속).
"""

from runtime.broker.kiwoom.payload_mapping import (
    KIWOOM_ERROR_TO_SAFETY,
    KIWOOM_STATUS_TO_ORDER_STATUS,
    build_kiwoom_order_payload,
    map_broker_error_to_safety as kiwoom_map_broker_error_to_safety,
    parse_kiwoom_place_response,
    raw_to_order_response as kiwoom_raw_to_order_response,
)

__all__ = [
    "KIWOOM_ERROR_TO_SAFETY",
    "KIWOOM_STATUS_TO_ORDER_STATUS",
    "build_kiwoom_order_payload",
    "parse_kiwoom_place_response",
    "kiwoom_raw_to_order_response",
    "kiwoom_map_broker_error_to_safety",
]
