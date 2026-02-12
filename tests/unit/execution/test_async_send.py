"""AsyncSend Stage 테스트."""
import asyncio
from decimal import Decimal

import pytest

from src.execution.contracts import OrderAck, SplitOrder, SplitOrderStatus
from src.execution.stages.async_send import AsyncSendStage
from src.provider.models.order_request import OrderSide, OrderType


class MockBroker:
    """성공하는 Mock 브로커."""

    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0

    async def send_order(self, symbol, side, qty, price, order_type):
        self.call_count += 1
        if self.responses:
            resp = self.responses.pop(0)
            if isinstance(resp, Exception):
                raise resp
            return resp
        return OrderAck(accepted=True, order_id=f"ORD-{self.call_count}")

    async def cancel_order(self, order_id):
        return True


class FailBroker:
    """항상 실패하는 Mock 브로커."""

    async def send_order(self, symbol, side, qty, price, order_type):
        raise ConnectionError("broker down")

    async def cancel_order(self, order_id):
        return False


def _make_split(qty=100, seq=1) -> SplitOrder:
    return SplitOrder(
        split_id=f"split-{seq}",
        parent_order_id="parent-1",
        sequence=seq,
        symbol="005930",
        side=OrderSide.BUY,
        qty=qty,
        price=Decimal("75000"),
        price_type=OrderType.LIMIT,
    )


class TestSuccessfulSend:
    def test_single_order(self):
        broker = MockBroker()
        stage = AsyncSendStage(broker)
        splits = [_make_split()]

        result, alerts = asyncio.run(stage.execute(splits))
        assert result.sent_count == 1
        assert result.failed_count == 0
        assert splits[0].status == SplitOrderStatus.SENT
        assert splits[0].broker_order_id == "ORD-1"

    def test_multiple_orders(self):
        broker = MockBroker()
        stage = AsyncSendStage(broker)
        splits = [_make_split(seq=i) for i in range(3)]

        result, alerts = asyncio.run(stage.execute(splits))
        assert result.sent_count == 3
        assert result.failed_count == 0


class TestFailedSend:
    def test_all_fail_triggers_fs090(self):
        broker = FailBroker()
        stage = AsyncSendStage(broker, max_retries=2)
        splits = [_make_split()]

        result, alerts = asyncio.run(stage.execute(splits))
        assert result.sent_count == 0
        assert result.failed_count == 1
        assert splits[0].status == SplitOrderStatus.FAILED
        assert any(a.code == "FS090" for a in alerts)

    def test_partial_failure(self):
        broker = MockBroker(responses=[
            OrderAck(accepted=True, order_id="ORD-1"),
            ConnectionError("timeout"),
            ConnectionError("timeout"),
            ConnectionError("timeout"),
        ])
        stage = AsyncSendStage(broker, max_retries=1)
        splits = [_make_split(seq=1), _make_split(seq=2)]

        result, alerts = asyncio.run(stage.execute(splits))
        assert result.sent_count == 1
        assert result.failed_count == 1


class TestRetry:
    def test_retry_then_success(self):
        broker = MockBroker(responses=[
            ConnectionError("timeout"),
            ConnectionError("timeout"),
            OrderAck(accepted=True, order_id="ORD-1"),
        ])
        stage = AsyncSendStage(broker, max_retries=3)
        splits = [_make_split()]

        result, alerts = asyncio.run(stage.execute(splits))
        assert result.sent_count == 1
        assert broker.call_count == 3

    def test_rejected_order(self):
        broker = MockBroker(responses=[
            OrderAck(accepted=False, reject_reason="INVALID_PRICE"),
            OrderAck(accepted=False, reject_reason="INVALID_PRICE"),
            OrderAck(accepted=False, reject_reason="INVALID_PRICE"),
        ])
        stage = AsyncSendStage(broker, max_retries=3)
        splits = [_make_split()]

        result, alerts = asyncio.run(stage.execute(splits))
        assert result.sent_count == 0
        assert result.failed_count == 1
