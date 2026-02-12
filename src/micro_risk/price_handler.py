"""Price Feed Handler.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §2.3
- 실시간 가격 피드 수신 및 버퍼 관리
- 가격 이상 감지
- 포지션 섀도우 가격 업데이트
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from src.micro_risk.contracts import MicroRiskAlert, PriceFeed, PositionShadow


class PriceFeedHandler:
    """가격 피드 핸들러 (§2.3)."""

    def __init__(self, buffer_size: int = 100) -> None:
        self._buffer_size = buffer_size
        self._buffers: dict[str, deque[PriceFeed]] = {}

    def on_price_tick(
        self,
        feed: PriceFeed,
        shadow: Optional[PositionShadow] = None,
    ) -> list[MicroRiskAlert]:
        """가격 틱 수신.

        Returns:
            이상 감지 시 알림 목록
        """
        alerts: list[MicroRiskAlert] = []
        symbol = feed.symbol

        # 이상 감지
        if self.detect_anomaly(symbol, feed.price):
            alerts.append(MicroRiskAlert(
                code="FS105",
                message=f"Price anomaly: {symbol} price={feed.price}",
                severity="WARNING",
                meta={"symbol": symbol, "price": str(feed.price)},
            ))

        # 버퍼에 추가
        if symbol not in self._buffers:
            self._buffers[symbol] = deque(maxlen=self._buffer_size)
        self._buffers[symbol].append(feed)

        # 섀도우 업데이트
        if shadow is not None:
            shadow.current_price = feed.price
            shadow.update_pnl()
            shadow.update_extremes(feed.price)

        return alerts

    def get_latest(self, symbol: str) -> Optional[PriceFeed]:
        """최신 PriceFeed 반환."""
        buf = self._buffers.get(symbol)
        if buf and len(buf) > 0:
            return buf[-1]
        return None

    def get_buffer(self, symbol: str) -> list[PriceFeed]:
        """심볼의 전체 가격 버퍼."""
        buf = self._buffers.get(symbol)
        return list(buf) if buf else []

    def is_price_stale(self, symbol: str, threshold_ms: int = 500) -> bool:
        """가격 데이터 stale 여부 (§2.3.3)."""
        buf = self._buffers.get(symbol)
        if not buf or len(buf) == 0:
            return True

        last_tick = buf[-1]
        now = datetime.now(timezone.utc)
        age_ms = (now - last_tick.timestamp).total_seconds() * 1000
        return age_ms > threshold_ms

    def detect_anomaly(
        self,
        symbol: str,
        new_price: Decimal,
        threshold_pct: Decimal = Decimal("0.05"),
    ) -> bool:
        """가격 급변 감지 (§2.3.4).

        1틱 사이에 threshold_pct 이상 변동은 이상.
        """
        buf = self._buffers.get(symbol)
        if not buf or len(buf) < 1:
            return False

        prev_price = buf[-1].price
        if prev_price <= 0:
            return False

        change_pct = abs((new_price - prev_price) / prev_price)
        return change_pct > threshold_pct

    def has_data(self, symbol: str) -> bool:
        """해당 심볼에 가격 데이터가 있는지."""
        buf = self._buffers.get(symbol)
        return buf is not None and len(buf) > 0

    def clear(self, symbol: Optional[str] = None) -> None:
        """버퍼 초기화."""
        if symbol:
            self._buffers.pop(symbol, None)
        else:
            self._buffers.clear()
