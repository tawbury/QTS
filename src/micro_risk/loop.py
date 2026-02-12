"""Micro Risk Loop Controller.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §4.2
- ETEDA와 독립적으로 실행
- 동기식 run_cycle()로 테스트 가능
- 사이클: sync → evaluate → dispatch → sleep
"""
from __future__ import annotations

from typing import Any, Optional

from src.micro_risk.contracts import (
    ActionType,
    MarketData,
    MicroRiskAction,
    MicroRiskAlert,
    MicroRiskConfig,
    PositionShadow,
)
from src.micro_risk.dispatcher import (
    ActionDispatcher,
    EmergencyOrderChannel,
    ETEDAController,
    SafetyNotifier,
)
from src.micro_risk.evaluator import RiskRuleEvaluator
from src.micro_risk.guardrails import check_loop_error
from src.micro_risk.price_handler import PriceFeedHandler
from src.micro_risk.shadow_manager import PositionShadowManager


class MicroRiskLoop:
    """Micro Risk Loop 컨트롤러 (§4.2).

    동기식 run_cycle()로 테스트 가능한 설계.
    실제 비동기 루프 실행은 외부에서 담당.
    """

    def __init__(
        self,
        config: Optional[MicroRiskConfig] = None,
        order_channel: Optional[EmergencyOrderChannel] = None,
        eteda_controller: Optional[ETEDAController] = None,
        safety_notifier: Optional[SafetyNotifier] = None,
    ) -> None:
        self.config = config or MicroRiskConfig()
        self.shadow_manager = PositionShadowManager()
        self.price_handler = PriceFeedHandler()
        self.evaluator = RiskRuleEvaluator(self.config)
        self.dispatcher = ActionDispatcher(
            shadow_manager=self.shadow_manager,
            order_channel=order_channel,
            eteda_controller=eteda_controller,
            safety_notifier=safety_notifier,
        )
        self._running = False
        self._consecutive_errors = 0
        self._cycle_count = 0
        self._alerts_log: list[MicroRiskAlert] = []

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def alerts_log(self) -> list[MicroRiskAlert]:
        return list(self._alerts_log)

    def start(self) -> None:
        """루프 시작."""
        self._running = True
        self._consecutive_errors = 0

    def stop(self) -> None:
        """루프 정지."""
        self._running = False

    def add_position(self, shadow: PositionShadow) -> None:
        """모니터링 포지션 추가."""
        self.shadow_manager.add_position(shadow)

    def remove_position(self, symbol: str) -> None:
        """모니터링 포지션 제거."""
        self.shadow_manager.remove_position(symbol)

    def inject_price(self, symbol: str, price_feed: Any) -> list[MicroRiskAlert]:
        """가격 틱 주입 (테스트용)."""
        shadow = self.shadow_manager.get(symbol)
        return self.price_handler.on_price_tick(price_feed, shadow)

    def sync_from_main(self, main_positions: dict[str, dict[str, Any]]) -> list[MicroRiskAlert]:
        """메인 포지션 동기화."""
        return self.shadow_manager.sync_from_main(main_positions)

    def run_cycle(self, market_data: Optional[MarketData] = None) -> list[MicroRiskAlert]:
        """단일 사이클 실행 (테스트 가능한 동기식).

        Returns:
            사이클 중 발생한 알림 목록
        """
        alerts: list[MicroRiskAlert] = []

        try:
            # 1. 보유 시간 업데이트
            self.shadow_manager.update_time_in_trade()

            # 2. 시장 데이터
            if market_data is None:
                market_data = MarketData()

            # 3. 각 포지션에 대해 규칙 평가
            for symbol, shadow in self.shadow_manager.items():
                if shadow.qty == 0:
                    continue

                # 규칙 평가
                actions = self.evaluator.evaluate(shadow, market_data)

                # 액션 실행
                for action in actions:
                    dispatch_alerts = self.dispatcher.dispatch(action)
                    alerts.extend(dispatch_alerts)

            self._consecutive_errors = 0
            self._cycle_count += 1

        except Exception as e:
            self._consecutive_errors += 1
            error_alerts = check_loop_error(e)
            alerts.extend(error_alerts)

            # 연속 에러 시 ETEDA 정지
            if self._consecutive_errors >= self.config.max_consecutive_errors:
                suspend_action = MicroRiskAction(
                    action_type=ActionType.ETEDA_SUSPEND,
                    symbol="ALL",
                    payload={
                        "reason": f"Micro loop consecutive errors: {self._consecutive_errors}",
                        "duration_ms": 60000,
                    },
                )
                alerts.extend(self.dispatcher.dispatch(suspend_action))
                self.stop()

        self._alerts_log.extend(alerts)
        return alerts

    def get_position_summary(self) -> dict[str, dict]:
        """모니터링 중인 포지션 요약."""
        summary = {}
        for symbol, shadow in self.shadow_manager.items():
            summary[symbol] = {
                "qty": shadow.qty,
                "pnl_pct": float(shadow.unrealized_pnl_pct),
                "mae_pct": float(shadow.mae_pct),
                "time_sec": shadow.time_in_trade_sec,
                "trailing_active": shadow.trailing_stop_active,
                "trailing_stop": float(shadow.trailing_stop_price),
            }
        return summary
