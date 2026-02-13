"""Strategy Enhancement — 피드백 기반 전략 파라미터 보정.

기존 함수: 슬리피지 보정, 수량 조정, 신뢰도 보정 (유틸리티).
FeedbackAwareStrategyEngine: Strategy Protocol 래퍼 — 피드백 메트릭을 전략 입력에 주입하고
    실행 품질 기반으로 Intent 수량/신뢰도를 보정한다.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Protocol, Sequence

from src.feedback.contracts import (
    FeedbackSummary,
    DEFAULT_FEEDBACK_SUMMARY,
    TickRecord,
)
from src.feedback.tick_analysis import (
    calculate_depth,
    calculate_spread_bps,
    calculate_volatility,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 유틸리티 함수 (기존)
# ---------------------------------------------------------------------------


def calculate_adjusted_entry_price(
    signal_price: Decimal,
    historical_slippage_bps: float,
    side: str,
) -> Decimal:
    """슬리피지 보정 진입가 계산.

    BUY: 슬리피지만큼 높은 가격 예상 → 제한가를 올림.
    SELL: 슬리피지만큼 낮은 가격 예상 → 제한가를 내림.
    """
    if signal_price <= 0:
        return signal_price

    slippage_factor = Decimal(str(historical_slippage_bps / 10000))

    if side.upper() == "BUY":
        return signal_price * (1 + slippage_factor)
    else:
        return signal_price * (1 - slippage_factor)


def adjust_qty_for_market_impact(
    target_qty: Decimal,
    estimated_impact_bps: float,
    max_acceptable_impact_bps: float = 20.0,
) -> Decimal:
    """시장 충격 기반 수량 조정.

    예상 충격이 허용치를 초과하면 수량을 비례 축소한다.
    """
    if target_qty <= 0:
        return target_qty

    if estimated_impact_bps <= max_acceptable_impact_bps:
        return target_qty

    reduction_ratio = max_acceptable_impact_bps / estimated_impact_bps
    adjusted = target_qty * Decimal(str(reduction_ratio))

    logger.warning(
        "Qty reduced due to market impact: %s → %s (impact=%.1f bps, max=%.1f bps)",
        target_qty, adjusted, estimated_impact_bps, max_acceptable_impact_bps,
    )
    return adjusted


def adjust_confidence(
    raw_confidence: float,
    quality_score: float,
) -> float:
    """실행 품질 기반 신뢰도 보정."""
    return max(0.0, min(1.0, raw_confidence * quality_score))


# ---------------------------------------------------------------------------
# StrategyInputEnhanced — 전략 입력에 피드백 메트릭 추가
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StrategyInputEnhanced:
    """기존 전략 입력에 피드백 메트릭을 부착한 확장 입력.

    Strategy가 피드백 정보를 몰라도 되지만, 피드백 인지 전략은
    이 객체를 통해 volatility/spread/depth/quality 등을 활용할 수 있다.
    """

    # 원본 전략 입력 (Strategy Protocol의 MarketContext, ExecutionContext)
    symbol: str
    price: float
    position_qty: int = 0
    cash: float = 0.0

    # 피드백 메트릭 (tick_analysis.py 결과)
    volatility: float = 0.0
    spread_bps: float = 0.0
    depth: int = 0

    # 피드백 요약 (aggregator 결과)
    avg_slippage_bps: float = 10.0
    avg_market_impact_bps: float = 15.0
    avg_quality_score: float = 0.75
    avg_fill_latency_ms: float = 50.0
    avg_fill_ratio: float = 0.95
    sample_count: int = 0

    @classmethod
    def from_feedback_summary(
        cls,
        *,
        symbol: str,
        price: float,
        position_qty: int = 0,
        cash: float = 0.0,
        ticks: list[TickRecord] | None = None,
        summary: FeedbackSummary | None = None,
    ) -> StrategyInputEnhanced:
        """tick 데이터와 FeedbackSummary로부터 생성."""
        _ticks = ticks or []
        _summary = summary or DEFAULT_FEEDBACK_SUMMARY

        volatility = calculate_volatility(_ticks) if _ticks else 0.0
        spread_bps = calculate_spread_bps(_ticks) if _ticks else 0.0
        depth = calculate_depth(_ticks) if _ticks else 0

        return cls(
            symbol=symbol,
            price=price,
            position_qty=position_qty,
            cash=cash,
            volatility=volatility,
            spread_bps=spread_bps,
            depth=depth,
            avg_slippage_bps=_summary.avg_slippage_bps,
            avg_market_impact_bps=_summary.avg_market_impact_bps,
            avg_quality_score=_summary.avg_quality_score,
            avg_fill_latency_ms=_summary.avg_fill_latency_ms,
            avg_fill_ratio=_summary.avg_fill_ratio,
            sample_count=_summary.sample_count,
        )


# ---------------------------------------------------------------------------
# FeedbackSummaryProvider — 피드백 요약 조회 프로토콜
# ---------------------------------------------------------------------------


class FeedbackSummaryProvider(Protocol):
    """종목별 FeedbackSummary를 제공하는 프로토콜.

    FeedbackAggregator.get_summary() 와 호환된다.
    """

    def get_summary(
        self, symbol: str, lookback_days: int = 30,
    ) -> FeedbackSummary: ...


# ---------------------------------------------------------------------------
# FeedbackAwareStrategyEngine — Strategy 래퍼
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EnhancedIntent:
    """피드백 보정이 적용된 Intent."""

    symbol: str
    side: str
    qty: int
    reason: str
    original_qty: int
    adjusted_entry_price: Decimal
    confidence: float


class FeedbackAwareStrategyEngine:
    """기존 Strategy를 감싸서 피드백 기반 보정을 적용하는 래퍼.

    역할:
    1. StrategyInputEnhanced를 생성하여 피드백 메트릭을 전략에 전달할 수 있도록 한다.
    2. Strategy가 생성한 Intent의 수량/진입가/신뢰도를 피드백 기반으로 보정한다.
    3. 기존 Strategy 구현에 영향을 주지 않는 데코레이터 패턴.

    사용 예:
        engine = FeedbackAwareStrategyEngine(
            strategy=my_strategy,
            summary_provider=aggregator,
        )
        intents = engine.generate_intents(market, execution, ticks=recent_ticks)
    """

    def __init__(
        self,
        strategy: object,
        summary_provider: FeedbackSummaryProvider | None = None,
        max_acceptable_impact_bps: float = 20.0,
        lookback_days: int = 30,
        confidence: float = 0.8,
    ) -> None:
        """초기화.

        Args:
            strategy: Strategy Protocol 구현체 (generate_intents 메서드 필요).
            summary_provider: 종목별 FeedbackSummary 제공자 (없으면 기본값 사용).
            max_acceptable_impact_bps: 최대 허용 시장 충격 (bps).
            lookback_days: 피드백 조회 기간 (일).
            confidence: 기본 신뢰도 (0.0~1.0).
        """
        if not hasattr(strategy, "generate_intents"):
            raise TypeError(
                "strategy must implement generate_intents(market, execution)"
            )
        self._strategy = strategy
        self._summary_provider = summary_provider
        self._max_impact_bps = max_acceptable_impact_bps
        self._lookback_days = lookback_days
        self._confidence = confidence

    # -- public API --

    def build_enhanced_input(
        self,
        *,
        symbol: str,
        price: float,
        position_qty: int = 0,
        cash: float = 0.0,
        ticks: list[TickRecord] | None = None,
    ) -> StrategyInputEnhanced:
        """피드백 메트릭이 포함된 확장 입력을 생성한다."""
        summary = self._get_summary(symbol)
        return StrategyInputEnhanced.from_feedback_summary(
            symbol=symbol,
            price=price,
            position_qty=position_qty,
            cash=cash,
            ticks=ticks,
            summary=summary,
        )

    def generate_intents(
        self,
        market: object,
        execution: object,
        *,
        ticks: list[TickRecord] | None = None,
    ) -> list[EnhancedIntent]:
        """기존 Strategy의 Intent를 생성한 뒤 피드백 기반으로 보정한다.

        Args:
            market: Strategy Protocol의 MarketContext (symbol, price 필드).
            execution: Strategy Protocol의 ExecutionContext (position_qty, cash 필드).
            ticks: 최근 틱 데이터 (선택적).

        Returns:
            피드백 보정된 EnhancedIntent 리스트.
        """
        # 1. 기존 전략으로 원본 Intent 생성
        raw_intents = self._strategy.generate_intents(market, execution)  # type: ignore[attr-defined]

        if not raw_intents:
            return []

        # 2. 종목별 피드백 요약 조회
        symbol = getattr(market, "symbol", "")
        price = getattr(market, "price", 0.0)
        summary = self._get_summary(symbol)

        # 3. 틱 분석으로 실시간 시장 상태 계산
        _ticks = ticks or []
        volatility = calculate_volatility(_ticks) if _ticks else 0.0
        spread_bps = calculate_spread_bps(_ticks) if _ticks else 0.0

        # 4. 각 Intent에 피드백 보정 적용
        enhanced: list[EnhancedIntent] = []
        for intent in raw_intents:
            enhanced_intent = self._enhance_intent(
                intent=intent,
                summary=summary,
                price=price,
                volatility=volatility,
                spread_bps=spread_bps,
            )
            enhanced.append(enhanced_intent)

        return enhanced

    # -- internal --

    def _get_summary(self, symbol: str) -> FeedbackSummary:
        """피드백 요약 조회 (provider 없으면 기본값)."""
        if self._summary_provider is not None:
            return self._summary_provider.get_summary(
                symbol, self._lookback_days,
            )
        return DEFAULT_FEEDBACK_SUMMARY

    def _enhance_intent(
        self,
        *,
        intent: object,
        summary: FeedbackSummary,
        price: float,
        volatility: float,
        spread_bps: float,
    ) -> EnhancedIntent:
        """단일 Intent에 피드백 보정을 적용한다."""
        symbol = getattr(intent, "symbol", "")
        side = getattr(intent, "side", "")
        qty = getattr(intent, "qty", 0)
        reason = getattr(intent, "reason", "")

        # 슬리피지 보정 진입가
        signal_price = Decimal(str(price)) if price > 0 else Decimal("0")
        adjusted_price = calculate_adjusted_entry_price(
            signal_price=signal_price,
            historical_slippage_bps=summary.avg_slippage_bps,
            side=side,
        )

        # 시장 충격 기반 수량 보정
        adjusted_qty_dec = adjust_qty_for_market_impact(
            target_qty=Decimal(str(qty)),
            estimated_impact_bps=summary.avg_market_impact_bps,
            max_acceptable_impact_bps=self._max_impact_bps,
        )
        adjusted_qty = max(0, int(adjusted_qty_dec))

        # 실행 품질 기반 신뢰도 보정
        confidence = adjust_confidence(
            self._confidence,
            summary.avg_quality_score,
        )

        # 변동성이 높으면 추가 신뢰도 감소 (보수적 대응)
        if volatility > 0.02:  # 2% 이상 변동성
            confidence *= 0.9
            confidence = max(0.0, min(1.0, confidence))

        enhanced_reason = reason
        if summary.sample_count > 0:
            enhanced_reason = (
                f"{reason} "
                f"[fb: slip={summary.avg_slippage_bps:.1f}bps, "
                f"impact={summary.avg_market_impact_bps:.1f}bps, "
                f"qual={summary.avg_quality_score:.2f}, "
                f"vol={volatility:.4f}]"
            )

        return EnhancedIntent(
            symbol=symbol,
            side=side,
            qty=adjusted_qty,
            reason=enhanced_reason,
            original_qty=qty,
            adjusted_entry_price=adjusted_price,
            confidence=confidence,
        )
