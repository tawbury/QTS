#!/usr/bin/env python3
"""
Trading Engine 테스트

Engine Layer ↔ Broker Layer 분리: ExecutionIntent/Response Contract 검증.
MockBroker/NoopBroker 주입으로 계약만 검증.
"""

import pytest
from datetime import datetime

from src.strategy.engines.trading_engine import TradingEngine
from src.qts.core.config.config_models import UnifiedConfig
from src.provider.brokers.mock_broker import MockBroker
from src.provider.brokers.noop_broker import NoopBroker
from src.provider.models.intent import ExecutionIntent
from src.provider.models.response import ExecutionResponse


def _make_engine(broker):
    config = UnifiedConfig(config_map={}, metadata={})
    return TradingEngine(config=config, broker=broker)


class TestTradingEngineContract:
    """ExecutionIntent/Response Contract 및 execute() I/O 검증."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        engine = _make_engine(MockBroker())
        result = await engine.initialize()
        assert result is True
        assert engine.state.is_running is False

    @pytest.mark.asyncio
    async def test_execute_submit_intent_with_mock_accepted(self):
        """submit_intent → MockBroker(quantity>0) → accepted True, 계약 필드 존재."""
        engine = _make_engine(MockBroker())
        intent = ExecutionIntent(
            intent_id="test-1",
            symbol="AAPL",
            side="BUY",
            quantity=10.0,
            intent_type="MARKET",
        )
        result = await engine.execute({
            "operation": "submit_intent",
            "intent": intent,
        })
        assert result["success"] is True
        assert "data" in result
        assert "execution_time" in result
        data = result["data"]
        assert data["intent_id"] == "test-1"
        assert data["accepted"] is True
        assert data["broker"] == "mock-broker"
        assert "message" in data

    @pytest.mark.asyncio
    async def test_execute_submit_intent_with_mock_rejected(self):
        """quantity<=0 → MockBroker → accepted False."""
        engine = _make_engine(MockBroker())
        result = await engine.execute({
            "operation": "submit_intent",
            "intent_id": "test-2",
            "symbol": "MSFT",
            "side": "SELL",
            "quantity": 0,
            "intent_type": "MARKET",
        })
        assert result["success"] is True
        assert result["data"]["accepted"] is False
        assert result["data"]["broker"] == "mock-broker"

    @pytest.mark.asyncio
    async def test_execute_submit_intent_with_noop_broker(self):
        """NoopBroker → 항상 accepted False."""
        engine = _make_engine(NoopBroker())
        result = await engine.execute({
            "operation": "submit_intent",
            "intent_id": "noop-1",
            "symbol": "GOOG",
            "side": "BUY",
            "quantity": 5,
            "intent_type": "MARKET",
        })
        assert result["success"] is True
        assert result["data"]["accepted"] is False
        assert result["data"]["broker"] == "noop-broker"

    @pytest.mark.asyncio
    async def test_execute_unknown_operation(self):
        """Unknown operation → success False, error 필드."""
        engine = _make_engine(MockBroker())
        result = await engine.execute({"operation": "unknown"})
        assert result["success"] is False
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__])
