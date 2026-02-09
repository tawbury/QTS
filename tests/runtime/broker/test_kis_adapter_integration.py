from __future__ import annotations

from datetime import datetime, timedelta
import pytest

from src.shared.timezone_utils import now_kst
from runtime.auth.token_cache import TokenCache
from runtime.broker.kis.adapter import KISBrokerAdapter
from runtime.broker.base import AccessTokenPayload


def test_kis_adapter_updates_runtime_token_cache(monkeypatch):
    """
    Adapter ↔ Runtime integration test.

    Flow:
    - Adapter.authenticate()
    - TokenCache updated
    - Runtime can retrieve valid token
    """

    now = now_kst()

    def mock_request_access_token():
        return AccessTokenPayload(
            access_token="integration_token",
            token_type="Bearer",
            expires_in=3600,
            issued_at=now,
        )

    # mock auth call
    monkeypatch.setattr(
        "runtime.broker.kis.adapter.request_access_token",
        mock_request_access_token,
    )

    cache = TokenCache(refresh_skew_seconds=30)
    adapter = KISBrokerAdapter(token_cache=cache)

    payload = adapter.authenticate()

    assert payload.access_token == "integration_token"

    # Runtime side verification
    assert cache.needs_refresh(now=now) is False
    assert cache.get_valid_token(now=now) == "integration_token"
    assert cache.get_authorization_header(now=now) == "Bearer integration_token"


def test_kis_adapter_refresh_needed_after_expiry(monkeypatch):
    now = now_kst()

    def mock_request_access_token():
        return AccessTokenPayload(
            access_token="short_lived",
            token_type="Bearer",
            expires_in=1,
            issued_at=now,
        )

    monkeypatch.setattr(
        "runtime.broker.kis.adapter.request_access_token",
        mock_request_access_token,
    )

    cache = TokenCache(refresh_skew_seconds=0)
    adapter = KISBrokerAdapter(token_cache=cache)

    adapter.authenticate()

    later = now + timedelta(seconds=5)
    assert cache.needs_refresh(now=later) is True
