"""BrokerEngine → AsyncBrokerProtocol 어댑터.

기존 BrokerEngine (동기, ExecutionIntent 기반)을 ExecutionPipeline의
AsyncBrokerProtocol 인터페이스로 변환한다.
"""
from __future__ import annotations

import uuid
from typing import Optional

from src.execution.contracts import OrderAck
from src.provider.interfaces.broker import BrokerEngine
from src.provider.models.intent import ExecutionIntent


class BrokerEngineAdapter:
    """BrokerEngine → AsyncBrokerProtocol 어댑터."""

    def __init__(self, broker: BrokerEngine) -> None:
        self._broker = broker

    async def send_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        price: Optional[float],
        order_type: str,
    ) -> OrderAck:
        """AsyncBrokerProtocol.send_order 구현."""
        intent = ExecutionIntent(
            intent_id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            quantity=float(qty),
            intent_type=order_type,
            metadata={"price": price} if price is not None else {},
        )
        resp = self._broker.submit_intent(intent)
        return OrderAck(
            accepted=resp.accepted,
            order_id=resp.intent_id,
            reject_reason="" if resp.accepted else (resp.message or "rejected"),
        )

    async def cancel_order(self, order_id: str) -> bool:
        """BrokerEngine에 cancel API 없음 → False 반환."""
        return False
