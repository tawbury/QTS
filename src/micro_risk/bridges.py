"""Micro Risk Loop 브릿지 어댑터.

런타임 의존성을 MicroRiskLoop Protocol에 연결하는 어댑터 3개.
근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §2.5, §4.4, §7.1
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from src.micro_risk.dispatcher import (
    EmergencyOrderChannel,
    ETEDAController,
    SafetyNotifier,
)

_LOG = logging.getLogger("micro_risk.bridges")


class BrokerEmergencyChannel:
    """BrokerEngine → EmergencyOrderChannel Protocol 어댑터 (§2.5.3).

    긴급 주문을 P0 우선순위로 브로커에 전송한다.
    """

    def __init__(self, broker) -> None:
        self._broker = broker

    def send_emergency_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        order_type: str,
        reason: str,
    ) -> bool:
        """긴급 주문 전송."""
        try:
            from src.provider.models.intent import ExecutionIntent

            intent = ExecutionIntent(
                intent_id=f"MICRO_RISK_{uuid.uuid4().hex[:8]}",
                symbol=symbol,
                side=side,
                quantity=float(qty),
                intent_type=order_type,
                metadata={"source": "MICRO_RISK_LOOP", "reason": reason},
            )
            resp = self._broker.submit_intent(intent)
            if resp.accepted:
                _LOG.info(
                    f"Emergency order accepted: {symbol} {side} qty={qty} reason={reason}"
                )
            else:
                _LOG.error(
                    f"Emergency order rejected: {symbol} {side} qty={qty} msg={resp.message}"
                )
            return resp.accepted
        except Exception as e:
            _LOG.error(f"Emergency order failed: {symbol} {side} qty={qty} error={e}")
            return False


class ETEDALoopController:
    """ETEDA Loop 제어 어댑터 (§4.4).

    Micro Risk Loop가 ETEDA를 정지/재개할 수 있도록 한다.
    should_stop()을 ETEDA Loop의 종료 조건으로 사용한다.
    """

    def __init__(self) -> None:
        self._suspended = False
        self._suspend_reason: str = ""
        self._suspend_source: str = ""

    def suspend(
        self,
        reason: str,
        source: str,
        duration_ms: Optional[int] = None,
    ) -> bool:
        """ETEDA 정지 요청."""
        self._suspended = True
        self._suspend_reason = reason
        self._suspend_source = source
        _LOG.warning(
            f"ETEDA suspended: reason={reason}, source={source}, duration={duration_ms}ms"
        )
        return True

    def is_suspended(self) -> bool:
        """정지 상태 확인."""
        return self._suspended

    def resume(self) -> None:
        """ETEDA 재개."""
        self._suspended = False
        self._suspend_reason = ""
        _LOG.info("ETEDA resumed")

    def should_stop(self) -> bool:
        """ETEDA Loop should_stop 조건. 정지 상태면 True."""
        return self._suspended

    @property
    def suspend_reason(self) -> str:
        return self._suspend_reason


class SafetyLayerNotifier:
    """SafetyLayer → SafetyNotifier Protocol 어댑터 (§7.1).

    Micro Risk Loop 이벤트를 Safety Layer에 통보한다.
    """

    def __init__(self, safety_layer=None) -> None:
        self._safety = safety_layer

    def notify(self, code: str, message: str) -> None:
        """Safety 알림 전송."""
        _LOG.warning(f"[Safety] {code}: {message}")
        if self._safety is not None and hasattr(self._safety, "record_fail_safe"):
            try:
                self._safety.record_fail_safe(code, message, "MicroRisk")
            except Exception as e:
                _LOG.error(f"Safety notification failed: {e}")
