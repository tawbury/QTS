"""Micro Risk Loop 런타임 통합 테스트.

런타임 브릿지 어댑터, 비동기 러너, ETEDA 연동을 검증한다.
근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §4.1~§4.4
"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from src.micro_risk.bridges import (
    BrokerEmergencyChannel,
    ETEDALoopController,
    SafetyLayerNotifier,
)
from src.micro_risk.async_runner import MicroRiskLoopRunner
from src.micro_risk.contracts import (
    ActionType,
    MarketData,
    MicroRiskConfig,
    PositionShadow,
)
from src.micro_risk.loop import MicroRiskLoop


# --- Bridge Tests ---


class TestETEDALoopController:
    """ETEDALoopController 브릿지 테스트."""

    def test_initial_state(self):
        ctrl = ETEDALoopController()
        assert not ctrl.is_suspended()
        assert not ctrl.should_stop()

    def test_suspend_sets_flags(self):
        ctrl = ETEDALoopController()
        result = ctrl.suspend(reason="test", source="MICRO_RISK_LOOP")
        assert result is True
        assert ctrl.is_suspended()
        assert ctrl.should_stop()
        assert ctrl.suspend_reason == "test"

    def test_resume_clears_flags(self):
        ctrl = ETEDALoopController()
        ctrl.suspend(reason="test", source="MICRO_RISK_LOOP")
        ctrl.resume()
        assert not ctrl.is_suspended()
        assert not ctrl.should_stop()


class TestBrokerEmergencyChannel:
    """BrokerEmergencyChannel 브릿지 테스트."""

    def test_send_accepted(self):
        broker = MagicMock()
        resp = MagicMock()
        resp.accepted = True
        broker.submit_intent.return_value = resp

        channel = BrokerEmergencyChannel(broker)
        result = channel.send_emergency_order(
            symbol="005930", side="SELL", qty=100,
            order_type="MARKET", reason="TRAILING_STOP_HIT",
        )
        assert result is True
        broker.submit_intent.assert_called_once()

    def test_send_rejected(self):
        broker = MagicMock()
        resp = MagicMock()
        resp.accepted = False
        resp.message = "rejected"
        broker.submit_intent.return_value = resp

        channel = BrokerEmergencyChannel(broker)
        result = channel.send_emergency_order(
            symbol="005930", side="SELL", qty=100,
            order_type="MARKET", reason="MAE_EXCEEDED",
        )
        assert result is False

    def test_send_exception(self):
        broker = MagicMock()
        broker.submit_intent.side_effect = Exception("network error")

        channel = BrokerEmergencyChannel(broker)
        result = channel.send_emergency_order(
            symbol="005930", side="SELL", qty=100,
            order_type="MARKET", reason="KILL_SWITCH",
        )
        assert result is False


class TestSafetyLayerNotifier:
    """SafetyLayerNotifier 브릿지 테스트."""

    def test_notify_with_safety_layer(self):
        safety = MagicMock()
        notifier = SafetyLayerNotifier(safety)
        notifier.notify("FS102", "test alert")
        safety.record_fail_safe.assert_called_once_with("FS102", "test alert", "MicroRisk")

    def test_notify_without_safety_layer(self):
        notifier = SafetyLayerNotifier(None)
        notifier.notify("FS102", "test alert")  # 에러 없이 통과

    def test_notify_safety_exception(self):
        safety = MagicMock()
        safety.record_fail_safe.side_effect = Exception("fail")
        notifier = SafetyLayerNotifier(safety)
        notifier.notify("FS102", "test alert")  # 에러 로깅만, 예외 전파 없음


# --- Async Runner Tests ---


class TestMicroRiskLoopRunner:
    """MicroRiskLoopRunner 비동기 러너 테스트."""

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """러너 시작/정지."""
        loop = MicroRiskLoop()
        runner = MicroRiskLoopRunner(loop, interval_ms=50)

        task = runner.start_background()
        await asyncio.sleep(0.2)

        assert runner.is_running
        assert loop.cycle_count > 0

        runner.stop()
        await asyncio.sleep(0.1)
        assert not runner.is_running

    @pytest.mark.asyncio
    async def test_runner_with_positions(self):
        """포지션 모니터링 중 러너 동작."""
        ctrl = ETEDALoopController()
        loop = MicroRiskLoop(eteda_controller=ctrl)

        shadow = PositionShadow(
            symbol="005930",
            qty=100,
            avg_price=75000,
            current_price=75000,
        )
        loop.add_position(shadow)

        runner = MicroRiskLoopRunner(loop, interval_ms=50)
        task = runner.start_background()
        await asyncio.sleep(0.2)

        assert loop.cycle_count > 0
        runner.stop()
        await asyncio.sleep(0.1)


# --- ETEDA Integration Tests ---


class TestETEDAMicroRiskIntegration:
    """ETEDA ↔ Micro Risk Loop 통합 테스트."""

    def test_micro_risk_suspends_eteda(self):
        """Micro Risk Loop Kill Switch → ETEDA 정지 (§4.4)."""
        ctrl = ETEDALoopController()
        loop = MicroRiskLoop(eteda_controller=ctrl)

        shadow = PositionShadow(
            symbol="005930",
            qty=100,
            avg_price=75000,
            current_price=75000,
        )
        loop.add_position(shadow)

        # Kill Switch 조건: VIX >= 40
        market = MarketData(vix=45.0, realized_volatility=0.10)
        alerts = loop.run_cycle(market_data=market)

        # ETEDA 정지 확인
        assert ctrl.is_suspended()
        assert any(a.code == "FS104" for a in alerts)

    def test_micro_risk_independent_when_eteda_paused(self):
        """ETEDA 정지 중에도 Micro Risk Loop 동작 (§4.1)."""
        ctrl = ETEDALoopController()
        loop = MicroRiskLoop(eteda_controller=ctrl)

        shadow = PositionShadow(
            symbol="005930",
            qty=100,
            avg_price=75000,
            current_price=74000,
            mae_pct=-0.03,
        )
        loop.add_position(shadow)

        # ETEDA 이미 정지 상태
        ctrl.suspend(reason="manual", source="test")

        # Micro Risk Loop는 여전히 MAE 규칙 평가 가능
        alerts = loop.run_cycle()

        # MAE 초과 → FULL_EXIT
        assert any(a.code == "FS102" for a in alerts)

    def test_position_sync_from_eteda(self):
        """ETEDA Act 결과 → Micro Risk Loop 동기화 (§6.2)."""
        loop = MicroRiskLoop()

        # 초기 포지션 추가
        shadow = PositionShadow(
            symbol="005930",
            qty=100,
            avg_price=75000,
            current_price=75000,
        )
        loop.add_position(shadow)

        # ETEDA에서 체결 후 동기화
        loop.sync_from_main({
            "005930": {
                "qty": 150,
                "avg_price": 75500,
                "current_price": 76000,
                "unrealized_pnl": 75000,
                "unrealized_pnl_pct": 0.0066,
            }
        })

        updated = loop.shadow_manager.get("005930")
        assert updated.qty == 150
        assert updated.avg_price == 75500
        assert updated.current_price == 76000
