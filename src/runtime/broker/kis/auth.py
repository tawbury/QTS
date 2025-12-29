from __future__ import annotations

"""
runtime.broker.kis.auth

KIS OAuth2 authentication (stateless).

Responsibilities (Phase 2):
- Read MODE (VTS / REAL) from environment
- Build OAuth2 token request
- Call /oauth2/tokenP
- Return AccessTokenPayload

Hard constraints:
- NO token caching
- NO runtime.auth import
- NO persistence
"""

import os
import requests
from datetime import datetime, timezone
from typing import Dict, Any

from runtime.broker.base import (
    AccessTokenPayload,
    BrokerAuthError,
    BrokerConfigError,
)


# =========================
# Environment helpers
# =========================

def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise BrokerConfigError(f"Missing required environment variable: {key}")
    return value


def _load_kis_env() -> Dict[str, str]:
    """
    Required env variables (Phase 2):

    MODE=VTS|REAL

    KIS_APP_KEY
    KIS_APP_SECRET

    KIS_BASE_URL_VTS
    KIS_BASE_URL_REAL
    """
    mode = _require_env("MODE").upper()
    if mode not in ("VTS", "REAL"):
        raise BrokerConfigError("MODE must be either 'VTS' or 'REAL'")

    app_key = _require_env("KIS_APP_KEY")
    app_secret = _require_env("KIS_APP_SECRET")

    if mode == "VTS":
        base_url = _require_env("KIS_BASE_URL_VTS")
    else:
        base_url = _require_env("KIS_BASE_URL_REAL")

    return {
        "mode": mode,
        "app_key": app_key,
        "app_secret": app_secret,
        "base_url": base_url.rstrip("/"),
    }


# =========================
# OAuth2 request
# =========================

def request_access_token(timeout: int = 10) -> AccessTokenPayload:
    """
    Perform OAuth2 token request to KIS.

    Raises:
    - BrokerConfigError
    - BrokerAuthError
    """
    cfg = _load_kis_env()

    url = f"{cfg['base_url']}/oauth2/tokenP"
    payload = {
        "grant_type": "client_credentials",
        "appkey": cfg["app_key"],
        "appsecret": cfg["app_secret"],
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
    except Exception as e:
        raise BrokerAuthError(f"KIS auth request failed: {e}") from e

    if resp.status_code != 200:
        raise BrokerAuthError(
            f"KIS auth failed (HTTP {resp.status_code}): {resp.text}"
        )

    try:
        data: Dict[str, Any] = resp.json()
    except Exception as e:
        raise BrokerAuthError("KIS auth response is not valid JSON") from e

    # Minimal validation
    if "access_token" not in data or "expires_in" not in data:
        raise BrokerAuthError(f"Invalid KIS auth response: {data}")

    return AccessTokenPayload(
        access_token=data["access_token"],
        token_type=data.get("token_type", "Bearer"),
        expires_in=int(data["expires_in"]),
        issued_at=datetime.now(timezone.utc),
        scope=data.get("scope"),
        raw=data,
    )
