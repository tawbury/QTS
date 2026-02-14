"""StrategyMultiplexer scalp/swing split tests."""
from __future__ import annotations

import pytest

try:
    from src.strategy.multiplexer.strategy_multiplexer import StrategyMultiplexer, StrategyIntent
    from src.strategy.registry.strategy_registry import StrategyRegistry
    from src.strategy.arbitration.intent_arbitrator import IntentArbitrator
    from src.strategy.engines.scalp_engine import ScalpStrategyEngine
    from src.strategy.engines.swing_engine import SwingStrategyEngine
    from src.strategy.contracts import get_strategy_tag
    from src.strategy.interfaces.strategy import MarketContext, ExecutionContext, Intent
    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False

pytestmark = pytest.mark.skipif(
    not _HAS_DEPS,
    reason="Strategy dependencies not installed",
)


class TestGetStrategyTag:
    """get_strategy_tag utility tests."""

    def test_scalp_prefix(self):
        si = StrategyIntent("scalp_main", "scalp_golden_cross", Intent("A", "BUY", 1, ""))
        assert get_strategy_tag(si) == "scalp"

    def test_swing_prefix(self):
        si = StrategyIntent("swing_main", "swing_trend", Intent("A", "BUY", 1, ""))
        assert get_strategy_tag(si) == "swing"

    def test_unknown_defaults_scalp(self):
        si = StrategyIntent("other", "other_strategy", Intent("A", "BUY", 1, ""))
        assert get_strategy_tag(si) == "scalp"


class TestMultiplexerDualEngine:
    """Multiplexer Scalp+Swing 듀얼 엔진 테스트."""

    def _setup_dual_engine(self):
        registry = StrategyRegistry()
        scalp = ScalpStrategyEngine()
        swing = SwingStrategyEngine()
        registry.register(scalp)
        registry.register(swing)
        mux = StrategyMultiplexer(registry)
        return mux, scalp, swing

    def test_dual_engine_both_signals(self):
        """Scalp+Swing 둘 다 신호 생성."""
        mux, _, _ = self._setup_dual_engine()

        market = MarketContext(symbol="005930", price=70000.0)
        execution = ExecutionContext(position_qty=0, cash=10_000_000.0)

        results = mux.collect(snapshot=(market, execution))

        assert len(results) == 2
        tags = {get_strategy_tag(si) for si in results}
        assert tags == {"scalp", "swing"}

    def test_scalp_disabled_only_swing(self):
        """Scalp 비활성화 시 Swing만 실행."""
        mux, _, _ = self._setup_dual_engine()
        mux.set_engine_state(scalp_enabled=False, swing_enabled=True)

        market = MarketContext(symbol="005930", price=70000.0)
        execution = ExecutionContext(position_qty=0, cash=10_000_000.0)

        results = mux.collect(snapshot=(market, execution))

        assert len(results) == 1
        assert get_strategy_tag(results[0]) == "swing"

    def test_swing_disabled_only_scalp(self):
        """Swing 비활성화 시 Scalp만 실행."""
        mux, _, _ = self._setup_dual_engine()
        mux.set_engine_state(scalp_enabled=True, swing_enabled=False)

        market = MarketContext(symbol="005930", price=70000.0)
        execution = ExecutionContext(position_qty=0, cash=10_000_000.0)

        results = mux.collect(snapshot=(market, execution))

        assert len(results) == 1
        assert get_strategy_tag(results[0]) == "scalp"

    def test_both_disabled_no_signals(self):
        """둘 다 비활성화 시 신호 없음."""
        mux, _, _ = self._setup_dual_engine()
        mux.set_engine_state(scalp_enabled=False, swing_enabled=False)

        market = MarketContext(symbol="005930", price=70000.0)
        execution = ExecutionContext(position_qty=0, cash=10_000_000.0)

        results = mux.collect(snapshot=(market, execution))

        assert len(results) == 0

    def test_engine_failure_isolation(self):
        """한 엔진 예외 시 다른 엔진 계속 실행."""

        class FailingEngine:
            @property
            def strategy_id(self) -> str:
                return "failing_scalp"

            @property
            def name(self) -> str:
                return "scalp_failing"

            def is_enabled(self) -> bool:
                return True

            def generate_intents(self, snapshot):
                raise RuntimeError("Engine crashed")

        registry = StrategyRegistry()
        failing = FailingEngine()
        swing = SwingStrategyEngine()
        registry.register(failing)
        registry.register(swing)
        mux = StrategyMultiplexer(registry)

        market = MarketContext(symbol="005930", price=70000.0)
        execution = ExecutionContext(position_qty=0, cash=10_000_000.0)

        results = mux.collect(snapshot=(market, execution))

        assert len(results) == 1
        assert get_strategy_tag(results[0]) == "swing"

    def test_re_enable_after_disable(self):
        """비활성화 후 재활성화 시 정상 동작."""
        mux, _, _ = self._setup_dual_engine()

        mux.set_engine_state(scalp_enabled=False, swing_enabled=True)
        mux.set_engine_state(scalp_enabled=True, swing_enabled=True)

        market = MarketContext(symbol="005930", price=70000.0)
        execution = ExecutionContext(position_qty=0, cash=10_000_000.0)

        results = mux.collect(snapshot=(market, execution))

        assert len(results) == 2


class TestArbitrationDualEngine:
    """Arbitrator 중복 제거 테스트."""

    def test_same_symbol_side_dedup(self):
        """동일 symbol/side는 첫 번째만 유지."""
        arbitrator = IntentArbitrator()

        intents = [
            StrategyIntent("scalp_main", "scalp_golden_cross",
                           Intent("005930", "BUY", 1, "[scalp] gc_buy")),
            StrategyIntent("swing_main", "swing_trend",
                           Intent("005930", "BUY", 5, "[swing] trend_entry")),
        ]

        result = arbitrator.arbitrate(intents)

        assert len(result) == 1
        assert result[0].strategy_id == "scalp_main"

    def test_different_symbols_kept(self):
        """다른 종목은 모두 유지."""
        arbitrator = IntentArbitrator()

        intents = [
            StrategyIntent("scalp_main", "scalp_golden_cross",
                           Intent("005930", "BUY", 1, "")),
            StrategyIntent("swing_main", "swing_trend",
                           Intent("035720", "BUY", 5, "")),
        ]

        result = arbitrator.arbitrate(intents)

        assert len(result) == 2
