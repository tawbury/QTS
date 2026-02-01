"""
OrderAdapter → BrokerEngine Adapter

BaseBrokerAdapter (OrderRequest/OrderResponse)를
BrokerEngine (ExecutionIntent/ExecutionResponse) 인터페이스로 변환합니다.
"""

from __future__ import annotations

import logging
from datetime import datetime

from app.execution.clients.broker.adapters.base_adapter import BaseBrokerAdapter
from app.execution.interfaces.broker import BrokerEngine
from app.execution.models.intent import ExecutionIntent
from app.execution.models.response import ExecutionResponse
from app.execution.models.order_request import OrderRequest, OrderSide, OrderType
from app.execution.models.order_response import OrderStatus


_log = logging.getLogger(__name__)


class OrderAdapterToBrokerEngineAdapter(BrokerEngine):
    """
    OrderAdapter를 BrokerEngine으로 래핑하는 어댑터.

    ExecutionIntent → OrderRequest 변환
    OrderResponse → ExecutionResponse 변환
    """

    def __init__(self, order_adapter: BaseBrokerAdapter):
        """
        OrderAdapterToBrokerEngineAdapter 초기화

        Args:
            order_adapter: BaseBrokerAdapter 인스턴스 (KiwoomOrderAdapter 등)
        """
        self._adapter = order_adapter
        _log.info(f"OrderAdapterToBrokerEngineAdapter initialized (broker={self._adapter.broker_id})")

    def submit_intent(self, intent: ExecutionIntent) -> ExecutionResponse:
        """
        ExecutionIntent → OrderRequest 변환 → OrderAdapter.place_order() 호출

        Args:
            intent: ExecutionIntent

        Returns:
            ExecutionResponse
        """
        try:
            # 1. ExecutionIntent → OrderRequest 변환
            order_request = self._intent_to_order_request(intent)

            # 2. OrderAdapter.place_order() 호출
            order_response = self._adapter.place_order(order_request)

            # 3. OrderResponse → ExecutionResponse 변환
            execution_response = self._order_response_to_execution_response(
                order_response, intent
            )

            return execution_response

        except Exception as e:
            _log.error(f"Failed to submit intent: {e}")
            return ExecutionResponse(
                intent_id=intent.intent_id,
                accepted=False,
                broker=self._adapter.broker_id,
                message=f"Error: {str(e)}",
                timestamp=datetime.now(),
            )

    def _intent_to_order_request(self, intent: ExecutionIntent) -> OrderRequest:
        """
        ExecutionIntent → OrderRequest 변환

        Args:
            intent: ExecutionIntent

        Returns:
            OrderRequest
        """
        # side 변환
        side_map = {
            "BUY": OrderSide.BUY,
            "SELL": OrderSide.SELL,
        }
        side = side_map.get(intent.side.upper(), OrderSide.BUY)

        # order_type 변환
        type_map = {
            "MARKET": OrderType.MARKET,
            "LIMIT": OrderType.LIMIT,
        }
        order_type = type_map.get(intent.intent_type.upper(), OrderType.MARKET)

        # OrderRequest 생성
        order_request = OrderRequest(
            symbol=intent.symbol,
            side=side,
            qty=int(intent.quantity),
            order_type=order_type,
            limit_price=intent.price if intent.price else None,
            dry_run=False,  # Production에서는 실제 주문
        )

        return order_request

    def _order_response_to_execution_response(
        self, order_response, intent: ExecutionIntent
    ) -> ExecutionResponse:
        """
        OrderResponse → ExecutionResponse 변환

        Args:
            order_response: OrderResponse
            intent: ExecutionIntent (intent_id 참조용)

        Returns:
            ExecutionResponse
        """
        # accepted 판정
        accepted = order_response.status in (
            OrderStatus.ACCEPTED,
            OrderStatus.FILLED,
            OrderStatus.PARTIALLY_FILLED,
        )

        # message 구성
        message = order_response.message or f"Status: {order_response.status.value}"

        return ExecutionResponse(
            intent_id=intent.intent_id,
            accepted=accepted,
            broker=self._adapter.broker_id,
            message=message,
            timestamp=datetime.now(),
        )
