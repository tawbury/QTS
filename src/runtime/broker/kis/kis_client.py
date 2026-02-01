"""
KIS REST API Client

한국투자증권(Korea Investment & Securities) API를 호출하여
주문, 조회, 취소 기능을 제공합니다.

KIS API 특징:
- OAuth2.0 토큰 인증
- Hashkey 생성 (POST 요청 시 필수)
- tr_id 헤더 (거래 ID)
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


class KISAPIError(Exception):
    """KIS API 에러"""
    pass


class KISAuthError(KISAPIError):
    """KIS 인증 에러"""
    pass


class KISClient:
    """
    KIS REST API Client

    주문 전송, 조회, 취소, 잔고 조회 등을 제공합니다.
    """

    # KIS API tr_id (open-trading-api order_cash 기준: 0011=매도, 0012=매수)
    TR_ID_BUY_VTS = "VTTC0012U"   # 모의투자 매수
    TR_ID_SELL_VTS = "VTTC0011U"  # 모의투자 매도
    TR_ID_BUY_REAL = "TTTC0012U"  # 실전투자 매수
    TR_ID_SELL_REAL = "TTTC0011U"  # 실전투자 매도

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        base_url: str,
        account_no: str,
        acnt_prdt_cd: str = "01",
        trading_mode: str = "VTS",
        timeout: int = 10,
    ):
        """
        KISClient 초기화

        Args:
            app_key: KIS API App Key
            app_secret: KIS API App Secret
            base_url: KIS API Base URL
            account_no: 계좌번호
            acnt_prdt_cd: 계좌상품코드 (기본: "01")
            trading_mode: "VTS" 또는 "REAL"
            timeout: HTTP 타임아웃 (초)
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url.rstrip("/")
        self.account_no = account_no
        self.acnt_prdt_cd = acnt_prdt_cd
        self.trading_mode = trading_mode.upper()
        self.timeout = timeout

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

        _log.info(
            f"KISClient initialized (mode={self.trading_mode}, "
            f"base_url={self.base_url}, account={self.account_no})"
        )

    def _get_access_token(self) -> str:
        """
        Access Token 발급 또는 캐싱된 토큰 반환.

        Returns:
            str: Access Token

        Raises:
            KISAuthError: 인증 실패
        """
        # 캐싱된 토큰이 유효하면 재사용
        if self._access_token and self._token_expires_at:
            if time.time() < self._token_expires_at - 60:  # 1분 여유
                return self._access_token

        # 토큰 발급
        url = urljoin(self.base_url, "/oauth2/tokenP")
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            if "access_token" not in data:
                raise KISAuthError(f"Token response missing access_token: {data}")

            self._access_token = data["access_token"]
            # 토큰 만료 시간 (기본 1일, 안전하게 23시간으로 설정)
            expires_in = data.get("expires_in", 86400)
            self._token_expires_at = time.time() + min(expires_in, 82800)

            _log.info("KIS access token acquired")
            return self._access_token

        except requests.RequestException as e:
            _log.error(f"Failed to get KIS access token: {e}")
            raise KISAuthError(f"Token acquisition failed: {e}") from e

    def _get_hashkey(self, body: Dict[str, Any]) -> str:
        """
        KIS API Hashkey 생성 (POST 요청 시 필수).

        Args:
            body: 요청 Body

        Returns:
            str: Hashkey
        """
        url = urljoin(self.base_url, "/uapi/hashkey")
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        try:
            resp = requests.post(url, json=body, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            if "HASH" not in data:
                raise KISAPIError(f"Hashkey response missing HASH: {data}")

            return data["HASH"]

        except requests.RequestException as e:
            _log.error(f"Failed to get KIS hashkey: {e}")
            raise KISAPIError(f"Hashkey generation failed: {e}") from e

    def _request(
        self,
        method: str,
        path: str,
        tr_id: str,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        KIS API 공통 요청

        Args:
            method: HTTP 메서드 (GET, POST, etc.)
            path: API 경로
            tr_id: 거래 ID (예: VTTC0802U)
            body: Request Body (POST용)
            params: Query Parameters (GET용)

        Returns:
            Dict[str, Any]: API 응답

        Raises:
            KISAPIError: API 호출 실패
        """
        url = urljoin(self.base_url, path)
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self._get_access_token()}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
        }

        # Hashkey 추가 (POST 요청 시)
        if method.upper() == "POST" and body:
            hashkey = self._get_hashkey(body)
            headers["hashkey"] = hashkey

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
                    f"KIS API error: {method} {path} (tr_id={tr_id}) -> "
                    f"{resp.status_code} {resp.text}"
                )
                raise KISAPIError(f"HTTP {resp.status_code}: {resp.text}")

            data = resp.json()

            # API 응답 코드 확인
            rt_cd = data.get("rt_cd")
            if rt_cd and str(rt_cd) != "0":
                msg1 = data.get("msg1", "Unknown error")
                _log.warning(f"KIS API returned non-zero code: {rt_cd} - {msg1}")
                # 에러지만 응답은 반환 (caller에서 처리)

            return data

        except requests.RequestException as e:
            _log.error(f"KIS API request failed: {method} {path} -> {e}")
            raise KISAPIError(f"Request failed: {e}") from e

    # KIS order-cash Body 키 (공식 샘플: 대문자만 전송)
    _ORDER_BODY_KEYS = frozenset({
        "CANO", "ACNT_PRDT_CD", "PDNO", "ORD_DVSN", "ORD_QTY", "ORD_UNPR",
        "EXCG_ID_DVSN_CD", "SLL_TYPE", "CNDT_PRIC",
    })

    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        주문 전송. open-trading-api order_cash: tr_id 0011/0012, Body 대문자 키만.
        """
        side = (payload.get("side") or "BUY")
        if hasattr(side, "value"):
            side = side.value
        side = str(side).upper()
        symbol = payload.get("symbol") or payload.get("PDNO")

        # tr_id 선택 (VTS vs REAL, BUY vs SELL)
        if self.trading_mode == "VTS":
            tr_id = self.TR_ID_BUY_VTS if side == "BUY" else self.TR_ID_SELL_VTS
        else:
            tr_id = self.TR_ID_BUY_REAL if side == "BUY" else self.TR_ID_SELL_REAL

        body = {k: v for k, v in payload.items() if k in self._ORDER_BODY_KEYS}
        _log.info("Placing KIS order: %s %s (tr_id=%s)", side, symbol, tr_id)
        return self._request("POST", "/uapi/domestic-stock/v1/trading/order-cash", tr_id, body=body)

    def get_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        주문 조회

        Args:
            params: 조회 파라미터 (order_id 등)

        Returns:
            Dict[str, Any]: API 응답
        """
        order_id = params.get("order_id")
        _log.info(f"Getting KIS order: {order_id}")

        # 주문 조회 tr_id (VTS/REAL 공통)
        tr_id = "VTTC8001R" if self.trading_mode == "VTS" else "TTTC8001R"

        return self._request("GET", "/uapi/domestic-stock/v1/trading/inquire-daily-ccld", tr_id, params=params)

    def cancel_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        주문 취소

        Args:
            params: 취소 파라미터 (order_id 등)

        Returns:
            Dict[str, Any]: API 응답
        """
        order_id = params.get("order_id")
        _log.info(f"Canceling KIS order: {order_id}")

        # 주문 취소 tr_id
        tr_id = "VTTC0803U" if self.trading_mode == "VTS" else "TTTC0803U"

        # 취소는 POST 요청 (body에 주문번호 등 포함)
        body = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "KRX_FWDG_ORD_ORGNO": params.get("org_no", ""),
            "ORGN_ODNO": order_id,
            "ORD_DVSN": "00",  # 주문구분 (00: 지정가)
            "RVSE_CNCL_DVSN_CD": "02",  # 정정취소구분 (02: 취소)
            "ORD_QTY": "0",
        }

        return self._request("POST", "/uapi/domestic-stock/v1/trading/order-rvsecncl", tr_id, body=body)

    def get_balance(self) -> Dict[str, Any]:
        """
        계좌 잔고 조회

        Returns:
            Dict[str, Any]: 잔고 정보
        """
        _log.info("Getting KIS account balance")

        tr_id = "VTTC8434R" if self.trading_mode == "VTS" else "TTTC8434R"

        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        return self._request("GET", "/uapi/domestic-stock/v1/trading/inquire-balance", tr_id, params=params)

    def get_positions(self) -> Dict[str, Any]:
        """
        보유 포지션 조회 (잔고 조회와 동일)

        Returns:
            Dict[str, Any]: 포지션 정보
        """
        return self.get_balance()
