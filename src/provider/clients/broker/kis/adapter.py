"""
runtime.broker.kis.adapter

KIS BrokerAdapter implementation (Phase 2).

Responsibilities:
- Invoke KIS OAuth2 authentication
- Deliver AccessTokenPayload to Runtime TokenCache

Hard constraints:
- Adapter is stateless
- No token caching
- No expiry 판단
"""

from src.provider.clients.broker.base import (
    BrokerAdapter,
    AccessTokenPayload,
)
from src.provider.clients.broker.kis.auth import request_access_token
from src.provider.clients.auth.token_cache import TokenCache


class KISBrokerAdapter(BrokerAdapter):
    """
    Phase 2 adapter:
    - authentication only
    - execution / order APIs are out of scope
    """

    def __init__(self, token_cache: TokenCache) -> None:
        self._token_cache = token_cache

    @property
    def broker_name(self) -> str:
        return "KIS"

    def authenticate(self) -> AccessTokenPayload:
        """
        Authenticate with KIS and update Runtime TokenCache.
        """
        payload = request_access_token()

        # Runtime owns state
        self._token_cache.update_from_payload(
            access_token=payload.access_token,
            token_type=payload.token_type,
            expires_in=payload.expires_in,
            issued_at=payload.issued_at,
            scope=payload.scope,
        )

        return payload
