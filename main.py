#!/usr/bin/env python3
"""
QTS 전체 구동 진입점 (ETEDA 파이프라인 루프).

- Config 로드 → Runner 생성 → run_eteda_loop 실행.
- --local-only: MockSheetsClient, MockSafetyHook, MockSnapshotSource 사용 (API 없이 동작)
- --dry-run: --local-only와 동일
- Broker/Safety는 선택 주입 (미설정 시 NoopBroker, safety_hook=None).

실행 예시:
    python main.py --local-only --verbose
    python main.py --local-only --max-iterations 5
    python main.py --scope scalp

검수 문서: docs/Full_Run_Integration_Scan.md
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# 프로젝트 루트 기준 src 경로 추가 (runtime.*, ops.*, shared.* import)
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if _SRC.exists() and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from runtime.config.config_loader import load_local_only_config, load_unified_config
from runtime.config.config_models import ConfigScope, UnifiedConfig
from runtime.config.config_validator import validate_config, ConfigValidationError
from runtime.config.env_loader import load_dotenv_if_available
from runtime.execution.brokers import create_broker_for_execution
from runtime.execution.brokers.noop_broker import NoopBroker
from runtime.execution_loop.eteda_loop import run_eteda_loop
from runtime.monitoring.central_logger import configure_central_logging
from runtime.utils.runtime_checks import preflight_check

_LOG = logging.getLogger("main")

# 종료 시그널 처리용 플래그
_shutdown_requested = False


def _parse_args() -> argparse.Namespace:
    """CLI 인자 파싱"""
    p = argparse.ArgumentParser(description="QTS ETEDA pipeline loop")
    p.add_argument(
        "--scope",
        choices=["scalp", "swing"],
        default="scalp",
        help="Config scope (load_unified_config). Default: scalp",
    )
    p.add_argument(
        "--broker",
        choices=["kis", "kiwoom"],
        default="kiwoom",
        help="Broker to use (kis or kiwoom). Default: kiwoom",
    )
    p.add_argument(
        "--local-only",
        action="store_true",
        help="Use only Config_Local (no Google Sheet config). Mock clients for testing.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (same as --local-only).",
    )
    p.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum iterations for local-only mode (default: 10, 0=unlimited).",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose logging (DEBUG level).",
    )
    return p.parse_args()


def _setup_signal_handlers() -> None:
    """Ctrl+C/종료 시그널 핸들러 설정"""
    global _shutdown_requested

    def handler(signum, frame):
        global _shutdown_requested
        _LOG.info("Shutdown signal received (signal=%s)", signum)
        _shutdown_requested = True

    # Windows에서는 SIGTERM이 없을 수 있음
    signal.signal(signal.SIGINT, handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handler)


def _create_mock_runner(
    config: UnifiedConfig,
    project_root: Path,
    max_iterations: int,
):
    """
    --local-only 모드용 Runner 생성.

    Mock 클라이언트들을 주입하여 API 의존성 없이 파이프라인을 테스트합니다.

    Args:
        config: UnifiedConfig 인스턴스
        project_root: 프로젝트 루트 경로
        max_iterations: 최대 반복 횟수

    Returns:
        (runner, snapshot_source, should_stop_fn) 튜플
    """
    from runtime.data.mock_sheets_client import MockSheetsClient
    from runtime.pipeline.mock_safety_hook import MockSafetyHook
    from runtime.execution_loop.mock_snapshot_source import (
        MockSnapshotSource,
        create_mock_should_stop,
    )
    from runtime.pipeline.eteda_runner import ETEDARunner

    # Mock Sheets Client
    mock_sheets = MockSheetsClient()

    # Mock Safety Hook
    mock_safety = MockSafetyHook(initial_state="NORMAL")

    # Broker: NoopBroker (실주문 없음)
    broker = create_broker_for_execution(live_allowed=False, adapter=None)
    assert isinstance(broker, NoopBroker), "Expected NoopBroker when adapter is None"

    # Runner 생성 (Mock 주입)
    runner = ETEDARunner(
        config=config,
        sheets_client=mock_sheets,
        project_root=project_root,
        broker=broker,
        safety_hook=mock_safety,
    )

    # Mock Snapshot Source
    snapshot_source = MockSnapshotSource(
        symbols=["005930", "000660"],  # 삼성전자, SK하이닉스
        base_prices={"005930": 70000.0, "000660": 150000.0},
        volatility=0.002,
        max_iterations=max_iterations,
    )

    # should_stop 함수: 시그널 + 최대 반복 횟수 체크
    def combined_should_stop() -> bool:
        global _shutdown_requested
        if _shutdown_requested:
            return True
        if max_iterations > 0 and snapshot_source.iteration_count >= max_iterations:
            return True
        # Config의 PIPELINE_PAUSED 체크
        paused = config.get_flat("PIPELINE_PAUSED")
        if paused and str(paused).strip().lower() in ("1", "true", "yes", "on"):
            return True
        return False

    return runner, snapshot_source, combined_should_stop


def _create_production_runner(
    config: UnifiedConfig,
    project_root: Path,
    broker_type: str = "kiwoom",
):
    """
    프로덕션 모드용 Runner 생성.

    실제 GoogleSheetsClient와 Broker API를 연결하여 동작합니다.

    Args:
        config: UnifiedConfig 인스턴스
        project_root: 프로젝트 루트 경로
        broker_type: "kis" 또는 "kiwoom"

    Returns:
        (runner, snapshot_source, should_stop_fn) 튜플
    """
    from runtime.pipeline.eteda_runner import ETEDARunner
    from runtime.execution_loop.eteda_loop_policy import default_should_stop_from_config
    from runtime.config.env_loader import get_broker_config, is_real_order_enabled
    from runtime.execution.adapters.order_adapter_to_broker_engine_adapter import (
        OrderAdapterToBrokerEngineAdapter,
    )

    # 1. Broker 설정 로드 (.env에서)
    broker_type_upper = broker_type.upper()
    try:
        broker_config = get_broker_config(broker_type=broker_type_upper)
        _LOG.info(
            f"Broker config loaded: {broker_config.broker_type}_{broker_config.trading_mode}"
        )

        # 2. Broker Client 및 Adapter 생성 (KIS vs KIWOOM)
        if broker_type_upper == "KIS":
            from runtime.broker.kis.kis_client import KISClient
            from runtime.broker.adapters.kis_adapter import KISOrderAdapter

            client = KISClient(
                app_key=broker_config.app_key,
                app_secret=broker_config.app_secret,
                base_url=broker_config.base_url,
                account_no=broker_config.account_no,
                acnt_prdt_cd=broker_config.acnt_prdt_cd,
                trading_mode=broker_config.trading_mode,
            )

            order_adapter = KISOrderAdapter(
                client=client,
                acnt_no=broker_config.account_no,
                acnt_prdt_cd=broker_config.acnt_prdt_cd,
            )

        elif broker_type_upper == "KIWOOM":
            from runtime.broker.kiwoom.kiwoom_client import KiwoomClient
            from runtime.broker.adapters.kiwoom_adapter import KiwoomOrderAdapter

            client = KiwoomClient(
                app_key=broker_config.app_key,
                app_secret=broker_config.app_secret,
                base_url=broker_config.base_url,
                account_no=broker_config.account_no,
                acnt_prdt_cd=broker_config.acnt_prdt_cd,
            )

            order_adapter = KiwoomOrderAdapter(
                client=client,
                acnt_no=broker_config.account_no,
                market="0",  # 0: 국내, 1: 해외
            )

        else:
            raise ValueError(f"Unsupported broker type: {broker_type}")

        # 3. BrokerEngine Adapter로 래핑
        adapter = OrderAdapterToBrokerEngineAdapter(order_adapter=order_adapter)

        # 4. LIVE 모드 확인
        real_order_enabled = is_real_order_enabled()
        live_allowed = broker_config.trading_mode == "REAL" and real_order_enabled

        if broker_config.trading_mode == "REAL" and not real_order_enabled:
            _LOG.warning(
                "REAL mode detected but ENABLE_REAL_ORDER=N. "
                "Orders will be rejected by BrokerEngine."
            )

        # 5. BrokerEngine 생성
        broker = create_broker_for_execution(live_allowed=live_allowed, adapter=adapter)
        _LOG.info(f"BrokerEngine created (live_allowed={live_allowed})")

    except Exception as e:
        _LOG.error(f"Failed to create production broker: {e}")
        _LOG.warning("Falling back to NoopBroker")
        broker = create_broker_for_execution(live_allowed=False, adapter=None)

    # Safety: 현재는 None (실제 SafetyLayer 연결 시 변경 필요)
    # TODO: ops.safety.SafetyLayer 연결 시 주입
    safety_hook = None

    # Runner 생성 (sheets_client=None → 내부에서 GoogleSheetsClient 생성)
    runner = ETEDARunner(
        config=config,
        sheets_client=None,  # 내부에서 GoogleSheetsClient 생성
        project_root=project_root,
        broker=broker,
        safety_hook=safety_hook,
    )

    # Snapshot source: None (기본 interval 트리거 사용)
    # TODO: Kiwoom WebSocket으로 실시간 시세 연결
    snapshot_source = None

    # should_stop: Config 기반
    def combined_should_stop() -> bool:
        global _shutdown_requested
        if _shutdown_requested:
            return True
        stop_fn = default_should_stop_from_config(config)
        return stop_fn()

    return runner, snapshot_source, combined_should_stop


def main() -> None:
    """메인 진입점"""
    args = _parse_args()

    # 로깅 설정 (콘솔 + 파일)
    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_file = _ROOT / "logs" / "qts.log"
    configure_central_logging(
        level=log_level,
        format_string="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        root=True,
        log_file=log_file,
    )

    # 시그널 핸들러 설정
    _setup_signal_handlers()

    project_root = _ROOT
    is_local_only = args.local_only or args.dry_run

    # --- .env 로드 (Production 모드에서만) ---
    if not is_local_only:
        load_dotenv_if_available(project_root)

    # --- Preflight Check ---
    if not preflight_check(project_root, verbose=args.verbose):
        _LOG.warning("Preflight check failed, but continuing anyway...")
        # Note: Config 로드 실패 시 명확한 에러가 발생하므로 여기서는 경고만

    # --- Config 로드 ---
    if is_local_only:
        _LOG.info("Loading local-only config...")
        result = load_local_only_config(project_root)
        if not result.ok or result.unified_config is None:
            _LOG.error("Config_Local load failed: %s", result.error)
            sys.exit(1)
        config = result.unified_config
    else:
        scope = ConfigScope.SCALP if args.scope == "scalp" else ConfigScope.SWING
        _LOG.info("Loading unified config (scope=%s)...", scope.value)
        result = load_unified_config(project_root, scope)
        if not result.ok or result.unified_config is None:
            _LOG.error("Unified config load failed: %s", result.error)
            sys.exit(1)
        config = result.unified_config

    # --- Config 검증 ---
    try:
        validate_config(config)
        _LOG.info("Config validation passed")
    except ConfigValidationError as e:
        _LOG.error("Config validation failed: %s", e)
        sys.exit(1)

    # --- Runner 생성 ---
    if is_local_only:
        _LOG.info("Creating mock runner (local-only mode)...")
        runner, snapshot_source, should_stop = _create_mock_runner(
            config=config,
            project_root=project_root,
            max_iterations=args.max_iterations,
        )
    else:
        _LOG.info(f"Creating production runner (broker={args.broker})...")
        runner, snapshot_source, should_stop = _create_production_runner(
            config=config,
            project_root=project_root,
            broker_type=args.broker,
        )

    # --- ETEDA Loop 실행 ---
    _LOG.info(
        "Starting ETEDA loop (scope=%s, local_only=%s, max_iterations=%s)",
        args.scope,
        is_local_only,
        args.max_iterations if is_local_only else "unlimited",
    )

    try:
        asyncio.run(
            run_eteda_loop(
                runner=runner,
                config=config,
                should_stop=should_stop,
                snapshot_source=snapshot_source,
            )
        )
    except KeyboardInterrupt:
        _LOG.info("KeyboardInterrupt received, shutting down...")
    except Exception as e:
        _LOG.exception("ETEDA loop failed with exception: %s", e)
        sys.exit(1)

    _LOG.info("ETEDA loop finished.")


if __name__ == "__main__":
    main()
