"""Stage 2: OrderSplit — 주문 분할."""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from src.execution.contracts import (
    ExecutionAlert,
    OrderDecision,
    SplitConfig,
    SplitOrder,
    SplitResult,
    SplitStrategy,
)


class OrderSplitStage:
    """주문 분할 단계."""

    def __init__(self, config: Optional[SplitConfig] = None) -> None:
        self.config = config or SplitConfig()

    def execute(
        self, order: OrderDecision, qty: Optional[int] = None
    ) -> tuple[SplitResult, list[ExecutionAlert]]:
        alerts: list[ExecutionAlert] = []
        effective_qty = qty if qty is not None else order.qty

        # 분할 불필요
        if effective_qty <= self.config.min_split_qty:
            split = self._make_split(order, effective_qty, 1, order.price)
            return SplitResult(strategy=SplitStrategy.SINGLE, splits=[split]), alerts

        # 전략 선택
        strategy = self._select_strategy(order, effective_qty)

        if strategy == SplitStrategy.TWAP:
            splits = self._twap_split(order, effective_qty)
        elif strategy == SplitStrategy.ICEBERG:
            splits = self._iceberg_split(order, effective_qty)
        else:
            # VWAP은 외부 거래량 프로파일 필요 → TWAP fallback
            splits = self._twap_split(order, effective_qty)
            strategy = SplitStrategy.TWAP

        # GR060: 분할 수 제한
        if len(splits) > self.config.max_splits:
            alerts.append(ExecutionAlert(
                code="GR060",
                severity="GUARDRAIL",
                message=f"Split count {len(splits)} exceeds max {self.config.max_splits}, consolidating",
                stage="SPLITTING",
            ))
            splits = self._consolidate_splits(splits, order, self.config.max_splits)

        return SplitResult(strategy=strategy, splits=splits), alerts

    def _select_strategy(self, order: OrderDecision, qty: int) -> SplitStrategy:
        if order.urgency == "URGENT":
            return SplitStrategy.TWAP
        if qty > self.config.min_split_qty * 10:
            return SplitStrategy.ICEBERG
        return SplitStrategy.TWAP

    def _twap_split(self, order: OrderDecision, qty: int) -> list[SplitOrder]:
        num = min(self.config.twap_num_buckets, qty)
        base_qty = qty // num
        remainder = qty % num
        splits: list[SplitOrder] = []
        for i in range(num):
            bucket_qty = base_qty + (1 if i < remainder else 0)
            if bucket_qty > 0:
                splits.append(self._make_split(order, bucket_qty, i + 1, order.price))
        return splits

    def _iceberg_split(self, order: OrderDecision, qty: int) -> list[SplitOrder]:
        visible = max(1, int(qty * float(self.config.iceberg_visible_pct)))
        splits: list[SplitOrder] = []
        remaining = qty
        seq = 1
        while remaining > 0:
            chunk = min(visible, remaining)
            splits.append(self._make_split(order, chunk, seq, order.price))
            remaining -= chunk
            seq += 1
        return splits

    def _make_split(
        self, order: OrderDecision, qty: int, seq: int, price: Optional[Decimal]
    ) -> SplitOrder:
        return SplitOrder(
            split_id=str(uuid.uuid4()),
            parent_order_id=order.order_id,
            sequence=seq,
            symbol=order.symbol,
            side=order.side,
            qty=qty,
            price=price,
            price_type=order.order_type,
        )

    def _consolidate_splits(
        self, splits: list[SplitOrder], order: OrderDecision, max_n: int
    ) -> list[SplitOrder]:
        total = sum(s.qty for s in splits)
        base = total // max_n
        remainder = total % max_n
        result: list[SplitOrder] = []
        for i in range(max_n):
            q = base + (1 if i < remainder else 0)
            if q > 0:
                result.append(self._make_split(order, q, i + 1, order.price))
        return result
