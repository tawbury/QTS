"""Position Shadow Manager.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §2.2
- 메인 포지션 상태를 미러링하여 잠금 없이 접근
- sync_fields: 메인에서 동기화, local_fields: Micro Loop 전용
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Iterator, Optional

from src.micro_risk.contracts import (
    MicroRiskAlert,
    PositionShadow,
    SYNC_FIELDS,
)


class PositionShadowManager:
    """포지션 섀도우 관리자."""

    def __init__(self) -> None:
        self._shadows: dict[str, PositionShadow] = {}

    def add_position(self, shadow: PositionShadow) -> None:
        """포지션 섀도우 추가."""
        self._shadows[shadow.symbol] = shadow

    def remove_position(self, symbol: str) -> Optional[PositionShadow]:
        """포지션 섀도우 제거."""
        return self._shadows.pop(symbol, None)

    def get(self, symbol: str) -> Optional[PositionShadow]:
        """특정 심볼의 섀도우 반환."""
        return self._shadows.get(symbol)

    def has_position(self, symbol: str) -> bool:
        return symbol in self._shadows

    def items(self) -> Iterator[tuple[str, PositionShadow]]:
        """전체 섀도우 이터레이터."""
        yield from self._shadows.items()

    def count(self) -> int:
        return len(self._shadows)

    def symbols(self) -> list[str]:
        return list(self._shadows.keys())

    def sync_from_main(
        self, main_positions: dict[str, dict[str, Any]],
    ) -> list[MicroRiskAlert]:
        """메인 포지션에서 sync_fields 동기화 (§2.2.3).

        Args:
            main_positions: {symbol: {qty, avg_price, current_price, ...}}

        Returns:
            동기화 중 발생한 알림 목록
        """
        alerts: list[MicroRiskAlert] = []
        now = datetime.now(timezone.utc)

        for symbol, main_data in main_positions.items():
            shadow = self._shadows.get(symbol)
            if shadow is None:
                continue

            # 충돌 감지: qty 불일치 (§6.3) — sync 전에 체크
            if "qty" in main_data and shadow.qty != main_data["qty"]:
                alerts.append(MicroRiskAlert(
                    code="FS101",
                    message=f"Qty mismatch: shadow={shadow.qty}, main={main_data['qty']}",
                    meta={"symbol": symbol},
                ))

            # sync_fields 업데이트
            for f in SYNC_FIELDS:
                if f in main_data:
                    val = main_data[f]
                    if isinstance(val, (int, float)) and f != "qty":
                        val = Decimal(str(val))
                    setattr(shadow, f, val)

            shadow.last_sync_time = now

        return alerts

    def update_time_in_trade(self) -> None:
        """전체 포지션의 보유 시간 업데이트."""
        now = datetime.now(timezone.utc)
        for shadow in self._shadows.values():
            delta = now - shadow.entry_time
            shadow.time_in_trade_sec = int(delta.total_seconds())

    def check_sync_staleness(
        self, stale_threshold_ms: int = 1000,
    ) -> list[MicroRiskAlert]:
        """동기화 지연 감지 (§2.2.3)."""
        alerts: list[MicroRiskAlert] = []
        now = datetime.now(timezone.utc)

        for symbol, shadow in self._shadows.items():
            delay_ms = (now - shadow.last_sync_time).total_seconds() * 1000
            if delay_ms > stale_threshold_ms:
                alerts.append(MicroRiskAlert(
                    code="FS101",
                    message=f"Sync stale: {symbol} delay={delay_ms:.0f}ms",
                    severity="CRITICAL" if delay_ms > stale_threshold_ms * 2 else "WARNING",
                    meta={"symbol": symbol, "delay_ms": delay_ms},
                ))

        return alerts
