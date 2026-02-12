"""Micro Risk Loop 통합 테스트."""
from decimal import Decimal

import pytest

from src.micro_risk.contracts import (
    ActionType,
    MAEConfig,
    MarketData,
    MicroRiskConfig,
    PositionShadow,
    PriceFeed,
    StrategyType,
    TrailingStopConfig,
    VolatilityKillSwitchConfig,
)
from src.micro_risk.dispatcher import (
    NoopETEDAController,
    NoopOrderChannel,
    NoopSafetyNotifier,
)
from src.micro_risk.loop import MicroRiskLoop
from src.event.contracts import EventType, EventPriority, create_event
from src.safety.state import SafetyState


class TestFullCycleHappyPath:
    """정상 사이클: 포지션 추가 → 사이클 실행 → 액션 없음."""

    def test_no_action_cycle(self):
        loop = MicroRiskLoop()
        loop.start()
        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("75500"),
        )
        loop.add_position(shadow)
        alerts = loop.run_cycle(MarketData())
        assert len(alerts) == 0
        assert loop.cycle_count == 1


class TestTrailingStopFullCycle:
    """트레일링 스탑 활성화 → 조정 → 히트."""

    def test_activation_and_hit(self):
        loop = MicroRiskLoop()
        loop.start()

        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("76500"),
        )
        shadow.unrealized_pnl_pct = Decimal("0.02")
        shadow.highest_price_since_entry = Decimal("76500")
        loop.add_position(shadow)

        # 1. 활성화 사이클
        alerts = loop.run_cycle(MarketData())
        assert shadow.trailing_stop_active is True
        assert shadow.trailing_stop_price > 0

        # 2. 가격 하락 → 스탑 히트
        shadow.current_price = Decimal("74000")
        alerts = loop.run_cycle(MarketData())
        has_exit = any(a.code == "FS102" for a in alerts)
        assert has_exit
        assert shadow.qty == 0


class TestMAEFullCycle:
    """MAE 초과 시 전량 청산."""

    def test_mae_triggers_exit(self):
        config = MicroRiskConfig(
            mae=MAEConfig(position_mae_threshold_pct=Decimal("0.02")),
        )
        loop = MicroRiskLoop(config=config)
        loop.start()

        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("73400"),
        )
        shadow.mae_pct = Decimal("-0.025")
        loop.add_position(shadow)

        alerts = loop.run_cycle(MarketData())
        assert any(a.code == "FS102" for a in alerts)
        assert shadow.qty == 0


class TestVolatilityKillSwitch:
    """변동성 킬스위치 발동 시 전체 청산."""

    def test_kill_switch(self):
        order_channel = NoopOrderChannel()
        eteda = NoopETEDAController()
        safety = NoopSafetyNotifier()

        loop = MicroRiskLoop(
            order_channel=order_channel,
            eteda_controller=eteda,
            safety_notifier=safety,
        )
        loop.start()

        loop.add_position(PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("75000"),
        ))
        loop.add_position(PositionShadow(
            symbol="000660", qty=50,
            avg_price=Decimal("120000"), current_price=Decimal("120000"),
        ))

        md = MarketData(vix=Decimal("45"))
        alerts = loop.run_cycle(md)

        # 전량 청산 확인
        assert len(order_channel.orders) >= 2
        assert eteda.is_suspended()
        assert any(c == "FS104" for c, _ in safety.notifications)


class TestETEDAIndependence:
    """ETEDA 정지 중에도 Micro Loop 동작."""

    def test_loop_works_with_suspended_eteda(self):
        eteda = NoopETEDAController()
        eteda._suspended = True  # ETEDA 정지 상태

        loop = MicroRiskLoop(eteda_controller=eteda)
        loop.start()

        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("73400"),
        )
        shadow.mae_pct = Decimal("-0.025")
        loop.add_position(shadow)

        alerts = loop.run_cycle(MarketData())
        # ETEDA 정지 중이어도 Micro Loop는 독립 실행
        assert any(a.code == "FS102" for a in alerts)


class TestTimeInTradeIntegration:
    """보유 시간 초과 통합 테스트."""

    def test_timeout_exit(self):
        from datetime import timedelta
        config = MicroRiskConfig()
        loop = MicroRiskLoop(config=config)
        loop.start()

        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("75000"),
        )
        # entry_time을 과거로 설정 (run_cycle이 time_in_trade_sec 재계산)
        shadow.entry_time = shadow.entry_time - timedelta(seconds=3700)
        loop.add_position(shadow)

        alerts = loop.run_cycle(MarketData())
        assert any(a.code == "FS102" for a in alerts)


class TestSafetyIntegration:
    """Safety Layer 연계."""

    def test_safety_notification(self):
        safety = NoopSafetyNotifier()
        loop = MicroRiskLoop(safety_notifier=safety)
        loop.start()

        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("73400"),
        )
        shadow.mae_pct = Decimal("-0.025")
        loop.add_position(shadow)

        loop.run_cycle(MarketData())
        assert len(safety.notifications) > 0
        codes = [c for c, _ in safety.notifications]
        assert "FS102" in codes


class TestEventSystemIntegration:
    """Event 시스템 통합."""

    def test_emergency_stop_is_p0(self):
        event = create_event(EventType.EMERGENCY_STOP, source="micro_risk")
        assert event.priority == EventPriority.P0_CRITICAL

    def test_vix_update_is_p1(self):
        event = create_event(EventType.VIX_UPDATE, source="market_data")
        assert event.priority == EventPriority.P1_HIGH


class TestSafetyStateCompatibility:
    """Safety State 호환성."""

    def test_lockdown_state(self):
        assert SafetyState.LOCKDOWN.value == "LOCKDOWN"
        assert SafetyState.NORMAL.value == "NORMAL"


class TestPositionManagement:
    """포지션 관리."""

    def test_add_remove_position(self):
        loop = MicroRiskLoop()
        loop.add_position(PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("75000"),
        ))
        assert loop.shadow_manager.count() == 1

        loop.remove_position("005930")
        assert loop.shadow_manager.count() == 0

    def test_position_summary(self):
        loop = MicroRiskLoop()
        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("76000"),
        )
        shadow.unrealized_pnl_pct = Decimal("0.0133")
        loop.add_position(shadow)

        summary = loop.get_position_summary()
        assert "005930" in summary
        assert summary["005930"]["qty"] == 100

    def test_skip_zero_qty(self):
        loop = MicroRiskLoop()
        loop.start()
        shadow = PositionShadow(
            symbol="005930", qty=0,
            avg_price=Decimal("75000"), current_price=Decimal("75000"),
        )
        shadow.mae_pct = Decimal("-0.03")
        loop.add_position(shadow)

        alerts = loop.run_cycle(MarketData())
        assert len(alerts) == 0  # qty=0 → skip


class TestPriceInjection:
    """가격 주입 테스트."""

    def test_inject_price(self):
        loop = MicroRiskLoop()
        shadow = PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("75000"),
        )
        loop.add_position(shadow)

        feed = PriceFeed(
            symbol="005930",
            price=Decimal("76000"),
            bid=Decimal("75900"), ask=Decimal("76100"),
        )
        loop.inject_price("005930", feed)
        assert shadow.current_price == Decimal("76000")


class TestConsecutiveErrors:
    """연속 에러 시 ETEDA 정지."""

    def test_consecutive_errors_stop_loop(self):
        eteda = NoopETEDAController()
        config = MicroRiskConfig(max_consecutive_errors=2)
        loop = MicroRiskLoop(config=config, eteda_controller=eteda)
        loop.start()

        # 에러 유발을 위해 evaluator를 monkey-patch
        def raise_error(shadow, md):
            raise RuntimeError("test error")

        loop.evaluator.evaluate = raise_error  # type: ignore[assignment]
        loop.add_position(PositionShadow(
            symbol="005930", qty=100,
            avg_price=Decimal("75000"), current_price=Decimal("75000"),
        ))

        # 1차 에러
        alerts1 = loop.run_cycle(MarketData())
        assert any(a.code == "FS100" for a in alerts1)
        assert loop.is_running  # 아직 실행 중

        # 2차 에러 → ETEDA 정지 + 루프 중단
        alerts2 = loop.run_cycle(MarketData())
        assert any(a.code == "FS103" for a in alerts2)
        assert not loop.is_running
        assert eteda.is_suspended()
