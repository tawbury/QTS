"""Action Dispatcher.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §2.5
- 평가 결과에 따른 액션 실행
- Protocol 기반 외부 의존성 주입
"""
from __future__ import annotations

from typing import Optional, Protocol

from src.micro_risk.contracts import (
    ActionType,
    MicroRiskAction,
    MicroRiskAlert,
    PositionShadow,
)
from src.micro_risk.shadow_manager import PositionShadowManager


# --- Protocol Dependencies ---

class EmergencyOrderChannel(Protocol):
    """긴급 주문 채널."""

    def send_emergency_order(
        self, symbol: str, side: str, qty: int, order_type: str, reason: str,
    ) -> bool: ...


class ETEDAController(Protocol):
    """ETEDA 파이프라인 제어."""

    def suspend(self, reason: str, source: str, duration_ms: Optional[int] = None) -> bool: ...

    def is_suspended(self) -> bool: ...


class SafetyNotifier(Protocol):
    """Safety 알림."""

    def notify(self, code: str, message: str) -> None: ...


# --- Noop Defaults ---

class NoopOrderChannel:
    """테스트용 Noop 주문 채널."""

    def __init__(self) -> None:
        self.orders: list[dict] = []

    def send_emergency_order(
        self, symbol: str, side: str, qty: int, order_type: str, reason: str,
    ) -> bool:
        self.orders.append({
            "symbol": symbol, "side": side, "qty": qty,
            "order_type": order_type, "reason": reason,
        })
        return True


class NoopETEDAController:
    """테스트용 Noop ETEDA 컨트롤러."""

    def __init__(self) -> None:
        self._suspended = False
        self.suspend_reasons: list[str] = []

    def suspend(self, reason: str, source: str, duration_ms: Optional[int] = None) -> bool:
        self._suspended = True
        self.suspend_reasons.append(reason)
        return True

    def is_suspended(self) -> bool:
        return self._suspended


class NoopSafetyNotifier:
    """테스트용 Noop Safety 알림."""

    def __init__(self) -> None:
        self.notifications: list[tuple[str, str]] = []

    def notify(self, code: str, message: str) -> None:
        self.notifications.append((code, message))


# --- Action Dispatcher ---

class ActionDispatcher:
    """액션 디스패처 (§2.5.3)."""

    def __init__(
        self,
        shadow_manager: PositionShadowManager,
        order_channel: Optional[EmergencyOrderChannel] = None,
        eteda_controller: Optional[ETEDAController] = None,
        safety_notifier: Optional[SafetyNotifier] = None,
    ) -> None:
        self._shadows = shadow_manager
        self._orders = order_channel or NoopOrderChannel()
        self._eteda = eteda_controller or NoopETEDAController()
        self._safety = safety_notifier or NoopSafetyNotifier()
        self._frozen_symbols: set[str] = set()
        self._dispatch_log: list[MicroRiskAction] = []

    @property
    def dispatch_log(self) -> list[MicroRiskAction]:
        return list(self._dispatch_log)

    @property
    def frozen_symbols(self) -> frozenset[str]:
        return frozenset(self._frozen_symbols)

    def dispatch(self, action: MicroRiskAction) -> list[MicroRiskAlert]:
        """액션 디스패치."""
        self._dispatch_log.append(action)
        alerts: list[MicroRiskAlert] = []

        if action.action_type == ActionType.TRAILING_STOP_ADJUST:
            self._adjust_trailing_stop(action)

        elif action.action_type == ActionType.PARTIAL_EXIT:
            alerts.extend(self._execute_partial_exit(action))

        elif action.action_type == ActionType.FULL_EXIT:
            alerts.extend(self._execute_full_exit(action))

        elif action.action_type == ActionType.POSITION_FREEZE:
            self._freeze_position(action)

        elif action.action_type == ActionType.ETEDA_SUSPEND:
            alerts.extend(self._suspend_eteda(action))

        elif action.action_type == ActionType.KILL_SWITCH:
            alerts.extend(self._execute_kill_switch(action))

        return alerts

    def _adjust_trailing_stop(self, action: MicroRiskAction) -> None:
        """트레일링 스탑 조정 (§5.1)."""
        shadow = self._shadows.get(action.symbol)
        if shadow is not None:
            new_stop = action.payload.get("new_stop")
            if new_stop is not None:
                shadow.trailing_stop_price = new_stop

    def _execute_partial_exit(self, action: MicroRiskAction) -> list[MicroRiskAlert]:
        """부분 청산 (§5.2)."""
        alerts: list[MicroRiskAlert] = []
        qty = action.payload.get("qty", 0)
        reason = action.payload.get("reason", "PARTIAL_EXIT")

        success = self._orders.send_emergency_order(
            symbol=action.symbol, side="SELL", qty=qty,
            order_type="MARKET", reason=reason,
        )

        if success:
            shadow = self._shadows.get(action.symbol)
            if shadow is not None:
                shadow.qty -= qty
            alerts.append(MicroRiskAlert(
                code="FS102",
                message=f"Partial exit: {action.symbol} qty={qty}",
                severity="WARNING",
            ))
        else:
            alerts.append(MicroRiskAlert(
                code="GR074",
                message=f"Emergency order failed: {action.symbol}",
                severity="CRITICAL",
            ))

        return alerts

    def _execute_full_exit(self, action: MicroRiskAction) -> list[MicroRiskAlert]:
        """전량 청산 (§5.3)."""
        alerts: list[MicroRiskAlert] = []
        shadow = self._shadows.get(action.symbol)
        qty = action.payload.get("qty", shadow.qty if shadow else 0)
        reason = action.payload.get("reason", "FULL_EXIT")

        success = self._orders.send_emergency_order(
            symbol=action.symbol, side="SELL", qty=qty,
            order_type="MARKET", reason=reason,
        )

        if success:
            if shadow is not None:
                shadow.trailing_stop_active = False
                shadow.qty = 0
            alerts.append(MicroRiskAlert(
                code="FS102",
                message=f"Full exit: {action.symbol} reason={reason}",
                severity="CRITICAL",
            ))
        else:
            alerts.append(MicroRiskAlert(
                code="GR074",
                message=f"Emergency order failed: {action.symbol}",
                severity="CRITICAL",
            ))

        self._safety.notify(
            "FS102", f"Micro Risk triggered full exit: {action.symbol}",
        )

        return alerts

    def _freeze_position(self, action: MicroRiskAction) -> None:
        """포지션 동결 (§5.4)."""
        self._frozen_symbols.add(action.symbol)

    def _suspend_eteda(self, action: MicroRiskAction) -> list[MicroRiskAlert]:
        """ETEDA 정지 (§5.5)."""
        alerts: list[MicroRiskAlert] = []
        reason = action.payload.get("reason", "MICRO_RISK_SUSPEND")
        duration_ms = action.payload.get("duration_ms", 60000)

        self._eteda.suspend(
            reason=reason, source="MICRO_RISK_LOOP", duration_ms=duration_ms,
        )

        self._safety.notify(
            "FS103", f"ETEDA suspended: {reason}",
        )

        alerts.append(MicroRiskAlert(
            code="FS103",
            message=f"ETEDA suspended by Micro Risk: {reason}",
            severity="CRITICAL",
        ))

        return alerts

    def _execute_kill_switch(self, action: MicroRiskAction) -> list[MicroRiskAlert]:
        """킬 스위치 (§7.4)."""
        alerts: list[MicroRiskAlert] = []

        # 1. 전체 포지션 청산
        for symbol, shadow in self._shadows.items():
            if shadow.qty != 0:
                exit_action = MicroRiskAction(
                    action_type=ActionType.FULL_EXIT,
                    symbol=symbol,
                    payload={
                        "qty": shadow.qty,
                        "reason": action.payload.get("reason", "KILL_SWITCH"),
                    },
                )
                alerts.extend(self._execute_full_exit(exit_action))

        # 2. ETEDA 정지 (무기한)
        self._eteda.suspend(
            reason="KILL_SWITCH", source="MICRO_RISK_LOOP", duration_ms=None,
        )

        # 3. Safety 통보
        self._safety.notify(
            "FS104", f"LOCKDOWN triggered by Micro Risk: {action.payload.get('reason', 'KILL_SWITCH')}",
        )

        alerts.append(MicroRiskAlert(
            code="FS104",
            message="Kill switch activated",
            severity="CRITICAL",
        ))

        return alerts
