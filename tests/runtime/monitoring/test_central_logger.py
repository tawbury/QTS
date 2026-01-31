"""
Central logging tests (Phase 9 — Logging & Monitoring Core).

- Logger name constants, get_logger / get_*_logger.
- configure_central_logging (level, root vs runtime-only).
"""

from __future__ import annotations

import logging

import pytest

from runtime.monitoring.central_logger import (
    LOG_BROKER,
    LOG_ENGINE,
    LOG_ETEDA,
    LOG_MONITORING,
    configure_central_logging,
    get_broker_logger,
    get_engine_logger,
    get_eteda_logger,
    get_logger,
    get_monitoring_logger,
)


def test_logger_name_constants():
    assert LOG_ETEDA == "runtime.eteda"
    assert LOG_ENGINE == "runtime.engine"
    assert LOG_BROKER == "runtime.broker"
    assert LOG_MONITORING == "runtime.monitoring"


def test_get_logger_returns_logger_with_name():
    log = get_logger("runtime.eteda")
    assert log.name == "runtime.eteda"


def test_get_eteda_logger():
    log = get_eteda_logger()
    assert log.name == LOG_ETEDA


def test_get_engine_logger():
    log = get_engine_logger()
    assert log.name == LOG_ENGINE


def test_get_broker_logger():
    log = get_broker_logger()
    assert log.name == LOG_BROKER


def test_get_monitoring_logger():
    log = get_monitoring_logger()
    assert log.name == LOG_MONITORING


def test_configure_central_logging_accepts_int_level():
    configure_central_logging(level=logging.DEBUG, root=False)
    for name in (LOG_ETEDA, LOG_ENGINE, LOG_BROKER, LOG_MONITORING):
        assert logging.getLogger(name).level == logging.DEBUG


def test_configure_central_logging_accepts_str_level():
    configure_central_logging(level="WARNING", root=False)
    for name in (LOG_ETEDA, LOG_ENGINE, LOG_BROKER, LOG_MONITORING):
        assert logging.getLogger(name).level == logging.WARNING


def test_configure_central_logging_root_true_sets_root_level():
    configure_central_logging(level=logging.INFO, root=True)
    assert logging.getLogger().level == logging.INFO
