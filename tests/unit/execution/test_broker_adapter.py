"""BrokerEngineAdapter 단위 테스트."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

try:
    from src.execution.broker_adapter import BrokerEngineAdapter
    from src.execution.contracts import CancelAck, ModifyAck, OrderAck
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
    async def test_cancel_order_returns_cancel_ack(self):
        adapter = BrokerEngineAdapter(_MockBroker(accept=True))
        result = await adapter.cancel_order("some-order-id")
        assert isinstance(result, CancelAck)
        assert result.accepted is True
        assert result.order_id == "some-order-id"

    @pytest.mark.asyncio
    async def test_cancel_order_removes_cache(self):
        adapter = BrokerEngineAdapter(_MockBroker(accept=True))
        # send_order로 캐시 생성
        ack = await adapter.send_order("005930", "BUY", 10, 75000.0, "LIMIT")
        assert ack.order_id in adapter._order_cache
        # cancel_order로 캐시 제거 확인
        await adapter.cancel_order(ack.order_id)
        assert ack.order_id not in adapter._order_cache

    @pytest.mark.asyncio
    async def test_send_order_no_price(self):
        adapter = BrokerEngineAdapter(_MockBroker(accept=True))
        ack = await adapter.send_order("005930", "BUY", 10, None, "MARKET")
        assert ack.accepted is True

    @pytest.mark.asyncio
    async def test_modify_order_success(self):
        adapter = BrokerEngineAdapter(_MockBroker(accept=True))
        # 먼저 주문 전송하여 캐시 생성
        ack = await adapter.send_order("005930", "BUY", 10, 75000.0, "LIMIT")
        old_order_id = ack.order_id

        # 가격 수정
        modify_ack = await adapter.modify_order(old_order_id, new_price=76000.0)
        assert isinstance(modify_ack, ModifyAck)
        assert modify_ack.accepted is True
        assert modify_ack.order_id != ""
        # 새 주문 ID는 기존과 다름 (cancel→re-send이므로)
        assert modify_ack.order_id != old_order_id

    @pytest.mark.asyncio
    async def test_modify_order_with_new_qty(self):
        adapter = BrokerEngineAdapter(_MockBroker(accept=True))
        ack = await adapter.send_order("005930", "BUY", 10, 75000.0, "LIMIT")

        modify_ack = await adapter.modify_order(ack.order_id, new_qty=20)
        assert modify_ack.accepted is True
        assert modify_ack.order_id != ""

    @pytest.mark.asyncio
    async def test_modify_order_no_cache_fails(self):
        adapter = BrokerEngineAdapter(_MockBroker(accept=True))
        # 캐시에 없는 주문 수정 시도
        modify_ack = await adapter.modify_order("nonexistent-order")
        assert modify_ack.accepted is False
        assert "캐시 미스" in modify_ack.reject_reason

    @pytest.mark.asyncio
    async def test_modify_order_resend_rejected(self):
        """cancel 성공 후 재주문이 거부되는 경우."""
        broker = _MockBroker(accept=True)
        adapter = BrokerEngineAdapter(broker)

        # 먼저 주문 전송
        ack = await adapter.send_order("005930", "BUY", 10, 75000.0, "LIMIT")

        # 재주문 시 거부되도록 브로커 상태 변경
        broker._accept = False
        modify_ack = await adapter.modify_order(ack.order_id, new_price=76000.0)
        assert modify_ack.accepted is False
        assert "재주문 거부" in modify_ack.reject_reason

    @pytest.mark.asyncio
    async def test_send_order_caches_info(self):
        adapter = BrokerEngineAdapter(_MockBroker(accept=True))
        ack = await adapter.send_order("005930", "BUY", 10, 75000.0, "LIMIT")
        assert ack.order_id in adapter._order_cache
        cached = adapter._order_cache[ack.order_id]
        assert cached["symbol"] == "005930"
        assert cached["side"] == "BUY"
        assert cached["qty"] == 10
        assert cached["price"] == 75000.0
        assert cached["order_type"] == "LIMIT"
