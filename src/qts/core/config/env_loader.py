"""
환경 변수 로더

.env 파일에서 Broker API 설정을 로드합니다.
KIS/KIWOOM 모의투자(VTS) / 실전투자(REAL) 모드를 자동으로 선택합니다.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

_log = logging.getLogger(__name__)


BrokerType = Literal["KIS", "KIWOOM"]
TradingMode = Literal["VTS", "REAL"]


# KIS와 Kiwoom의 환경 변수 접두사
BROKER_PREFIXES = {
    "KIS": "KIS",
    "KIWOOM": "KIWOOM"
}


@dataclass(frozen=True)
class BrokerConfig:
    """Broker API 설정"""
    broker_type: BrokerType
    trading_mode: TradingMode
    app_key: str
    app_secret: str
    account_no: str
    acnt_prdt_cd: str
    base_url: str
    websocket_url: Optional[str] = None


def load_dotenv_if_available(project_root: Optional[Path] = None) -> bool:
    """
    .env 파일 로드 (python-dotenv 사용)

    Args:
        project_root: 프로젝트 루트 경로 (None이면 현재 디렉토리)

    Returns:
        bool: .env 로드 성공 여부
    """
    try:
        from dotenv import load_dotenv

        env_path = project_root / "config" / ".env" if project_root else Path("config") / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            _log.info(f".env file loaded from {env_path}")
            return True
        else:
            _log.warning(f".env file not found at {env_path}")
            return False
    except ImportError:
        _log.warning("python-dotenv not installed, skipping .env loading")
        return False


def load_env_by_run_mode(project_root: Optional[Path] = None) -> dict:
    """
    RUN_MODE 환경변수를 기반으로 .env 파일을 레이어링 로드.

    로딩 순서 (override=False, 즉 먼저 로드된 값이 우선):
      1. OS 환경변수 (항상 최우선 — load_dotenv가 덮어쓰지 않음)
      2. config/.env.{RUN_MODE}  (환경별 경로/설정)
      3. config/.env.shared       (공통 설정)
      4. .env                     (시크릿, local 모드만)

    RUN_MODE 값:
      "local"     → .env.local + .env.shared + .env (기본값)
      "container" → .env.container + .env.shared

    Args:
        project_root: 프로젝트 루트 경로 (None이면 현재 작업 디렉토리)

    Returns:
        dict with keys: run_mode, files_loaded, files_skipped
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        _log.warning("python-dotenv not installed; skipping .env file loading")
        return {"run_mode": os.environ.get("RUN_MODE", "local"), "files_loaded": [], "files_skipped": []}

    if project_root is None:
        project_root = Path.cwd()

    run_mode = os.environ.get("RUN_MODE", "local")
    config_base = project_root / "config"

    result = {"run_mode": run_mode, "files_loaded": [], "files_skipped": []}

    # 레이어 순서: 환경별 → 공통 → 시크릿 (override=False이므로 먼저 로드된 값 우선)
    layers = [
        config_base / f".env.{run_mode}",   # 환경별 (경로, DB_HOST 등)
        config_base / ".env.shared",         # 공통 (TZ, LOG_LEVEL 등)
    ]

    # local 모드: 시크릿 파일도 로드 (config 디렉토리)
    if run_mode == "local":
        secrets_file = config_base / ".env"
        if secrets_file.exists():
            layers.append(secrets_file)

    for env_file in layers:
        if env_file.exists():
            load_dotenv(env_file, override=False)
            result["files_loaded"].append(str(env_file))
        else:
            result["files_skipped"].append(str(env_file))

    # [로컬 모드] 상대 경로를 절대 경로로 변환 (디렉토리 생성 없음)
    if run_mode == "local":
        path_vars = [
            "QTS_DATA_DIR",
            "QTS_LOG_DIR",
            "QTS_CONFIG_DIR",
            "OBSERVER_DATA_DIR",
        ]
        
        for var in path_vars:
            value = os.environ.get(var)
            if value and value.startswith("./"):
                # 상대 경로를 절대 경로로 변환
                abs_path = (project_root / value[2:]).resolve()
                os.environ[var] = str(abs_path)
            elif value and value.startswith("../"):
                # 부모 디렉토리 포함 상대 경로
                abs_path = (project_root / value).resolve()
                os.environ[var] = str(abs_path)

    _log.info(
        "Environment loaded: RUN_MODE=%s | loaded=%s | skipped=%s",
        run_mode, result["files_loaded"], result["files_skipped"],
    )
    return result


def get_broker_config(broker_type: BrokerType = "KIWOOM") -> BrokerConfig:
    """
    Broker API 설정 로드

    Args:
        broker_type: "KIS" 또는 "KIWOOM"

    Returns:
        BrokerConfig: Broker API 설정

    Raises:
        ValueError: 필수 환경 변수가 누락된 경우
    """
    # 1. 모드 결정 (VTS vs REAL)
    mode_key = f"{broker_type}_MODE"
    mode_value = os.getenv(mode_key, f"{broker_type}_VTS").upper()

    if "REAL" in mode_value:
        trading_mode: TradingMode = "REAL"
    else:
        trading_mode = "VTS"

    _log.info(f"Broker mode: {broker_type}_{trading_mode}")

    # 2. 환경 변수 키 구성 (대소문자 모두 지원)
    prefix_upper = f"{broker_type}_{trading_mode}_"
    prefix_lower = prefix_upper.lower()

    def getenv_multi(*names, default=None):
        for n in names:
            v = os.getenv(n)
            if v is not None:
                return v
        return default

    # 3. 필수 환경 변수 로드 (upper/lower 모두 시도)
    app_key = getenv_multi(f"{prefix_upper}APP_KEY", f"{prefix_lower}app_key")
    app_secret = getenv_multi(f"{prefix_upper}APP_SECRET", f"{prefix_lower}app_secret")
    account_no = getenv_multi(f"{prefix_upper}ACCOUNT_NO", f"{prefix_lower}account_no")
    acnt_prdt_cd = getenv_multi(f"{prefix_upper}ACNT_PRDT_CD", f"{prefix_lower}acnt_prdt_cd", default="01")
    base_url = getenv_multi(f"{prefix_upper}BASE_URL", f"{prefix_lower}base_url")

    # 4. 선택적 환경 변수
    websocket_url = getenv_multi(f"{prefix_upper}WEBSOCKET_URL", f"{prefix_lower}websocket_url")

    # 5. 검증

    missing = []
    if not app_key:
        missing.append(f"{prefix_upper}APP_KEY or {prefix_lower}app_key")
        app_key = ""
    if not app_secret:
        missing.append(f"{prefix_upper}APP_SECRET or {prefix_lower}app_secret")
        app_secret = ""
    if not account_no:
        missing.append(f"{prefix_upper}ACCOUNT_NO or {prefix_lower}account_no")
        account_no = ""
    if not base_url:
        missing.append(f"{prefix_upper}BASE_URL or {prefix_lower}base_url")
        base_url = ""

    if missing:
        logging.warning(
            f"[get_broker_config] Missing required environment variables for {broker_type}_{trading_mode}: "
            f"{', '.join(missing)} (set as empty string for test mode)"
        )

    return BrokerConfig(
        broker_type=broker_type,
        trading_mode=trading_mode,
        app_key=app_key,
        app_secret=app_secret,
        account_no=account_no,
        acnt_prdt_cd=acnt_prdt_cd,
        base_url=base_url,
        websocket_url=websocket_url,
    )


def is_real_order_enabled() -> bool:
    """
    실전 주문 활성화 여부 확인

    Returns:
        bool: ENABLE_REAL_ORDER 환경 변수가 "Y"인 경우 True
    """
    enable_real_order = os.getenv("ENABLE_REAL_ORDER", "N").strip().upper()
    return enable_real_order == "Y"


def get_google_sheets_config() -> tuple[str, str]:
    """
    Google Sheets API 설정 로드

    Returns:
        tuple[str, str]: (spreadsheet_id, credentials_path)

    Raises:
        ValueError: 필수 환경 변수가 누락된 경우
    """
    spreadsheet_id = os.getenv("GOOGLE_SHEET_KEY")
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_FILE")

    missing = []
    if not spreadsheet_id:
        missing.append("GOOGLE_SHEET_KEY")
    if not credentials_path:
        missing.append("GOOGLE_CREDENTIALS_FILE")

    if missing:
        raise ValueError(
            f"Missing required environment variables for Google Sheets: "
            f"{', '.join(missing)}"
        )

    return spreadsheet_id, credentials_path
