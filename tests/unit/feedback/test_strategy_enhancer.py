"""feedback/strategy_enhancer.py 단위 테스트."""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence

import pytest

from src.feedback.contracts import (
    DEFAULT_FEEDBACK_SUMMARY,
    FeedbackSummary,
    TickRecord,
)
from src.feedback.strategy_enhancer import (
    EnhancedIntent,
    FeedbackAwareStrategyEngine,
    StrategyInputEnhanced,
    adjust_confidence,
    adjust_qty_for_market_impact,
    calculate_adjusted_entry_price,
)


class TestCalculateAdjustedEntryPrice:
    def test_buy_positive_slippage(self):
        """매수: 슬리피지만큼 높은 가격."""
        result = calculate_adjusted_entry_price(
            signal_price=Decimal("75000"),
            historical_slippage_bps=10.0,
            side="BUY",
        )
        # 75000 * (1 + 10/10000) = 75000 * 1.001 = 75075
        assert result == Decimal("75000") * Decimal("1.001")

    def test_sell_positive_slippage(self):
        """매도: 슬리피지만큼 낮은 가격."""
        result = calculate_adjusted_entry_price(
            signal_price=Decimal("75000"),
            historical_slippage_bps=10.0,
            side="SELL",
        )
        assert result == Decimal("75000") * Decimal("0.999")

    def test_zero_slippage(self):
        """0 슬리피지면 원래 가격."""
        result = calculate_adjusted_entry_price(
            signal_price=Decimal("75000"),
            historical_slippage_bps=0.0,
            side="BUY",
        )
        assert result == Decimal("75000")

    def test_zero_signal_price(self):
        """시그널 가격 0이면 그대로 반환."""
        result = calculate_adjusted_entry_price(
            signal_price=Decimal("0"),
            historical_slippage_bps=10.0,
            side="BUY",
        )
        assert result == Decimal("0")

    def test_negative_signal_price(self):
        result = calculate_adjusted_entry_price(
            signal_price=Decimal("-100"),
            historical_slippage_bps=10.0,
            side="BUY",
        )
        assert result == Decimal("-100")

    def test_case_insensitive_side(self):
        buy = calculate_adjusted_entry_price(
            signal_price=Decimal("100"),
            historical_slippage_bps=100.0,
            side="buy",
        )
        sell = calculate_adjusted_entry_price(
            signal_price=Decimal("100"),
            historical_slippage_bps=100.0,
            side="sell",
        )
        assert buy > Decimal("100")
        assert sell < Decimal("100")

    def test_large_slippage(self):
        """100bps = 1%."""
        result = calculate_adjusted_entry_price(
            signal_price=Decimal("10000"),
            historical_slippage_bps=100.0,
            side="BUY",
        )
        assert result == Decimal("10000") * Decimal("1.01")


class TestAdjustQtyForMarketImpact:
    def test_under_threshold(self):
        """충격이 허용 이하면 원래 수량."""
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("1000"),
            estimated_impact_bps=10.0,
            max_acceptable_impact_bps=20.0,
        )
        assert result == Decimal("1000")

    def test_at_threshold(self):
        """정확히 허용치면 원래 수량."""
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("1000"),
            estimated_impact_bps=20.0,
            max_acceptable_impact_bps=20.0,
        )
        assert result == Decimal("1000")

    def test_over_threshold(self):
        """초과 시 비례 축소."""
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("1000"),
            estimated_impact_bps=50.0,
            max_acceptable_impact_bps=20.0,
        )
        # reduction_ratio = 20/50 = 0.4
        assert result == Decimal("1000") * Decimal("0.4")

    def test_zero_qty(self):
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("0"),
            estimated_impact_bps=50.0,
        )
        assert result == Decimal("0")

    def test_negative_qty(self):
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("-100"),
            estimated_impact_bps=50.0,
        )
        assert result == Decimal("-100")

    def test_double_threshold(self):
        """충격이 2배면 수량 50%."""
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("1000"),
            estimated_impact_bps=40.0,
            max_acceptable_impact_bps=20.0,
        )
        assert result == Decimal("1000") * Decimal("0.5")

    def test_example_from_spec(self):
        """아키텍처 문서 예제: 50bps, max 20bps → 40%."""
        result = adjust_qty_for_market_impact(
            target_qty=Decimal("1000"),
            estimated_impact_bps=50.0,
            max_acceptable_impact_bps=20.0,
        )
        assert result == Decimal("1000") * Decimal("0.4")


class TestAdjustConfidence:
    def test_full_quality(self):
        assert adjust_confidence(0.8, 1.0) == 0.8

    def test_half_quality(self):
        assert adjust_confidence(0.8, 0.5) == pytest.approx(0.4)

    def test_zero_quality(self):
        assert adjust_confidence(0.8, 0.0) == 0.0

    def test_clamped_max(self):
        assert adjust_confidence(1.0, 1.5) == 1.0

    def test_clamped_min(self):
        assert adjust_confidence(-0.5, 1.0) == 0.0

    def test_typical(self):
        """일반적인 케이스: 0.85 * 0.92 = 0.782."""
        result = adjust_confidence(0.85, 0.92)
        assert pytest.approx(result, abs=0.01) == 0.782


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _MarketCtx:
    """테스트용 Strategy MarketContext."""
    symbol: str
    price: float


@dataclass(frozen=True)
class _ExecCtx:
    """테스트용 Strategy ExecutionContext."""
    position_qty: int
    cash: float


@dataclass(frozen=True)
class _Intent:
    """테스트용 Intent."""
    symbol: str
    side: str
    qty: int
    reason: str


class _DummyStrategy:
    """테스트용 Strategy 구현체."""

    def __init__(self, intents: list[_Intent] | None = None):
        self._intents = intents or []

    def generate_intents(
        self, market: _MarketCtx, execution: _ExecCtx,
    ) -> Sequence[_Intent]:
        return self._intents


class _DummySummaryProvider:
    """테스트용 FeedbackSummaryProvider."""

    def __init__(self, summary: FeedbackSummary | None = None):
        self._summary = summary or DEFAULT_FEEDBACK_SUMMARY
        self.calls: list[tuple[str, int]] = []

    def get_summary(self, symbol: str, lookback_days: int = 30) -> FeedbackSummary:
        self.calls.append((symbol, lookback_days))
        return self._summary


def _make_ticks(
    n: int = 5,
    base_price: float = 75000.0,
    spread: float = 50.0,
) -> list[TickRecord]:
    """테스트용 틱 데이터 생성."""
    ts = datetime(2025, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
    ticks = []
    for i in range(n):
        side = "BID" if i % 2 == 0 else "ASK"
        price = base_price if side == "BID" else base_price + spread
        ticks.append(TickRecord(
            timestamp=ts,
            symbol="005930",
            price=Decimal(str(price)),
            volume=100 + i * 10,
            side=side,
        ))
    return ticks


# ---------------------------------------------------------------------------
# StrategyInputEnhanced 테스트
# ---------------------------------------------------------------------------


class TestStrategyInputEnhanced:
    """StrategyInputEnhanced 데이터 클래스 테스트."""

    def test_defaults(self):
        """기본값 생성."""
        inp = StrategyInputEnhanced(symbol="005930", price=75000.0)
        assert inp.symbol == "005930"
        assert inp.price == 75000.0
        assert inp.position_qty == 0
        assert inp.cash == 0.0
        assert inp.volatility == 0.0
        assert inp.spread_bps == 0.0
        assert inp.depth == 0
        assert inp.avg_slippage_bps == 10.0
        assert inp.avg_quality_score == 0.75
        assert inp.sample_count == 0

    def test_from_feedback_summary_no_ticks(self):
        """틱 없이 FeedbackSummary로부터 생성."""
        summary = FeedbackSummary(
            avg_slippage_bps=5.0,
            avg_market_impact_bps=8.0,
            avg_quality_score=0.9,
            avg_fill_latency_ms=30.0,
            avg_fill_ratio=0.98,
            sample_count=50,
        )
        inp = StrategyInputEnhanced.from_feedback_summary(
            symbol="005930",
            price=75000.0,
            position_qty=10,
            cash=1000000.0,
            summary=summary,
        )
        assert inp.symbol == "005930"
        assert inp.price == 75000.0
        assert inp.position_qty == 10
        assert inp.cash == 1000000.0
        assert inp.avg_slippage_bps == 5.0
        assert inp.avg_quality_score == 0.9
        assert inp.sample_count == 50
        # 틱 없으면 실시간 메트릭 0
        assert inp.volatility == 0.0
        assert inp.spread_bps == 0.0
        assert inp.depth == 0

    def test_from_feedback_summary_with_ticks(self):
        """틱 데이터가 있으면 volatility/spread/depth 계산."""
        ticks = _make_ticks(n=6, base_price=75000.0, spread=50.0)
        inp = StrategyInputEnhanced.from_feedback_summary(
            symbol="005930",
            price=75000.0,
            ticks=ticks,
        )
        # 틱 있으면 실시간 메트릭 > 0
        assert inp.volatility > 0.0
        assert inp.spread_bps > 0.0
        assert inp.depth > 0

    def test_from_feedback_summary_defaults(self):
        """summary 없으면 DEFAULT_FEEDBACK_SUMMARY 사용."""
        inp = StrategyInputEnhanced.from_feedback_summary(
            symbol="005930",
            price=75000.0,
        )
        assert inp.avg_slippage_bps == DEFAULT_FEEDBACK_SUMMARY.avg_slippage_bps
        assert inp.avg_quality_score == DEFAULT_FEEDBACK_SUMMARY.avg_quality_score

    def test_frozen(self):
        """frozen=True 확인."""
        inp = StrategyInputEnhanced(symbol="005930", price=75000.0)
        with pytest.raises(AttributeError):
            inp.price = 80000.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# FeedbackAwareStrategyEngine 테스트
# ---------------------------------------------------------------------------


class TestFeedbackAwareStrategyEngine:
    """FeedbackAwareStrategyEngine 래퍼 테스트."""

    def test_init_requires_generate_intents(self):
        """strategy에 generate_intents가 없으면 TypeError."""
        with pytest.raises(TypeError, match="generate_intents"):
            FeedbackAwareStrategyEngine(strategy=object())

    def test_init_valid_strategy(self):
        """유효한 strategy로 초기화."""
        engine = FeedbackAwareStrategyEngine(strategy=_DummyStrategy())
        assert engine is not None

    def test_generate_intents_empty(self):
        """전략이 빈 intent 반환 시 빈 리스트."""
        engine = FeedbackAwareStrategyEngine(strategy=_DummyStrategy([]))
        result = engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(0, 1000000.0),
        )
        assert result == []

    def test_generate_intents_basic(self):
        """기본 Intent에 피드백 보정 적용."""
        intents = [_Intent("005930", "BUY", 100, "test_buy")]
        engine = FeedbackAwareStrategyEngine(strategy=_DummyStrategy(intents))

        result = engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(0, 1000000.0),
        )

        assert len(result) == 1
        ei = result[0]
        assert isinstance(ei, EnhancedIntent)
        assert ei.symbol == "005930"
        assert ei.side == "BUY"
        assert ei.original_qty == 100
        # 기본 FeedbackSummary의 impact=15bps < max 20bps이므로 수량 유지
        assert ei.qty == 100

    def test_generate_intents_qty_reduced_by_impact(self):
        """시장 충격이 높으면 수량 축소."""
        intents = [_Intent("005930", "BUY", 100, "test_buy")]
        high_impact_summary = FeedbackSummary(
            avg_slippage_bps=10.0,
            avg_market_impact_bps=50.0,  # 50bps > max 20bps
            avg_quality_score=0.8,
            sample_count=10,
        )
        provider = _DummySummaryProvider(high_impact_summary)
        engine = FeedbackAwareStrategyEngine(
            strategy=_DummyStrategy(intents),
            summary_provider=provider,
            max_acceptable_impact_bps=20.0,
        )

        result = engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(0, 1000000.0),
        )

        assert len(result) == 1
        ei = result[0]
        # 20/50 = 0.4 → 100 * 0.4 = 40
        assert ei.qty == 40
        assert ei.original_qty == 100

    def test_generate_intents_entry_price_adjusted(self):
        """BUY 시 슬리피지만큼 진입가가 올라감."""
        intents = [_Intent("005930", "BUY", 100, "test_buy")]
        summary = FeedbackSummary(
            avg_slippage_bps=10.0,
            avg_market_impact_bps=5.0,
            avg_quality_score=1.0,
            sample_count=10,
        )
        provider = _DummySummaryProvider(summary)
        engine = FeedbackAwareStrategyEngine(
            strategy=_DummyStrategy(intents),
            summary_provider=provider,
        )

        result = engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(0, 1000000.0),
        )

        ei = result[0]
        expected = Decimal("75000") * Decimal("1.001")  # 10bps up
        assert ei.adjusted_entry_price == expected

    def test_generate_intents_sell_price_adjusted(self):
        """SELL 시 슬리피지만큼 진입가가 내려감."""
        intents = [_Intent("005930", "SELL", 50, "test_sell")]
        summary = FeedbackSummary(
            avg_slippage_bps=10.0,
            avg_market_impact_bps=5.0,
            avg_quality_score=1.0,
            sample_count=10,
        )
        provider = _DummySummaryProvider(summary)
        engine = FeedbackAwareStrategyEngine(
            strategy=_DummyStrategy(intents),
            summary_provider=provider,
        )

        result = engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(50, 1000000.0),
        )

        ei = result[0]
        expected = Decimal("75000") * Decimal("0.999")  # 10bps down
        assert ei.adjusted_entry_price == expected

    def test_generate_intents_confidence_adjusted(self):
        """실행 품질이 낮으면 신뢰도 감소."""
        intents = [_Intent("005930", "BUY", 100, "test_buy")]
        low_quality = FeedbackSummary(
            avg_slippage_bps=5.0,
            avg_market_impact_bps=5.0,
            avg_quality_score=0.5,  # 낮은 품질
            sample_count=10,
        )
        provider = _DummySummaryProvider(low_quality)
        engine = FeedbackAwareStrategyEngine(
            strategy=_DummyStrategy(intents),
            summary_provider=provider,
            confidence=0.8,
        )

        result = engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(0, 1000000.0),
        )

        ei = result[0]
        # confidence = 0.8 * 0.5 = 0.4
        assert pytest.approx(ei.confidence, abs=0.01) == 0.4

    def test_generate_intents_high_volatility_reduces_confidence(self):
        """변동성 2% 초과 시 추가 신뢰도 감소."""
        intents = [_Intent("005930", "BUY", 100, "test_buy")]
        summary = FeedbackSummary(
            avg_slippage_bps=5.0,
            avg_market_impact_bps=5.0,
            avg_quality_score=1.0,
            sample_count=10,
        )
        provider = _DummySummaryProvider(summary)
        engine = FeedbackAwareStrategyEngine(
            strategy=_DummyStrategy(intents),
            summary_provider=provider,
            confidence=1.0,
        )

        # 높은 변동성을 만드는 틱 (가격 차이가 큰 틱)
        ts = datetime(2025, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        volatile_ticks = [
            TickRecord(ts, "005930", Decimal("73000"), 100, "TRADE"),
            TickRecord(ts, "005930", Decimal("77000"), 100, "TRADE"),
        ]
        # volatility = (77000-73000)/75000 = 4000/75000 ≈ 0.053 > 0.02

        result = engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(0, 1000000.0),
            ticks=volatile_ticks,
        )

        ei = result[0]
        # confidence = 1.0 * 1.0 * 0.9 = 0.9 (변동성 감쇄)
        assert pytest.approx(ei.confidence, abs=0.01) == 0.9

    def test_generate_intents_no_volatility_penalty(self):
        """변동성 2% 이하면 추가 감쇄 없음."""
        intents = [_Intent("005930", "BUY", 100, "test_buy")]
        summary = FeedbackSummary(
            avg_slippage_bps=5.0,
            avg_market_impact_bps=5.0,
            avg_quality_score=1.0,
            sample_count=10,
        )
        provider = _DummySummaryProvider(summary)
        engine = FeedbackAwareStrategyEngine(
            strategy=_DummyStrategy(intents),
            summary_provider=provider,
            confidence=1.0,
        )

        # 변동성이 낮은 틱 (모두 같은 가격)
        ts = datetime(2025, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
        stable_ticks = [
            TickRecord(ts, "005930", Decimal("75000"), 100, "TRADE"),
            TickRecord(ts, "005930", Decimal("75010"), 100, "TRADE"),
        ]
        # volatility ≈ 10/75005 ≈ 0.00013 < 0.02

        result = engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(0, 1000000.0),
            ticks=stable_ticks,
        )

        ei = result[0]
        # confidence = 1.0 * 1.0 = 1.0 (변동성 감쇄 없음)
        assert pytest.approx(ei.confidence, abs=0.01) == 1.0

    def test_generate_intents_reason_enriched_with_feedback(self):
        """sample_count > 0이면 reason에 피드백 정보 추가."""
        intents = [_Intent("005930", "BUY", 100, "signal_buy")]
        summary = FeedbackSummary(
            avg_slippage_bps=5.0,
            avg_market_impact_bps=8.0,
            avg_quality_score=0.9,
            sample_count=20,
        )
        provider = _DummySummaryProvider(summary)
        engine = FeedbackAwareStrategyEngine(
            strategy=_DummyStrategy(intents),
            summary_provider=provider,
        )

        result = engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(0, 1000000.0),
        )

        ei = result[0]
        assert "signal_buy" in ei.reason
        assert "fb:" in ei.reason
        assert "slip=5.0bps" in ei.reason
        assert "impact=8.0bps" in ei.reason
        assert "qual=0.90" in ei.reason

    def test_generate_intents_reason_plain_without_samples(self):
        """sample_count == 0이면 reason에 피드백 정보 없음."""
        intents = [_Intent("005930", "BUY", 100, "signal_buy")]
        # DEFAULT_FEEDBACK_SUMMARY sample_count=0
        engine = FeedbackAwareStrategyEngine(strategy=_DummyStrategy(intents))

        result = engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(0, 1000000.0),
        )

        ei = result[0]
        assert ei.reason == "signal_buy"
        assert "fb:" not in ei.reason

    def test_generate_intents_multiple_intents(self):
        """여러 Intent가 있으면 각각 보정."""
        intents = [
            _Intent("005930", "BUY", 100, "buy_signal"),
            _Intent("035720", "SELL", 50, "sell_signal"),
        ]
        engine = FeedbackAwareStrategyEngine(strategy=_DummyStrategy(intents))

        result = engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(50, 1000000.0),
        )

        assert len(result) == 2
        assert result[0].symbol == "005930"
        assert result[0].side == "BUY"
        assert result[1].symbol == "035720"
        assert result[1].side == "SELL"

    def test_summary_provider_called_with_correct_args(self):
        """summary_provider가 올바른 인자로 호출되는지 확인."""
        intents = [_Intent("005930", "BUY", 100, "test")]
        provider = _DummySummaryProvider()
        engine = FeedbackAwareStrategyEngine(
            strategy=_DummyStrategy(intents),
            summary_provider=provider,
            lookback_days=60,
        )

        engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(0, 1000000.0),
        )

        assert len(provider.calls) == 1
        assert provider.calls[0] == ("005930", 60)

    def test_no_summary_provider_uses_default(self):
        """summary_provider가 없으면 DEFAULT_FEEDBACK_SUMMARY 사용."""
        intents = [_Intent("005930", "BUY", 100, "test")]
        engine = FeedbackAwareStrategyEngine(strategy=_DummyStrategy(intents))

        result = engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(0, 1000000.0),
        )

        # DEFAULT_FEEDBACK_SUMMARY: impact=15bps < max 20bps → 수량 유지
        assert result[0].qty == 100

    def test_build_enhanced_input_basic(self):
        """build_enhanced_input이 StrategyInputEnhanced를 올바르게 생성."""
        summary = FeedbackSummary(
            avg_slippage_bps=5.0,
            avg_market_impact_bps=8.0,
            avg_quality_score=0.9,
            sample_count=20,
        )
        provider = _DummySummaryProvider(summary)
        engine = FeedbackAwareStrategyEngine(
            strategy=_DummyStrategy(),
            summary_provider=provider,
        )

        inp = engine.build_enhanced_input(
            symbol="005930",
            price=75000.0,
            position_qty=10,
            cash=500000.0,
        )

        assert isinstance(inp, StrategyInputEnhanced)
        assert inp.symbol == "005930"
        assert inp.price == 75000.0
        assert inp.position_qty == 10
        assert inp.cash == 500000.0
        assert inp.avg_slippage_bps == 5.0
        assert inp.avg_quality_score == 0.9
        assert inp.sample_count == 20

    def test_build_enhanced_input_with_ticks(self):
        """틱 데이터가 있으면 실시간 메트릭 계산."""
        engine = FeedbackAwareStrategyEngine(strategy=_DummyStrategy())
        ticks = _make_ticks(n=6, base_price=75000.0, spread=50.0)

        inp = engine.build_enhanced_input(
            symbol="005930",
            price=75000.0,
            ticks=ticks,
        )

        assert inp.volatility > 0.0
        assert inp.spread_bps > 0.0
        assert inp.depth > 0

    def test_custom_max_impact(self):
        """max_acceptable_impact_bps 커스텀 설정."""
        intents = [_Intent("005930", "BUY", 100, "test")]
        summary = FeedbackSummary(
            avg_market_impact_bps=30.0,  # 30bps
            avg_quality_score=1.0,
            sample_count=10,
        )
        provider = _DummySummaryProvider(summary)

        # max_impact=50 → 30 < 50 이므로 수량 유지
        engine = FeedbackAwareStrategyEngine(
            strategy=_DummyStrategy(intents),
            summary_provider=provider,
            max_acceptable_impact_bps=50.0,
        )

        result = engine.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(0, 1000000.0),
        )
        assert result[0].qty == 100

        # max_impact=10 → 30 > 10 이므로 수량 축소
        engine2 = FeedbackAwareStrategyEngine(
            strategy=_DummyStrategy(intents),
            summary_provider=provider,
            max_acceptable_impact_bps=10.0,
        )

        result2 = engine2.generate_intents(
            _MarketCtx("005930", 75000.0),
            _ExecCtx(0, 1000000.0),
        )
        # 10/30 = 0.333... → 100 * 0.333 = 33
        assert result2[0].qty == 33
        assert result2[0].original_qty == 100


class TestEnhancedIntent:
    """EnhancedIntent 데이터 클래스 테스트."""

    def test_creation(self):
        ei = EnhancedIntent(
            symbol="005930",
            side="BUY",
            qty=100,
            reason="test",
            original_qty=200,
            adjusted_entry_price=Decimal("75075"),
            confidence=0.85,
        )
        assert ei.symbol == "005930"
        assert ei.side == "BUY"
        assert ei.qty == 100
        assert ei.original_qty == 200
        assert ei.adjusted_entry_price == Decimal("75075")
        assert ei.confidence == 0.85

    def test_frozen(self):
        ei = EnhancedIntent(
            symbol="005930",
            side="BUY",
            qty=100,
            reason="test",
            original_qty=100,
            adjusted_entry_price=Decimal("75000"),
            confidence=0.8,
        )
        with pytest.raises(AttributeError):
            ei.qty = 50  # type: ignore[misc]
