"""
Kiwoom REST API Client

Kiwoom API를 호출하여 주문, 조회, 취소 기능을 제공합니다.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests


_log = logging.getLogger(__name__)


class KiwoomAPIError(Exception):
    """Kiwoom API 에러"""
    pass


class KiwoomAuthError(KiwoomAPIError):
    """Kiwoom 인증 에러"""
    pass


class KiwoomClient:
    """
    Kiwoom REST API Client

    주문 전송, 조회, 취소 기능을 제공합니다.
    """

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        base_url: str,
        account_no: str,
        acnt_prdt_cd: str = "01",
        timeout: int = 10,
    ):
        """
        KiwoomClient 초기화

        Args:
            app_key: Kiwoom API App Key
            app_secret: Kiwoom API App Secret
            base_url: Kiwoom API Base URL
            account_no: 계좌번호
            acnt_prdt_cd: 계좌상품코드 (기본: "01")
            timeout: HTTP 타임아웃 (초)
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url.rstrip("/")
        self.account_no = account_no
        self.acnt_prdt_cd = acnt_prdt_cd
        self.timeout = timeout

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

        _log.info(
            f"KiwoomClient initialized (base_url={self.base_url}, "
            f"account={self.account_no})"
        )

    def _get_access_token(self) -> str:
        """
        Access Token 발급 또는 캐싱된 토큰 반환.

        Returns:
            str: Access Token

        Raises:
            KiwoomAuthError: 인증 실패
        """
        # 캐싱된 토큰이 유효하면 재사용
        if self._access_token and self._token_expires_at:
            if time.time() < self._token_expires_at - 60:  # 1분 여유
                return self._access_token

        # 토큰 발급 (openapi.kiwoom.com: Body secretkey, 응답 token / expires_dt)
        url = urljoin(self.base_url, "/oauth2/token")
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.app_secret,
        }

        try:
            resp = requests.post(
                url, headers=headers, json=payload, timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()

            token = data.get("token") or data.get("access_token")
            if not token:
                raise KiwoomAuthError(f"Token response missing token: {data}")

            self._access_token = token
            # expires_dt: "20241107083713" 형식 → 만료 시각(KST) 파싱 후 캐시
            expires_dt = data.get("expires_dt")
            if expires_dt and isinstance(expires_dt, str) and len(expires_dt) >= 14:
                try:
                    from datetime import datetime
                    # YYYYMMDDHHmmss
                    dt = datetime(
                        int(expires_dt[0:4]), int(expires_dt[4:6]), int(expires_dt[6:8]),
                        int(expires_dt[8:10]), int(expires_dt[10:12]), int(expires_dt[12:14]),
                    )
                    self._token_expires_at = dt.timestamp()
                except (ValueError, IndexError):
                    self._token_expires_at = time.time() + 82800
            else:
                self._token_expires_at = time.time() + 82800

            _log.info("Kiwoom access token acquired")
            return self._access_token

        except requests.RequestException as e:
            _log.error(f"Failed to get Kiwoom access token: {e}")
            raise KiwoomAuthError(f"Token acquisition failed: {e}") from e

    def _make_signature(self, path: str, body: Dict[str, Any]) -> str:
        """
        API 요청 서명 생성 (HMAC-SHA256)

        Args:
            path: API 경로 (예: "/api/v1/order")
            body: 요청 Body

        Returns:
            str: Signature (hex)
        """
        body_str = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        message = f"{path}{body_str}"
        signature = hmac.new(
            self.app_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        api_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Kiwoom API 공통 요청.

        주문/조회/취소는 POST /api/dostk/ordr + Header api-id (kt10000~kt10003).
        """
        url = urljoin(self.base_url, path)
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {self._get_access_token()}",
            "appkey": self.app_key,
        }
        if api_id:
            headers["api-id"] = api_id

        # 서명: 스펙 확정 전까지 선택 적용 (일부 API만 요구할 수 있음)
        if method.upper() == "POST" and body and not api_id:
            headers["signature"] = self._make_signature(path, body)

        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body else None,
                params=params if params else None,
                timeout=self.timeout,
            )

            # HTTP 상태 코드 확인
            if resp.status_code >= 400:
                _log.error(
                    f"Kiwoom API error: {method} {path} -> {resp.status_code} {resp.text}"
                )
                raise KiwoomAPIError(
                    f"HTTP {resp.status_code}: {resp.text}"
                )

            data = resp.json()

            # API 응답 코드 확인
            return_code = data.get("return_code") or data.get("rt_cd")
            if return_code and str(return_code) != "0":
                return_msg = data.get("return_msg") or data.get("msg1", "Unknown error")
                _log.warning(
                    f"Kiwoom API returned non-zero code: {return_code} - {return_msg}"
                )
                # 에러지만 응답은 반환 (caller에서 처리)

            return data

        except requests.RequestException as e:
            _log.error(f"Kiwoom API request failed: {method} {path} -> {e}")
            raise KiwoomAPIError(f"Request failed: {e}") from e

    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        주문 전송. openapi.kiwoom.com: POST /api/dostk/ordr, Header api-id: kt10000(매수)/kt10001(매도).
        payload에 _api_id가 있으면 헤더로 사용 후 body에서 제거.
        """
        body = dict(payload)
        api_id = body.pop("_api_id", None) or "kt10000"
        _log.info("Placing Kiwoom order: api_id=%s, stk_cd=%s", api_id, body.get("stk_cd"))
        return self._request("POST", "/api/dostk/ordr", body=body, api_id=api_id)

    def get_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        주문 조회. openapi.kiwoom.com: POST /api/dostk/ordr, api-id: kt10002.
        """
        order_id = params.get("order_id") or params.get("ord_no")
        _log.info("Getting Kiwoom order: %s", order_id)
        body = {"ord_no": order_id}
        return self._request("POST", "/api/dostk/ordr", body=body, api_id="kt10002")

    def cancel_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        주문 취소. openapi.kiwoom.com: POST /api/dostk/ordr, api-id: kt10003.
        """
        order_id = params.get("order_id") or params.get("ord_no")
        _log.info("Canceling Kiwoom order: %s", order_id)
        body = {"ord_no": order_id}
        return self._request("POST", "/api/dostk/ordr", body=body, api_id="kt10003")

    def get_balance(self) -> Dict[str, Any]:
        """
        계좌 잔고 조회

        Returns:
            Dict[str, Any]: 잔고 정보
        """
        _log.info("Getting Kiwoom account balance")
        params = {
            "account_no": self.account_no,
            "acnt_prdt_cd": self.acnt_prdt_cd,
        }
        return self._request("GET", "/api/v1/balance", params=params)

    def get_positions(self) -> Dict[str, Any]:
        """
        보유 포지션 조회

        Returns:
            Dict[str, Any]: 포지션 정보
        """
        _log.info("Getting Kiwoom positions")
        params = {
            "account_no": self.account_no,
            "acnt_prdt_cd": self.acnt_prdt_cd,
        }
        return self._request("GET", "/api/v1/positions", params=params)
