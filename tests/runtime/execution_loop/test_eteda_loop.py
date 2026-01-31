"""ETEDA Loop policy and run_eteda_loop (Phase 5 – Trigger & Loop Control)."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

import pytest

from runtime.config.config_models import UnifiedConfig
from runtime.execution_loop.eteda_loop import run_eteda_loop
from runtime.execution_loop.eteda_loop_policy import (
    ETEDALoopPolicy,
    default_should_stop_from_config,
)


def test_eteda_loop_policy_from_config_defaults():
    config = UnifiedConfig(config_map={}, metadata={})
    policy = ETEDALoopPolicy.from_config(config)
    assert policy.interval_ms == 1000
    assert policy.error_backoff_ms == 5000
    assert policy.error_backoff_max_retries == 3
    assert policy.no_overlap is True


def test_eteda_loop_policy_from_config_custom():
    config = UnifiedConfig(
        config_map={
            "INTERVAL_MS": "2000",
            "ERROR_BACKOFF_MS": "3000",
            "ERROR_BACKOFF_MAX_RETRIES": "5",
        },
        metadata={},
    )
    policy = ETEDALoopPolicy.from_config(config)
    assert policy.interval_ms == 2000
    assert policy.error_backoff_ms == 3000
    assert policy.error_backoff_max_retries == 5


def test_default_should_stop_from_config_false():
    config = UnifiedConfig(config_map={}, metadata={})
    stop = default_should_stop_from_config(config)
    assert stop() is False
    config2 = UnifiedConfig(config_map={"PIPELINE_PAUSED": "0"}, metadata={})
    stop2 = default_should_stop_from_config(config2)
    assert stop2() is False


def test_default_should_stop_from_config_true():
    config = UnifiedConfig(config_map={"PIPELINE_PAUSED": "1"}, metadata={})
    stop = default_should_stop_from_config(config)
    assert stop() is True
    config2 = UnifiedConfig(config_map={"pipeline_paused": "true"}, metadata={})
    stop2 = default_should_stop_from_config(config2)
    assert stop2() is True


@pytest.mark.asyncio
async def test_run_eteda_loop_stops_when_should_stop_immediate():
    """루프는 should_stop이 True면 run_once 없이 즉시 종료."""
    call_count = 0

    class FakeRunner:
        async def run_once(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return {"status": "ok"}

    config = UnifiedConfig(config_map={"PIPELINE_PAUSED": "1"}, metadata={})
    await run_eteda_loop(FakeRunner(), config)
    assert call_count == 0


@pytest.mark.asyncio
async def test_run_eteda_loop_stops_after_max_consecutive_errors():
    """연속 예외가 ERROR_BACKOFF_MAX_RETRIES 초과 시 루프 안전 중단."""
    call_count = 0

    class FailingRunner:
        async def run_once(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("simulated failure")

    config = UnifiedConfig(
        config_map={
            "INTERVAL_MS": "10000",
            "ERROR_BACKOFF_MS": "50",
            "ERROR_BACKOFF_MAX_RETRIES": "2",
        },
        metadata={},
    )
    await run_eteda_loop(FailingRunner(), config)
    assert call_count == 3  # 1 + retry 1 + retry 2, then stop
