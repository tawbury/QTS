from __future__ import annotations

import pytest

from src.shared.timezone_utils import KST
from runtime.broker.kis.auth import request_access_token
from runtime.broker.base import BrokerAuthError, BrokerConfigError


class DummyResponse:
    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json = json_data
        self.text = str(json_data)

    def json(self):
        return self._json


def setup_env(monkeypatch):
    """.env 스키마: KIS_MODE + KIS_VTS_* (모의) 또는 KIS_REAL_* (실전)."""
    monkeypatch.setenv("KIS_MODE", "KIS_VTS")
    monkeypatch.setenv("KIS_VTS_APP_KEY", "dummy_key")
    monkeypatch.setenv("KIS_VTS_APP_SECRET", "dummy_secret")
    monkeypatch.setenv("KIS_VTS_BASE_URL", "https://vts.kis.test")


def test_kis_auth_success(monkeypatch):
    setup_env(monkeypatch)

    def mock_post(url, json, timeout):
        assert url.endswith("/oauth2/tokenP")
        return DummyResponse(
            200,
            {
                "access_token": "abc123",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
        )

    monkeypatch.setattr("requests.post", mock_post)

    payload = request_access_token()

    assert payload.access_token == "abc123"
    assert payload.token_type == "Bearer"
    assert payload.expires_in == 3600
    assert payload.issued_at.tzinfo == KST


def test_kis_auth_http_error(monkeypatch):
    setup_env(monkeypatch)

    def mock_post(url, json, timeout):
        return DummyResponse(401, {"error": "unauthorized"})

    monkeypatch.setattr("requests.post", mock_post)

    with pytest.raises(BrokerAuthError):
        request_access_token()


def test_kis_auth_missing_env(monkeypatch):
    """KIS_VTS_* 미설정 시 BrokerConfigError."""
    monkeypatch.delenv("KIS_MODE", raising=False)
    monkeypatch.delenv("KIS_VTS_APP_KEY", raising=False)

    with pytest.raises(BrokerConfigError):
        request_access_token()
