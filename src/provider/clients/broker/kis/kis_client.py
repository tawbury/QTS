"""
KIS REST API Client

한국투자증권(Korea Investment & Securities) API를 호출하여
주문, 조회, 취소 기능을 제공합니다.

KIS API 특징:
- OAuth2.0 토큰 인증 (1분당 1회 발급 제한: GitHub open-trading-api README)
- 토큰은 파일 캐시로 프로세스 간 재사용 (공식 kis_auth 패턴)
- Hashkey 생성 (POST 요청 시 필수)
- tr_id 헤더 (거래 ID)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests


_log = logging.getLogger(__name__)

# KIS 토큰 발급 제한: 1분당 1회 (https://github.com/koreainvestment/open-trading-api)
_KIS_TOKEN_MIN_INTERVAL_SEC = 60


def _kis_token_cache_path(base_url: str) -> Path:
    """base_url별 토큰 캐시 파일 경로 (VTS/REAL 분리)."""
    safe = re.sub(r"[^\w\-.]", "_", base_url.strip().rstrip("/"))
    return Path(os.path.expanduser("~")) / f".qts_kis_token_{safe}.json"


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

    def _read_token_cache(self) -> Optional[str]:
        """파일 캐시에서 유효한 토큰 읽기 (만료 1분 전까지 재사용)."""
        path = _kis_token_cache_path(self.base_url)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("base_url") != self.base_url:
                return None
            expires_at = data.get("expires_at")
            if expires_at is None or time.time() >= expires_at - 60:
                return None
            token = data.get("token")
            if not token:
                return None
            self._access_token = token
            self._token_expires_at = float(expires_at)
            _log.debug("KIS token loaded from cache")
            return token
        except (OSError, json.JSONDecodeError, TypeError) as e:
            _log.debug("KIS token cache read failed: %s", e)
            return None

    def _write_token_cache(self, token: str, expires_at: float) -> None:
        """발급받은 토큰을 파일 캐시에 저장 (프로세스 간 재사용)."""
        path = _kis_token_cache_path(self.base_url)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    {"token": token, "expires_at": expires_at, "base_url": self.base_url},
                    f,
                )
        except OSError as e:
            _log.debug("KIS token cache write failed: %s", e)

    def _get_access_token(self) -> str:
        """
        Access Token 발급 또는 캐싱된 토큰 반환.

        - 메모리·파일 캐시 유효 시 재사용 (KIS 1분당 1회 발급 제한 준수).
        - 공식 kis_auth 패턴: 토큰 파일 저장 후 재사용.

        Returns:
            str: Access Token

        Raises:
            KISAuthError: 인증 실패
        """
        # 1) 메모리 캐시 유효하면 재사용
        if self._access_token and self._token_expires_at:
            if time.time() < self._token_expires_at - 60:
                return self._access_token

        # 2) 파일 캐시에서 유효한 토큰 있으면 재사용 (다른 프로세스가 발급한 토큰)
        cached = self._read_token_cache()
        if cached:
            return cached

        # 3) 1분당 1회 제한: 마지막 발급 시각 파일 확인 후 필요 시 대기
        cache_path = _kis_token_cache_path(self.base_url)
        path_ts = cache_path.with_suffix(".last_request")
        if path_ts.exists():
            try:
                last = float(path_ts.read_text(encoding="utf-8").strip())
                elapsed = time.time() - last
                if elapsed < _KIS_TOKEN_MIN_INTERVAL_SEC:
                    wait = _KIS_TOKEN_MIN_INTERVAL_SEC - elapsed
                    _log.debug("KIS token rate limit: waiting %.1fs", wait)
                    time.sleep(wait)
            except (OSError, ValueError):
                pass

        # 4) 토큰 발급
        url = urljoin(self.base_url, "/oauth2/tokenP")
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        try:
            try:
                path_ts.write_text(str(time.time()), encoding="utf-8")
            except OSError:
                pass
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            if "access_token" not in data:
                raise KISAuthError(f"Token response missing access_token: {data}")

            self._access_token = data["access_token"]
            expires_in = data.get("expires_in", 86400)
            self._token_expires_at = time.time() + min(expires_in, 82800)

            self._write_token_cache(self._access_token, self._token_expires_at)
            _log.info("KIS access token acquired")
            return self._access_token

        except requests.RequestException as e:
            _log.error(f"Failed to get KIS access token: {e}")
            raise KISAuthError(f"Token acquisition failed: {e}") from e

    def _get_hashkey(self, body_json: str) -> str:
        """
        KIS API Hashkey 생성 (POST 요청 시 필수).

        IGW00002 방지: hashkey는 전송할 body와 동일한 바이트로 발급해야 하므로
        body_json(직렬화된 JSON 문자열)을 그대로 전달·전송합니다.

        Args:
            body_json: 직렬화된 요청 Body (JSON 문자열)

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
            resp = requests.post(
                url, data=body_json.encode("utf-8"), headers=headers, timeout=self.timeout
            )
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
            "custtype": "P",  # 개인 "P", 제휴사 "B" (open-trading-api kis_auth.py)
        }

        # Hashkey 및 POST body: 동일 직렬화 사용 (IGW00002 방지)
        body_bytes: Optional[bytes] = None
        if method.upper() == "POST" and body:
            body_str = json.dumps(body, sort_keys=True, ensure_ascii=False)
            body_bytes = body_str.encode("utf-8")
            hashkey = self._get_hashkey(body_str)
            headers["hashkey"] = hashkey

        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body_bytes if body_bytes is not None else None,
                json=None if body_bytes is not None else (body if body else None),
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
