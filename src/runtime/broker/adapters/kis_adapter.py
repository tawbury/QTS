"""
KIS broker adapter.

Arch §2.2, §10.1: KIS OrderAdapter 계약 준수.
Protocol-Driven: KISClient 주입으로 실제 API 호출부 분리 → 테스트 용이성.
"""

from __future__ import annotations

from typing import Optional

from runtime.broker.adapters.base_adapter import BaseBrokerAdapter
from runtime.broker.adapters.protocols import OrderClientProtocol
from runtime.broker.kis.payload_mapping import (
    build_kis_order_payload,
    parse_kis_place_response,
    raw_to_order_response,
)
from runtime.broker.order_base import OrderQuery
from runtime.execution.models.order_request import OrderRequest
from runtime.execution.models.order_response import OrderResponse, OrderStatus


class KISOrderAdapter(BaseBrokerAdapter):
    """
    KIS order adapter.

    Same contract as Kiwoom: place_order, get_order, cancel_order.
    client 주입 시 payload_mapping으로 KIS REST API 호출.
    client 미주입 시 스텁(테스트/개발용).
    """

    def __init__(
        self,
        client: Optional[OrderClientProtocol] = None,
        *,
        acnt_no: str = "",
        acnt_prdt_cd: str = "01",
    ) -> None:
        """
        KISOrderAdapter 초기화

        Args:
            client: KISClient 인스턴스 (Optional)
            acnt_no: 계좌번호
            acnt_prdt_cd: 계좌상품코드
        """
        self._client = client
        self._acnt_no = acnt_no
        self._acnt_prdt_cd = acnt_prdt_cd

    @property
    def broker_id(self) -> str:
        return "kis"

    def name(self) -> str:
        return "KIS"

    def place_order(self, req: OrderRequest) -> OrderResponse:
        """주문 전송"""
        if req.dry_run:
            return self._dry_run_response("KIS-VIRTUAL")
        if self._client is None:
            return self._stub_rejected()

        # OrderRequest → KIS Payload 변환
        payload = build_kis_order_payload(
            req,
            cano=self._acnt_no,
            acnt_prdt_cd=self._acnt_prdt_cd,
            market="KR",
        )

        # DEBUG: Log payload
        import logging
        _log = logging.getLogger(__name__)
        _log.info(f"KIS Order Payload: {payload}")

        # KIS API 호출
        resp = self._client.place_order(payload)

        # 응답 파싱
        status, broker_order_id, message = parse_kis_place_response(resp)

        if status == OrderStatus.REJECTED:
            return OrderResponse(
                status=status,
                broker_order_id=broker_order_id,
                message=message,
                raw=resp,
            )

        return OrderResponse(
            status=status,
            broker_order_id=broker_order_id,
            message=message,
            raw=resp,
        )

    def get_order(self, query: OrderQuery) -> OrderResponse:
        """주문 조회"""
        if self._client is None:
            return self._stub_unknown(query)
        resp = self._client.get_order({"order_id": query.broker_order_id})
        return raw_to_order_response(resp, default_broker_order_id=query.broker_order_id)

    def cancel_order(self, query: OrderQuery) -> OrderResponse:
        """주문 취소"""
        if self._client is None:
            return self._stub_unknown(query)
        resp = self._client.cancel_order({"order_id": query.broker_order_id})

        # 응답 코드 확인
        rt_cd = resp.get("rt_cd", -1)
        if isinstance(rt_cd, str) and rt_cd.isdigit():
            rt_cd = int(rt_cd)

        ok = rt_cd == 0 or str(rt_cd) == "0"

        return OrderResponse(
            status=OrderStatus.CANCELED if ok else OrderStatus.UNKNOWN,
            broker_order_id=query.broker_order_id,
            message=resp.get("msg1") or resp.get("message"),
            raw=resp,
        )
