from __future__ import annotations

from datetime import timezone
import pytest

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
    monkeypatch.setenv("MODE", "VTS")
    monkeypatch.setenv("KIS_APP_KEY", "dummy_key")
    monkeypatch.setenv("KIS_APP_SECRET", "dummy_secret")
    monkeypatch.setenv("KIS_BASE_URL_VTS", "https://vts.kis.test")
    monkeypatch.setenv("KIS_BASE_URL_REAL", "https://real.kis.test")


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
    assert payload.issued_at.tzinfo == timezone.utc


def test_kis_auth_http_error(monkeypatch):
    setup_env(monkeypatch)

    def mock_post(url, json, timeout):
        return DummyResponse(401, {"error": "unauthorized"})

    monkeypatch.setattr("requests.post", mock_post)

    with pytest.raises(BrokerAuthError):
        request_access_token()


def test_kis_auth_missing_env(monkeypatch):
    monkeypatch.delenv("MODE", raising=False)

    with pytest.raises(BrokerConfigError):
        request_access_token()
