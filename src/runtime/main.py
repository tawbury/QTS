#!/usr/bin/env python3
"""
QTS Application Entrypoint

단일 앱 진입점입니다.
src/ 구조로 리팩토링된 새로운 진입점입니다.

실행 방법:
    python -m src.runtime.main --local-only --verbose
    python -m src.runtime.main --scope scalp --broker kiwoom
    docker run -e QTS_ENV=production qts-app
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# 프로젝트 루트를 sys.path에 추가
_ROOT = Path(__file__).resolve().parent.parent.parent  # prj_qts/
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# src 내부 imports
from src.qts.core.config.config_loader import load_local_only_config, load_unified_config
from src.qts.core.config.config_models import ConfigScope, UnifiedConfig
from src.qts.core.config.config_validator import validate_config, ConfigValidationError
from src.qts.core.config.env_loader import load_dotenv_if_available
from src.monitoring.central_logger import configure_central_logging
from src.pipeline.loop.eteda_loop import run_eteda_loop
from src.observer_client.factory import create_observer_client

# shared imports
from src.shared.paths import get_project_root
from src.shared.timezone_utils import get_kst_now


_LOG = logging.getLogger("src.runtime.main")

# 종료 시그널 처리용 플래그
_shutdown_requested = False


def _parse_args() -> argparse.Namespace:
    """CLI 인자 파싱"""
    p = argparse.ArgumentParser(description="QTS Trading System")
    p.add_argument(
        "--scope",
        choices=["scalp", "swing"],
        default="scalp",
        help="Trading strategy scope (default: scalp)",
    )
    p.add_argument(
        "--broker",
        choices=["kis", "kiwoom"],
        default="kiwoom",
        help="Broker to use (default: kiwoom)",
    )
    p.add_argument(
        "--local-only",
        action="store_true",
        help="Use local config only (no Google Sheets). Enables stub Observer.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (same as --local-only)",
    )
    p.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum iterations for local-only mode (default: 10, 0=unlimited)",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose logging (DEBUG level)",
    )
    p.add_argument(
        "--env",
        choices=["development", "production"],
        default="development",
        help="Runtime environment (default: development)",
    )
    return p.parse_args()


def _setup_signal_handlers() -> None:
    """Ctrl+C/종료 시그널 핸들러 설정"""
    global _shutdown_requested

    def handler(signum, frame):
        global _shutdown_requested
        _LOG.info(f"Shutdown signal received (signal={signum})")
        _shutdown_requested = True

    signal.signal(signal.SIGINT, handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handler)


class NoopSheetsClient:
    """Google Sheets를 사용하지 않는 환경용 Stub 클라이언트"""
    def __getattr__(self, name):
        def method(*args, **kwargs):
            _LOG.debug(f"NoopSheetsClient.{name} called (doing nothing)")
            return None
        return method

    async def authenticate(self) -> bool:
        return True


def _create_production_runner(
    config: UnifiedConfig,
    project_root: Path,
    broker_type: str,
    observer_client,
    local_only: bool = False,
):
    """
    프로덕션 모드용 Runner 생성

    실제 GoogleSheetsClient와 Broker API를 연결하여 동작합니다.
    """
    from src.pipeline.eteda_runner import ETEDARunner
    from src.pipeline.loop.eteda_loop_policy import default_should_stop_from_config
    from src.safety.layer import SafetyLayer

    _LOG.info(f"Creating Runner (broker={broker_type}, local_only={local_only})")

    # Google Sheets Client
    if local_only:
        _LOG.info("Using NoopSheetsClient (local-only mode)")
        sheets_client = NoopSheetsClient()
    else:
        from src.db.google_sheets_client import GoogleSheetsClient
        sheets_client = GoogleSheetsClient()

    # Broker Adapter
    if local_only:
        from src.provider.brokers.noop_broker import NoopBroker
        _LOG.info("Using NoopBroker (local-only mode)")
        broker = NoopBroker()
    else:
        from src.qts.core.config.env_loader import get_broker_config, is_real_order_enabled
        from src.provider.adapters.order_adapter_to_broker_engine_adapter import (
            OrderAdapterToBrokerEngineAdapter,
        )
        from src.provider.clients.broker.adapters.registry import get_broker

        broker_config = get_broker_config(broker_type.upper())
        
        client = None
        if broker_type == "kis":
            from src.provider.clients.broker.kis.kis_client import KISClient
            client = KISClient(
                app_key=broker_config.app_key,
                app_secret=broker_config.app_secret,
                base_url=broker_config.base_url,
                account_no=broker_config.account_no,
                acnt_prdt_cd=broker_config.acnt_prdt_cd,
                trading_mode=broker_config.trading_mode
            )

        adapter = get_broker(
            broker_type, 
            client=client,
            acnt_no=broker_config.account_no,
            acnt_prdt_cd=broker_config.acnt_prdt_cd
        )

        # Broker Engine
        live_allowed = is_real_order_enabled()
        broker = OrderAdapterToBrokerEngineAdapter(adapter, live_allowed=live_allowed)
        if live_allowed:
            _LOG.warning("LIVE TRADING ENABLED - Real orders will be executed")
        else:
            _LOG.info("PAPER TRADING MODE - Orders will be simulated")

    # Safety Layer (Safety Hook)
    kill_switch_enabled = config.get_flat("safety.kill_switch_enabled") or False
    safe_mode_enabled = config.get_flat("safety.safe_mode_enabled") or False  # Assuming this key exists or defaulting False
    
    safety_hook = SafetyLayer(
        kill_switch=bool(kill_switch_enabled),
        safe_mode=bool(safe_mode_enabled)
    )

    # Runner 생성
    runner = ETEDARunner(
        config=config,
        sheets_client=sheets_client,
        project_root=project_root,
        broker=broker,
        safety_hook=safety_hook,
    )

    # Snapshot Source: Observer Client를 통해 실시간 데이터 수신
    if hasattr(observer_client, "get_next_snapshot"):
        snapshot_source = observer_client.get_next_snapshot
        _LOG.info("Using Observer Client as snapshot source")
    else:
        snapshot_source = None

    # should_stop 함수
    should_stop_fn = default_should_stop_from_config(config)

    return runner, snapshot_source, should_stop_fn


def preflight_check(project_root: Path, local_only: bool) -> None:
    """
    앱 시작 전 사전 검증
    """
    import os
    _LOG.info("Running preflight checks...")

    # 1. 필수 디렉토리 존재 확인 (K8s 환경에서는 QTS_LOG_DIR 사용)
    logs_dir = Path(os.environ.get("QTS_LOG_DIR", str(project_root / "logs")))
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
        _LOG.info(f"Created logs directory: {logs_dir}")

    # 2. Config 파일 존재 확인 (K8s 환경에서는 ConfigMap 사용하므로 선택적)
    config_local = project_root / "config" / "local" / "config_local.json"
    deployment_mode = os.environ.get("QTS_DEPLOYMENT_MODE", "local")
    if deployment_mode == "local" and not config_local.exists():
        raise FileNotFoundError(f"Config file not found: {config_local}")
    elif deployment_mode != "local":
        _LOG.info(f"Running in {deployment_mode} mode - config from environment/ConfigMap")

    # 3. Google Sheets 인증 (production 모드만)
    if not local_only and deployment_mode == "local":
        env_cred_path = os.getenv("GOOGLE_CREDENTIALS_FILE")
        if env_cred_path:
            credentials = project_root / env_cred_path
        else:
            credentials = project_root / "config" / "credentials.json"

        if not credentials.exists():
            _LOG.warning(f"Google credentials not found: {credentials}")

    _LOG.info("Preflight checks passed")


def main() -> int:
    """
    메인 진입점

    Returns:
        int: Exit code (0=성공, 1=실패)
    """
    # 0. Cleanup
    from src.maintenance.cleanup import cleanup_logs, cleanup_trade_data
    try:
        cleanup_logs()
        cleanup_trade_data()
    except Exception as e:
        # 실패해도 시스템 시작은 계속
        logging.warning(f"Cleanup failed: {e}", exc_info=True)

    args = _parse_args()

    # 0. 로깅 설정
    from datetime import datetime
    log_level = logging.DEBUG if args.verbose else logging.INFO
    # K8s 환경에서는 QTS_LOG_DIR 환경변수 사용, 로컬에서는 _ROOT/logs
    import os
    log_dir = Path(os.environ.get("QTS_LOG_DIR", str(_ROOT / "logs")))
    log_file_name = f"qts_{datetime.now().strftime('%Y%m%d')}.log"
    log_file = log_dir / log_file_name
    configure_central_logging(
        level=log_level,
        format_string="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        root=True,
        log_file=log_file,
    )

    _LOG.info("=" * 80)
    _LOG.info("QTS Trading System Starting")
    _LOG.info(f"Timestamp: {get_kst_now()}")
    _LOG.info(f"Arguments: {vars(args)}")
    _LOG.info("=" * 80)

    # 1. Signal handlers
    _setup_signal_handlers()

    # 2. .env 로드
    project_root = get_project_root()
    load_dotenv_if_available(project_root)
    _LOG.info(f"Project root: {project_root}")

    # 3. Preflight check
    local_only = args.local_only or args.dry_run
    try:
        preflight_check(project_root, local_only)
    except Exception as e:
        _LOG.error(f"Preflight check failed: {e}")
        return 1

    # 4. Config 로드
    try:
        deployment_mode = os.environ.get("QTS_DEPLOYMENT_MODE", "local")
        use_local_config = local_only
        
        if use_local_config:
            _LOG.info(f"Loading Local-Only Config (local_only={local_only})")
            merge_result = load_local_only_config(project_root)
        else:
            scope_str = args.scope.upper()
            scope = ConfigScope[scope_str]
            _LOG.info(f"Loading Unified Config (scope={scope})")
            merge_result = load_unified_config(project_root, scope)

        if not merge_result.ok or merge_result.unified_config is None:
            raise ConfigValidationError(merge_result.error or "Config load failed")

        config = merge_result.unified_config

        # Config 검증
        validate_config(config)
        _LOG.info("Config loaded and validated successfully")

    except ConfigValidationError as e:
        _LOG.error(f"Config validation failed: {e}")
        return 1
    except Exception as e:
        _LOG.error(f"Failed to load config: {e}", exc_info=True)
        return 1

    # 5. Observer Client 생성
    try:
        import os
        observer_type = os.environ.get("OBSERVER_TYPE", "stub").lower()

        if observer_type == "file":
            from src.observer_client.file_client import FileObserverClient
            assets_dir = os.environ.get(
                "OBSERVER_ASSETS_DIR",
                "/opt/platform/runtime/observer/data/assets"
            )
            observer = FileObserverClient(assets_dir=assets_dir)
            _LOG.info(f"Observer Client: File (dir={assets_dir})")
        else:
            observer = create_observer_client(client_type="stub")
            _LOG.info("Observer Client: Stub (mock)")

        # Observer 연결
        asyncio.run(observer.connect())

    except Exception as e:
        _LOG.error(f"Failed to create Observer client: {e}", exc_info=True)
        return 1

    # 6. Runner 생성
    # K8s 모드에서는 mock runner 사용 (GoogleSheetsClient 불필요)
    try:
        runner, snapshot_source, should_stop_fn = _create_production_runner(
            config=config,
            project_root=project_root,
            broker_type=args.broker,
            observer_client=observer,
            local_only=local_only,
        )

        _LOG.info("Runner created successfully")

    except Exception as e:
        _LOG.error(f"Failed to create runner: {e}", exc_info=True)
        return 1

    # 7. ETEDA Loop 실행
    try:
        _LOG.info("Starting ETEDA Loop...")
        asyncio.run(run_eteda_loop(
            runner=runner,
            config=config,
            should_stop=should_stop_fn,
            snapshot_source=snapshot_source,
        ))
        _LOG.info("ETEDA Loop completed")

    except KeyboardInterrupt:
        _LOG.info("Interrupted by user (Ctrl+C)")
    except Exception as e:
        _LOG.error(f"ETEDA Loop error: {e}", exc_info=True)
        return 1
    finally:
        # 8. Cleanup
        _LOG.info("Shutting down...")
        asyncio.run(observer.disconnect())
        _LOG.info("Observer disconnected")

    _LOG.info("=" * 80)
    _LOG.info("QTS Trading System Terminated")
    _LOG.info("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
