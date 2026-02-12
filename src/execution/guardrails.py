"""Execution Guardrails (GR060-064) + Fail-Safe (FS090-095)."""
from __future__ import annotations

from decimal import Decimal

from src.execution.contracts import (
    ExecutionAlert,
    ExecutionContext,
    SplitOrder,
    SplitOrderStatus,
)


# ---------------------------------------------------------------------------
# Guardrails (GR060-064)
# ---------------------------------------------------------------------------

def check_split_count(splits: list[SplitOrder], max_splits: int = 20) -> list[ExecutionAlert]:
    """GR060: 분할 주문 과다 검사."""
    if len(splits) > max_splits:
        return [ExecutionAlert(
            code="GR060",
            severity="GUARDRAIL",
            message=f"Split count {len(splits)} exceeds maximum {max_splits}",
            stage="SPLITTING",
        )]
    return []


def check_insufficient_balance(
    required: Decimal, available: Decimal
) -> list[ExecutionAlert]:
    """GR061: 잔고 부족 검사."""
    if required > available > 0:
        return [ExecutionAlert(
            code="GR061",
            severity="GUARDRAIL",
            message=f"Required {required} exceeds available {available}",
            stage="PRECHECK",
        )]
    if available <= 0:
        return [ExecutionAlert(
            code="GR061",
            severity="GUARDRAIL",
            message=f"No available balance",
            stage="PRECHECK",
        )]
    return []


def check_daily_trade_limit(
    current_count: int, limit: int = 100
) -> list[ExecutionAlert]:
    """GR062: 일일 거래 한도 검사."""
    if current_count >= limit:
        return [ExecutionAlert(
            code="GR062",
            severity="GUARDRAIL",
            message=f"Daily trade count {current_count} >= limit {limit}",
            stage="PRECHECK",
        )]
    return []


def check_slippage(
    original_price: Decimal, fill_price: Decimal, threshold: Decimal = Decimal("0.003")
) -> list[ExecutionAlert]:
    """GR063: 슬리피지 경고."""
    if original_price == 0:
        return []
    slippage = abs(fill_price - original_price) / original_price
    if slippage > threshold:
        return [ExecutionAlert(
            code="GR063",
            severity="GUARDRAIL",
            message=f"Slippage {slippage:.4f} exceeds threshold {threshold}",
            stage="MONITORING",
        )]
    return []


def check_fill_delay(elapsed_ms: float, threshold_ms: float = 30_000) -> list[ExecutionAlert]:
    """GR064: 체결 지연 경고."""
    if elapsed_ms > threshold_ms:
        return [ExecutionAlert(
            code="GR064",
            severity="WARNING",
            message=f"Fill delay {elapsed_ms:.0f}ms exceeds {threshold_ms:.0f}ms",
            stage="MONITORING",
        )]
    return []


# ---------------------------------------------------------------------------
# Fail-Safe (FS090-095)
# ---------------------------------------------------------------------------

def check_all_sends_failed(sent: int, failed: int) -> list[ExecutionAlert]:
    """FS090: 전송 전체 실패."""
    if sent == 0 and failed > 0:
        return [ExecutionAlert(
            code="FS090",
            severity="FAIL_SAFE",
            message=f"All {failed} order sends failed",
            stage="SENDING",
        )]
    return []


def check_invalid_symbol(symbol: str, valid_symbols: set[str] | None = None) -> list[ExecutionAlert]:
    """FS091: 잘못된 종목."""
    if not symbol or len(symbol) == 0:
        return [ExecutionAlert(
            code="FS091",
            severity="FAIL_SAFE",
            message=f"Empty symbol",
            stage="PRECHECK",
        )]
    if valid_symbols is not None and symbol not in valid_symbols:
        return [ExecutionAlert(
            code="FS091",
            severity="FAIL_SAFE",
            message=f"Invalid symbol: {symbol}",
            stage="PRECHECK",
        )]
    return []


def check_fill_timeout(filled_qty: int, total_qty: int) -> list[ExecutionAlert]:
    """FS093: 체결 타임아웃 (filled < total)."""
    if filled_qty < total_qty:
        return [ExecutionAlert(
            code="FS093",
            severity="FAIL_SAFE",
            message=f"Fill timeout: {filled_qty}/{total_qty} filled",
            stage="MONITORING",
        )]
    return []


def check_slippage_exceeded(
    original_price: Decimal,
    fill_price: Decimal,
    max_pct: Decimal = Decimal("0.005"),
) -> list[ExecutionAlert]:
    """FS094: 슬리피지 초과."""
    if original_price == 0:
        return []
    slippage = abs(fill_price - original_price) / original_price
    if slippage > max_pct:
        return [ExecutionAlert(
            code="FS094",
            severity="FAIL_SAFE",
            message=f"Slippage {slippage:.4f} exceeds max {max_pct}",
            stage="ADJUSTING",
        )]
    return []


# ---------------------------------------------------------------------------
# Combined
# ---------------------------------------------------------------------------

def run_execution_guardrails(ctx: ExecutionContext) -> list[ExecutionAlert]:
    """실행 컨텍스트에 대한 전체 가드레일 실행."""
    alerts: list[ExecutionAlert] = []

    # GR060
    alerts.extend(check_split_count(ctx.splits))

    # GR064
    if ctx.stage_start_time is not None:
        from datetime import datetime, timezone
        elapsed = (datetime.now(timezone.utc) - ctx.stage_start_time).total_seconds() * 1_000
        alerts.extend(check_fill_delay(elapsed))

    return alerts
