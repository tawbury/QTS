import os

from src.qts.core.config.execution_mode import ExecutionMode
from src.provider.brokers.live_broker import LiveBroker
from src.provider.brokers.mock_broker import MockBroker
from src.qts.core.config.execution_mode import decide_execution_mode


def _select_engine(sheet_mode, sheet_enabled, ack):
    d = decide_execution_mode(sheet_mode, sheet_enabled, ack)
    return LiveBroker if d.live_allowed else MockBroker


def test_runner_selects_mock_by_default():
    engine = _select_engine("PAPER", "1", None)
    assert engine is MockBroker


def test_runner_blocks_live_without_ack(monkeypatch):
    monkeypatch.delenv("QTS_LIVE_ACK", raising=False)
    engine = _select_engine("LIVE", "1", None)
    assert engine is MockBroker


def test_runner_allows_live_with_ack(monkeypatch):
    monkeypatch.setenv("QTS_LIVE_ACK", "I_UNDERSTAND_LIVE_TRADING")
    engine = _select_engine("LIVE", "true", "I_UNDERSTAND_LIVE_TRADING")
    assert engine is LiveBroker
