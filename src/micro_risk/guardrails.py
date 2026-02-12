"""Micro Risk Loop Guardrails.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §7
- FS100-FS105: Fail-Safe 코드
- GR070-GR074: Guardrail 코드
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.micro_risk.contracts import (
    MicroRiskAlert,
    MicroRiskConfig,
    PositionShadow,
)


# --- Fail-Safe (FS100-FS105) ---

def check_loop_error(error: Optional[Exception] = None) -> list[MicroRiskAlert]:
    """FS100: Micro Loop 크래시."""
    if error is None:
        return []
    return [MicroRiskAlert(
        code="FS100",
        message=f"Micro loop error: {error}",
        severity="CRITICAL",
        meta={"error_type": type(error).__name__},
    )]


def check_sync_delay(delay_ms: float, threshold_ms: float = 1000) -> list[MicroRiskAlert]:
    """FS101: 동기화 지연."""
    if delay_ms <= threshold_ms:
        return []
    return [MicroRiskAlert(
        code="FS101",
        message=f"Sync delay: {delay_ms:.0f}ms > {threshold_ms:.0f}ms",
        severity="CRITICAL" if delay_ms > threshold_ms * 2 else "WARNING",
        meta={"delay_ms": delay_ms, "threshold_ms": threshold_ms},
    )]


def check_emergency_exit(symbol: str, qty: int, reason: str) -> list[MicroRiskAlert]:
    """FS102: 긴급 청산 실행."""
    return [MicroRiskAlert(
        code="FS102",
        message=f"Emergency exit: {symbol} qty={qty} reason={reason}",
        severity="CRITICAL",
        meta={"symbol": symbol, "qty": qty, "reason": reason},
    )]


def check_eteda_suspend(reason: str) -> list[MicroRiskAlert]:
    """FS103: ETEDA 정지 요청."""
    return [MicroRiskAlert(
        code="FS103",
        message=f"ETEDA suspend: {reason}",
        severity="CRITICAL",
        meta={"reason": reason},
    )]


def check_kill_switch(reason: str) -> list[MicroRiskAlert]:
    """FS104: Kill Switch 발동."""
    return [MicroRiskAlert(
        code="FS104",
        message=f"Kill switch: {reason}",
        severity="CRITICAL",
        meta={"reason": reason},
    )]


def check_price_feed_interrupted(
    symbol: str, is_stale: bool,
) -> list[MicroRiskAlert]:
    """FS105: 가격 피드 중단."""
    if not is_stale:
        return []
    return [MicroRiskAlert(
        code="FS105",
        message=f"Price feed interrupted: {symbol}",
        severity="WARNING",
        meta={"symbol": symbol},
    )]


# --- Guardrails (GR070-GR074) ---

def check_trailing_stop_adjustment_frequency(
    adjustments_count: int, max_per_minute: int = 60,
) -> list[MicroRiskAlert]:
    """GR070: 트레일링 스탑 과다 조정."""
    if adjustments_count <= max_per_minute:
        return []
    return [MicroRiskAlert(
        code="GR070",
        message=f"Trailing stop excessive: {adjustments_count}/{max_per_minute} per minute",
        meta={"count": adjustments_count, "limit": max_per_minute},
    )]


def check_mae_approaching(
    mae_pct: Decimal,
    threshold_pct: Decimal,
    warning_ratio: Decimal = Decimal("0.80"),
) -> list[MicroRiskAlert]:
    """GR071: MAE 임계값 근접."""
    warning_level = threshold_pct * warning_ratio
    if abs(mae_pct) < warning_level:
        return []
    return [MicroRiskAlert(
        code="GR071",
        message=f"MAE approaching: {mae_pct} (threshold={threshold_pct})",
        meta={"mae_pct": str(mae_pct), "threshold": str(threshold_pct)},
    )]


def check_time_warning(
    time_in_trade_sec: int,
    max_time_sec: int,
    warning_at_pct: Decimal = Decimal("0.80"),
) -> list[MicroRiskAlert]:
    """GR072: 보유 시간 경고."""
    warning_sec = int(max_time_sec * warning_at_pct)
    if time_in_trade_sec < warning_sec:
        return []
    return [MicroRiskAlert(
        code="GR072",
        message=f"Time warning: {time_in_trade_sec}s / {max_time_sec}s",
        meta={"time_sec": time_in_trade_sec, "max_sec": max_time_sec},
    )]


def check_volatility_rising(
    vix: Decimal,
    warning_level: Decimal = Decimal("25"),
) -> list[MicroRiskAlert]:
    """GR073: 변동성 상승."""
    if vix < warning_level:
        return []
    return [MicroRiskAlert(
        code="GR073",
        message=f"Volatility rising: VIX={vix}",
        meta={"vix": str(vix)},
    )]


def check_emergency_order_failure(
    success: bool, symbol: str,
) -> list[MicroRiskAlert]:
    """GR074: 긴급 주문 실패."""
    if success:
        return []
    return [MicroRiskAlert(
        code="GR074",
        message=f"Emergency order failed: {symbol}",
        severity="CRITICAL",
        meta={"symbol": symbol},
    )]


# --- Combined Runner ---

def run_micro_risk_guardrails(
    shadow: PositionShadow,
    config: MicroRiskConfig,
    market_vix: Decimal = Decimal("20"),
    trailing_adjustments: int = 0,
) -> list[MicroRiskAlert]:
    """전체 Micro Risk guardrail 실행."""
    alerts: list[MicroRiskAlert] = []

    # GR071: MAE 근접
    alerts.extend(check_mae_approaching(
        shadow.mae_pct, config.mae.position_mae_threshold_pct,
    ))

    # GR072: 보유 시간
    max_time = config.time_in_trade.get_max_time(shadow.strategy)
    if max_time is not None:
        alerts.extend(check_time_warning(
            shadow.time_in_trade_sec, max_time, config.time_in_trade.warning_at_pct,
        ))

    # GR073: 변동성
    alerts.extend(check_volatility_rising(
        market_vix, config.volatility.vix_warning_level,
    ))

    # GR070: 트레일링 스탑 과다
    alerts.extend(check_trailing_stop_adjustment_frequency(trailing_adjustments))

    return alerts
