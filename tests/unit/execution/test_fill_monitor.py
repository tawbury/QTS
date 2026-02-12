"""FillMonitor Stage 테스트."""
from decimal import Decimal

import pytest

from src.execution.contracts import FillEvent, SplitOrder, SplitOrderStatus
from src.execution.stages.fill_monitor import FillMonitorStage
from src.provider.models.order_request import OrderSide, OrderType


def _make_order(broker_id="ORD-1", qty=100) -> SplitOrder:
    s = SplitOrder(
        split_id="a", parent_order_id="p", sequence=1,
        symbol="005930", side=OrderSide.BUY, qty=qty,
        status=SplitOrderStatus.SENT,
    )
    s.broker_order_id = broker_id
    return s


def _make_fill(order_id="ORD-1", qty=50, price="75000") -> FillEvent:
    return FillEvent(
        order_id=order_id, symbol="005930", side=OrderSide.BUY,
        filled_qty=qty, filled_price=Decimal(price),
    )


class TestCompleteFill:
    def test_all_filled(self):
        stage = FillMonitorStage()
        orders = [_make_order("ORD-1", 100)]
        fills = [_make_fill("ORD-1", 100)]

        result, alerts = stage.process_fills(orders, fills)
        assert result.status == "COMPLETE"
        assert result.filled_qty == 100
        assert result.remaining_qty == 0
        assert orders[0].status == SplitOrderStatus.FILLED

    def test_multiple_fills_complete(self):
        stage = FillMonitorStage()
        orders = [_make_order("ORD-1", 100)]
        fills = [
            _make_fill("ORD-1", 40, "75000"),
            _make_fill("ORD-1", 60, "75100"),
        ]

        result, alerts = stage.process_fills(orders, fills)
        assert result.status == "COMPLETE"
        assert result.filled_qty == 100
        assert orders[0].avg_fill_price is not None


class TestPartialFill:
    def test_partial_status(self):
        stage = FillMonitorStage()
        orders = [_make_order("ORD-1", 100)]
        fills = [_make_fill("ORD-1", 60)]

        result, alerts = stage.process_fills(orders, fills)
        assert result.status == "PARTIAL"
        assert result.filled_qty == 60
        assert result.remaining_qty == 40
        assert orders[0].status == SplitOrderStatus.PARTIALLY_FILLED


class TestNoFills:
    def test_needs_adjustment(self):
        stage = FillMonitorStage()
        orders = [_make_order("ORD-1", 100)]
        fills = []

        result, alerts = stage.process_fills(orders, fills)
        assert result.status == "NEEDS_ADJUSTMENT"
        assert result.filled_qty == 0
        assert any(a.code == "GR064" for a in alerts)


class TestMultipleOrders:
    def test_mixed_fills(self):
        stage = FillMonitorStage()
        orders = [
            _make_order("ORD-1", 100),
            _make_order("ORD-2", 200),
        ]
        fills = [
            _make_fill("ORD-1", 100),  # ORD-1 완전 체결
            _make_fill("ORD-2", 50),   # ORD-2 부분 체결
        ]

        result, alerts = stage.process_fills(orders, fills)
        assert result.status == "PARTIAL"
        assert result.filled_qty == 150
        assert result.remaining_qty == 150
        assert orders[0].status == SplitOrderStatus.FILLED
        assert orders[1].status == SplitOrderStatus.PARTIALLY_FILLED

    def test_all_orders_filled(self):
        stage = FillMonitorStage()
        orders = [
            _make_order("ORD-1", 100),
            _make_order("ORD-2", 200),
        ]
        fills = [
            _make_fill("ORD-1", 100),
            _make_fill("ORD-2", 200),
        ]

        result, alerts = stage.process_fills(orders, fills)
        assert result.status == "COMPLETE"
        assert result.filled_qty == 300


class TestAvgFillPrice:
    def test_weighted_average(self):
        stage = FillMonitorStage()
        orders = [_make_order("ORD-1", 100)]
        fills = [
            _make_fill("ORD-1", 40, "75000"),
            _make_fill("ORD-1", 60, "76000"),
        ]

        result, _ = stage.process_fills(orders, fills)
        # (40*75000 + 60*76000) / 100 = (3000000 + 4560000) / 100 = 75600
        assert orders[0].avg_fill_price == Decimal("75600")
