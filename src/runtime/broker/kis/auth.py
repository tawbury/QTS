from __future__ import annotations

"""
runtime.broker.kis.auth

KIS OAuth2 authentication (stateless).

Responsibilities (Phase 2):
- Read KIS_MODE (KIS_VTS / KIS_REAL) or MODE from environment; .env와 동일 스키마.
- Build OAuth2 token request
- Call /oauth2/tokenP
- Return AccessTokenPayload

Env schema (모의/실전 완전 분리, .env 기준):
- KIS_MODE = "KIS_VTS" | "KIS_REAL"
- 모의: KIS_VTS_APP_KEY, KIS_VTS_APP_SECRET, KIS_VTS_BASE_URL
- 실전: KIS_REAL_APP_KEY, KIS_REAL_APP_SECRET, KIS_REAL_BASE_URL

Hard constraints:
- NO token caching
- NO runtime.auth import
- NO persistence
"""

import os
import requests
from datetime import datetime
from typing import Dict, Any

from shared.timezone_utils import now_kst

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
    .env 스키마와 동일: KIS_MODE로 모의/실전 선택 후 해당 접두사 환경변수 사용.

    KIS_MODE = "KIS_VTS" | "KIS_REAL" (기본 KIS_VTS)
    모의: KIS_VTS_APP_KEY, KIS_VTS_APP_SECRET, KIS_VTS_BASE_URL
    실전: KIS_REAL_APP_KEY, KIS_REAL_APP_SECRET, KIS_REAL_BASE_URL

    하위 호환: MODE=VTS|REAL 이 있으면 KIS_MODE 없을 때 사용.
    """
    mode_value = (os.getenv("KIS_MODE") or os.getenv("MODE") or "KIS_VTS").strip().upper()
    if "REAL" in mode_value:
        trading_mode: str = "REAL"
    else:
        trading_mode = "VTS"

    prefix = f"KIS_{trading_mode}_"
    app_key = os.getenv(f"{prefix}APP_KEY")
    app_secret = os.getenv(f"{prefix}APP_SECRET")
    base_url = os.getenv(f"{prefix}BASE_URL")

    if not app_key:
        raise BrokerConfigError(f"Missing required env: {prefix}APP_KEY")
    if not app_secret:
        raise BrokerConfigError(f"Missing required env: {prefix}APP_SECRET")
    if not base_url:
        raise BrokerConfigError(f"Missing required env: {prefix}BASE_URL")

    return {
        "mode": trading_mode,
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
        issued_at=now_kst(),
        scope=data.get("scope"),
        raw=data,
    )
