"""OrderSplit Stage 테스트."""
from decimal import Decimal

import pytest

from src.execution.contracts import OrderDecision, SplitConfig, SplitStrategy
from src.execution.stages.order_split import OrderSplitStage
from src.provider.models.order_request import OrderSide, OrderType


@pytest.fixture
def stage():
    return OrderSplitStage()


@pytest.fixture
def small_order():
    return OrderDecision(
        symbol="005930", side=OrderSide.BUY, qty=50,
        price=Decimal("75000"), order_type=OrderType.LIMIT,
    )


@pytest.fixture
def medium_order():
    return OrderDecision(
        symbol="005930", side=OrderSide.BUY, qty=500,
        price=Decimal("75000"), order_type=OrderType.LIMIT,
    )


@pytest.fixture
def large_order():
    return OrderDecision(
        symbol="005930", side=OrderSide.BUY, qty=5000,
        price=Decimal("75000"), order_type=OrderType.LIMIT,
    )


class TestSingleStrategy:
    def test_small_order_no_split(self, stage, small_order):
        result, alerts = stage.execute(small_order)
        assert result.strategy == SplitStrategy.SINGLE
        assert len(result.splits) == 1
        assert result.splits[0].qty == 50
        assert result.total_qty == 50

    def test_exact_threshold(self):
        stage = OrderSplitStage(SplitConfig(min_split_qty=100))
        order = OrderDecision(
            symbol="005930", side=OrderSide.BUY, qty=100,
            price=Decimal("75000"),
        )
        result, _ = stage.execute(order)
        assert result.strategy == SplitStrategy.SINGLE


class TestTWAPSplit:
    def test_medium_order_twap(self, stage, medium_order):
        result, alerts = stage.execute(medium_order)
        assert result.strategy == SplitStrategy.TWAP
        assert len(result.splits) == 5  # default twap_num_buckets
        assert result.total_qty == 500

    def test_qty_preserved(self, stage, medium_order):
        result, _ = stage.execute(medium_order)
        assert sum(s.qty for s in result.splits) == 500

    def test_all_splits_have_parent_id(self, stage, medium_order):
        result, _ = stage.execute(medium_order)
        for s in result.splits:
            assert s.parent_order_id == medium_order.order_id

    def test_sequences_ordered(self, stage, medium_order):
        result, _ = stage.execute(medium_order)
        seqs = [s.sequence for s in result.splits]
        assert seqs == sorted(seqs)


class TestIcebergSplit:
    def test_large_order_iceberg(self, stage, large_order):
        result, alerts = stage.execute(large_order)
        assert result.strategy == SplitStrategy.ICEBERG
        assert result.total_qty == 5000
        # visible = 30% of 5000 = 1500 per chunk
        assert len(result.splits) >= 3


class TestGR060SplitLimit:
    def test_too_many_splits_consolidates(self):
        config = SplitConfig(
            min_split_qty=10, max_splits=5,
            iceberg_visible_pct=Decimal("0.05"),
        )
        stage = OrderSplitStage(config)
        order = OrderDecision(
            symbol="005930", side=OrderSide.BUY, qty=1000,
            price=Decimal("75000"),
        )
        result, alerts = stage.execute(order)
        assert len(result.splits) <= 5
        assert result.total_qty == 1000
        assert any(a.code == "GR060" for a in alerts)


class TestCustomQty:
    def test_adjusted_qty(self, stage):
        order = OrderDecision(
            symbol="005930", side=OrderSide.BUY, qty=500,
            price=Decimal("75000"),
        )
        result, _ = stage.execute(order, qty=200)
        assert result.strategy == SplitStrategy.TWAP
        assert result.total_qty == 200


class TestUrgentOrder:
    def test_urgent_uses_twap(self, stage):
        order = OrderDecision(
            symbol="005930", side=OrderSide.BUY, qty=5000,
            price=Decimal("75000"), urgency="URGENT",
        )
        result, _ = stage.execute(order)
        assert result.strategy == SplitStrategy.TWAP
