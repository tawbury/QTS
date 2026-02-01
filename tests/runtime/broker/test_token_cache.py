from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from shared.timezone_utils import now_kst
from runtime.auth.token_cache import TokenCache


def kst_now() -> datetime:
    return now_kst()


def test_token_cache_starts_empty_and_needs_refresh() -> None:
    cache = TokenCache()
    assert cache.get_state() is None
    assert cache.needs_refresh() is True

    with pytest.raises(RuntimeError):
        cache.get_valid_token()


def test_token_cache_update_and_get_valid_token() -> None:
    cache = TokenCache(refresh_skew_seconds=30)

    issued_at = kst_now()
    cache.update_from_payload(
        access_token="abc",
        token_type="Bearer",
        expires_in=3600,
        issued_at=issued_at,
        scope=None,
    )

    assert cache.needs_refresh(now=issued_at) is False
    assert cache.get_valid_token(now=issued_at) == "abc"
    assert cache.get_authorization_header(now=issued_at) == "Bearer abc"


def test_token_cache_expired_requires_refresh() -> None:
    cache = TokenCache(refresh_skew_seconds=30)

    issued_at = kst_now() - timedelta(hours=2)
    cache.update_from_payload(
        access_token="abc",
        token_type="Bearer",
        expires_in=60,  # expired long ago
        issued_at=issued_at,
    )

    now = kst_now()
    assert cache.needs_refresh(now=now) is True
    with pytest.raises(RuntimeError):
        cache.get_valid_token(now=now)


def test_token_cache_near_expiry_requires_refresh_by_skew() -> None:
    cache = TokenCache(refresh_skew_seconds=30)

    now = kst_now()
    issued_at = now
    # expires in 20s, within skew(30s) => refresh needed
    cache.update_from_payload(
        access_token="abc",
        token_type="Bearer",
        expires_in=20,
        issued_at=issued_at,
    )

    assert cache.needs_refresh(now=now) is True
    with pytest.raises(RuntimeError):
        cache.get_valid_token(now=now)


def test_token_cache_clear() -> None:
    cache = TokenCache()
    cache.update(
        access_token="abc",
        token_type="Bearer",
        expires_at=kst_now() + timedelta(seconds=3600),
    )
    assert cache.get_state() is not None

    cache.clear()
    assert cache.get_state() is None
    assert cache.needs_refresh() is True
