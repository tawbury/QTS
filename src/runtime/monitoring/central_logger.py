"""
Central Logging System (Phase 9 — Logging & Monitoring Core).

- ETEDA Pipeline, Engine, Broker 단계별 로거 이름 통일
- 단일 설정 진입점(configure_central_logging)으로 레벨/포맷 제어
- 근거: docs/arch/09_Ops_Automation_Architecture.md
"""

from __future__ import annotations

import logging
from typing import Optional

# Logger name hierarchy (ETEDA / Engine / Broker)
LOG_ETEDA = "runtime.eteda"
LOG_ENGINE = "runtime.engine"
LOG_BROKER = "runtime.broker"
LOG_MONITORING = "runtime.monitoring"


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


def configure_central_logging(
    level: int | str = logging.INFO,
    format_string: Optional[str] = None,
    root: bool = True,
) -> None:
    """
    Configure central logging for runtime.

    - level: logging.INFO, logging.DEBUG, etc. or "INFO", "DEBUG"
    - format_string: log format; default includes asctime, levelname, name, message
    - root: if True, configure root logger; else only runtime.* loggers
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    fmt = format_string or _DEFAULT_FORMAT
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(fmt))

    if root:
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        if not root_logger.handlers:
            root_logger.addHandler(handler)
    else:
        for name in (LOG_ETEDA, LOG_ENGINE, LOG_BROKER, LOG_MONITORING):
            log = logging.getLogger(name)
            log.setLevel(level)
            log.handlers.clear()
            log.addHandler(handler)
            log.propagate = False
