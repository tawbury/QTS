"""BrokerEngine → AsyncBrokerProtocol 어댑터.

기존 BrokerEngine (동기, ExecutionIntent 기반)을 ExecutionPipeline의
AsyncBrokerProtocol 인터페이스로 변환한다.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from src.execution.contracts import CancelAck, ModifyAck, OrderAck
from src.provider.interfaces.broker import BrokerEngine
from src.provider.models.intent import ExecutionIntent

logger = logging.getLogger(__name__)

# 최근 주문 정보를 캐싱하기 위한 타입 (cancel→re-send 패턴에서 사용)
_OrderInfo = dict  # {"symbol": str, "side": str, "qty": int, "price": float|None, "order_type": str}


class BrokerEngineAdapter:
    """BrokerEngine → AsyncBrokerProtocol 어댑터."""

    def __init__(self, broker: BrokerEngine) -> None:
        self._broker = broker
        # 주문 정보 캐시: order_id → 주문 파라미터 (modify 시 cancel→re-send에 필요)
        self._order_cache: dict[str, _OrderInfo] = {}

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
        ack = OrderAck(
            accepted=resp.accepted,
            order_id=resp.intent_id,
            reject_reason="" if resp.accepted else (resp.message or "rejected"),
        )
        # 주문 성공 시 캐시에 저장 (modify 시 cancel→re-send에 필요)
        if ack.accepted:
            self._order_cache[ack.order_id] = {
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "price": price,
                "order_type": order_type,
            }
        return ack

    async def cancel_order(self, order_id: str) -> CancelAck:
        """주문 취소. BrokerEngine에 cancel API가 없으므로 best-effort 수락 처리."""
        logger.info("주문 취소 요청: order_id=%s (best-effort)", order_id)
        # BrokerEngine 인터페이스에 cancel API가 없으므로 best-effort 수락
        # 캐시에서 해당 주문 정보 제거
        self._order_cache.pop(order_id, None)
        return CancelAck(accepted=True, order_id=order_id)

    async def modify_order(
        self,
        order_id: str,
        *,
        new_price: Optional[float] = None,
        new_qty: Optional[int] = None,
    ) -> ModifyAck:
        """주문 수정. BrokerEngine에 modify API가 없으므로 취소 후 재주문(cancel→re-send) 패턴."""
        # 1. 원본 주문 정보를 cancel 전에 보관 (cancel_order가 캐시를 제거하므로)
        original = self._order_cache.get(order_id)
        if original is None:
            logger.warning("주문 수정 실패: 원본 주문 정보 없음 order_id=%s", order_id)
            return ModifyAck(
                accepted=False,
                order_id=order_id,
                reject_reason="원본 주문 정보 없음 (캐시 미스)",
            )

        # 2. 기존 주문 취소 시도
        cancel_ack = await self.cancel_order(order_id)
        if not cancel_ack.accepted:
            logger.warning("주문 수정 실패: 기존 주문 취소 거부 order_id=%s", order_id)
            return ModifyAck(
                accepted=False,
                order_id=order_id,
                reject_reason=f"취소 실패: {cancel_ack.reject_reason}",
            )

        # 3. 새 조건으로 재주문
        send_price = new_price if new_price is not None else original["price"]
        send_qty = new_qty if new_qty is not None else original["qty"]

        new_ack = await self.send_order(
            symbol=original["symbol"],
            side=original["side"],
            qty=send_qty,
            price=send_price,
            order_type=original["order_type"],
        )

        if not new_ack.accepted:
            logger.warning(
                "주문 수정 실패: 재주문 거부 order_id=%s, reason=%s",
                order_id,
                new_ack.reject_reason,
            )
            return ModifyAck(
                accepted=False,
                order_id=new_ack.order_id or order_id,
                reject_reason=f"재주문 거부: {new_ack.reject_reason}",
            )

        logger.info(
            "주문 수정 완료: old_id=%s → new_id=%s",
            order_id,
            new_ack.order_id,
        )
        return ModifyAck(
            accepted=True,
            order_id=new_ack.order_id,
        )
