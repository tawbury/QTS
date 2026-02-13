"""BrokerEngineAdapter 단위 테스트."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

try:
    from src.execution.broker_adapter import BrokerEngineAdapter
    from src.execution.contracts import OrderAck
    from src.provider.models.response import ExecutionResponse
    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False

pytestmark = pytest.mark.skipif(
    not _HAS_DEPS,
    reason="Execution dependencies not installed",
)


class _MockBroker:
    NAME = "mock-broker"

    def __init__(self, *, accept: bool = True):
        self._accept = accept

    def submit_intent(self, intent):
        return ExecutionResponse(
            intent_id=intent.intent_id,
            accepted=self._accept,
            broker=self.NAME,
            message="ok" if self._accept else "rejected",
        )


class TestBrokerEngineAdapter:

    @pytest.mark.asyncio
    async def test_send_order_accepted(self):
        adapter = BrokerEngineAdapter(_MockBroker(accept=True))
        ack = await adapter.send_order("005930", "BUY", 10, 75000.0, "MARKET")
        assert isinstance(ack, OrderAck)
        assert ack.accepted is True
        assert ack.order_id != ""

    @pytest.mark.asyncio
    async def test_send_order_rejected(self):
        adapter = BrokerEngineAdapter(_MockBroker(accept=False))
        ack = await adapter.send_order("005930", "BUY", 10, 75000.0, "MARKET")
        assert ack.accepted is False
        assert ack.reject_reason != ""

    @pytest.mark.asyncio
    async def test_cancel_order_returns_false(self):
        adapter = BrokerEngineAdapter(_MockBroker(accept=True))
        result = await adapter.cancel_order("some-order-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_order_no_price(self):
        adapter = BrokerEngineAdapter(_MockBroker(accept=True))
        ack = await adapter.send_order("005930", "BUY", 10, None, "MARKET")
        assert ack.accepted is True
