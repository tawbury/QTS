"""
Central Logging System (Phase 9 — Logging & Monitoring Core).

- ETEDA Pipeline, Engine, Broker 단계별 로거 이름 통일
- 단일 설정 진입점(configure_central_logging)으로 레벨/포맷/파일 로그 제어
- 근거: docs/arch/09_Ops_Automation_Architecture.md §6
"""

from __future__ import annotations

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

# Logger name hierarchy (ETEDA / Engine / Broker)
LOG_ETEDA = "runtime.eteda"
LOG_ENGINE = "runtime.engine"
LOG_BROKER = "runtime.broker"
LOG_MONITORING = "runtime.monitoring"

# 파일 로그 기본값
_LOG_DIR_NAME = "logs"
_LOG_BASE_NAME = "qts.log"
_DEFAULT_RETENTION_DAYS = 7


def get_logger(name: str) -> logging.Logger:
    """Return a logger under the central hierarchy. Prefer LOG_* constants."""
    return logging.getLogger(name)


def get_eteda_logger() -> logging.Logger:
    """Logger for ETEDA Pipeline (Extract/Transform/Evaluate/Decide/Act)."""
    return get_logger(LOG_ETEDA)


def get_engine_logger() -> logging.Logger:
    """Logger for Engine layer (Strategy/Portfolio/Performance/Trading)."""
    return get_logger(LOG_ENGINE)


def get_broker_logger() -> logging.Logger:
    """Logger for Broker communication (order, heartbeat, errors)."""
    return get_logger(LOG_BROKER)


def get_monitoring_logger() -> logging.Logger:
    """Logger for monitoring/metrics/health."""
    return get_logger(LOG_MONITORING)


_DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def _make_file_handler(
    log_path: Path,
    level: int,
    fmt: str,
    retention_days: int = _DEFAULT_RETENTION_DAYS,
) -> TimedRotatingFileHandler:
    """Create TimedRotatingFileHandler for daily rotation."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = TimedRotatingFileHandler(
        filename=str(log_path),
        when="midnight",
        interval=1,
        backupCount=retention_days,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(fmt))
    return handler


def configure_central_logging(
    level: int | str = logging.INFO,
    format_string: Optional[str] = None,
    root: bool = True,
    log_file: Optional[Path] = None,
    retention_days: Optional[int] = None,
) -> None:
    """
    Configure central logging for runtime.

    - level: logging.INFO, logging.DEBUG, etc. or "INFO", "DEBUG"
    - format_string: log format; default includes asctime, levelname, name, message
    - root: if True, configure root logger; else only runtime.* loggers
    - log_file: if set, add file handler (TimedRotatingFileHandler, midnight rotation)
    - retention_days: backup count for rotated files (default: 7, env QTS_LOG_RETENTION_DAYS)
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    fmt = format_string or _DEFAULT_FORMAT

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(fmt))

    handlers: list[logging.Handler] = [console_handler]

    # 파일 핸들러 (log_file 지정 시)
    if log_file is not None:
        try:
            days = retention_days
            if days is None:
                days = int(os.getenv("QTS_LOG_RETENTION_DAYS", str(_DEFAULT_RETENTION_DAYS)))
            file_handler = _make_file_handler(log_path=log_file, level=level, fmt=fmt, retention_days=days)
            handlers.append(file_handler)
        except OSError as e:
            # 로그 디렉터리 생성/쓰기 실패 시 콘솔만 사용
            _fallback = logging.getLogger(__name__)
            _fallback.warning("File logging disabled: %s", e)

    if root:
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.handlers.clear()
        for h in handlers:
            root_logger.addHandler(h)
    else:
        for name in (LOG_ETEDA, LOG_ENGINE, LOG_BROKER, LOG_MONITORING):
            log = logging.getLogger(name)
            log.setLevel(level)
            log.handlers.clear()
            for h in handlers:
                log.addHandler(h)
            log.propagate = False
