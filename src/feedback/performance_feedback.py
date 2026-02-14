"""PerformanceFeedbackProvider - 실시간 성능 메트릭 → 포지션 크기 조정.

근거: docs/02-design/features/eteda-db-feedback-loop.design.md D-06
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PerformanceSnapshot:
    """실시간 성능 스냅샷."""

    daily_pnl: Decimal = Decimal("0")
    daily_mdd: float = 0.0
    consecutive_losses: int = 0
    sizing_multiplier: float = 1.0


# MDD → sizing multiplier 임계값
_MDD_THRESHOLDS = [
    (0.05, 0.0),   # MDD > 5%: 신규 진입 차단
    (0.03, 0.5),   # MDD > 3%: qty 50%
    (0.02, 0.7),   # MDD > 2%: qty 70%
]

# 연속 손실 차단 임계값
_MAX_CONSECUTIVE_LOSSES = 5


class PerformanceFeedbackProvider:
    """실시간 성능 메트릭 → 포지션 크기 조정.

    T_Ledger에서 당일 매매 기록을 조회하여 MDD, 연속 손실을 계산하고
    이를 기반으로 포지션 크기 배수를 산출한다.
    """

    def __init__(
        self,
        t_ledger_repo: Any,
        config: Any,
    ) -> None:
        self._ledger = t_ledger_repo
        self._config = config
        self._cached_snapshot: Optional[PerformanceSnapshot] = None

    def get_realtime_metrics(self) -> PerformanceSnapshot:
        """당일 PnL, MDD, 연속 손실 계산."""
        try:
            trades = self._get_today_trades()
            if not trades:
                return PerformanceSnapshot()

            daily_pnl = self._calculate_daily_pnl(trades)
            daily_mdd = self._calculate_daily_mdd(trades)
            consecutive_losses = self._count_consecutive_losses(trades)
            multiplier = self._compute_sizing_multiplier(daily_mdd, consecutive_losses)

            snapshot = PerformanceSnapshot(
                daily_pnl=daily_pnl,
                daily_mdd=daily_mdd,
                consecutive_losses=consecutive_losses,
                sizing_multiplier=multiplier,
            )
            self._cached_snapshot = snapshot
            return snapshot
        except Exception:
            logger.warning("Performance metrics calculation failed, using defaults")
            return self._cached_snapshot or PerformanceSnapshot()

    def get_sizing_multiplier(self) -> float:
        """MDD 기반 포지션 크기 배수."""
        snapshot = self.get_realtime_metrics()
        return snapshot.sizing_multiplier

    def should_block_new_entry(self) -> bool:
        """MDD > 5% 또는 연속 손실 >= 5 → 차단."""
        snapshot = self.get_realtime_metrics()
        if snapshot.daily_mdd > 0.05:
            logger.warning(
                f"[PerfFeedback] MDD {snapshot.daily_mdd:.1%} > 5%% → blocking new entry"
            )
            return True
        if snapshot.consecutive_losses >= _MAX_CONSECUTIVE_LOSSES:
            logger.warning(
                f"[PerfFeedback] Consecutive losses {snapshot.consecutive_losses} >= {_MAX_CONSECUTIVE_LOSSES} → blocking"
            )
            return True
        return False

    def _get_today_trades(self) -> list[dict]:
        """T_Ledger에서 당일 매매 기록 조회."""
        try:
            all_trades = self._ledger.get_all()
            if not all_trades:
                return []

            from datetime import date

            today = date.today().isoformat()
            return [
                t for t in all_trades
                if str(t.get("timestamp", "")).startswith(today)
            ]
        except Exception:
            return []

    @staticmethod
    def _calculate_daily_pnl(trades: list[dict]) -> Decimal:
        """당일 누적 PnL."""
        total = Decimal("0")
        for t in trades:
            pnl = t.get("pnl") or t.get("realized_pnl") or 0
            total += Decimal(str(pnl))
        return total

    @staticmethod
    def _calculate_daily_mdd(trades: list[dict]) -> float:
        """당일 최대 낙폭 (MDD) 비율."""
        if not trades:
            return 0.0

        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0

        for t in trades:
            pnl = float(t.get("pnl") or t.get("realized_pnl") or 0)
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # MDD를 비율로 변환 (기준: 일일 자본 100,000,000)
        base_capital = 100_000_000.0
        return max_drawdown / base_capital if base_capital > 0 else 0.0

    @staticmethod
    def _count_consecutive_losses(trades: list[dict]) -> int:
        """끝에서부터 연속 손실 횟수."""
        count = 0
        for t in reversed(trades):
            pnl = float(t.get("pnl") or t.get("realized_pnl") or 0)
            if pnl < 0:
                count += 1
            else:
                break
        return count

    @staticmethod
    def _compute_sizing_multiplier(mdd: float, consecutive_losses: int) -> float:
        """MDD + 연속 손실 기반 sizing multiplier."""
        # MDD 기반
        multiplier = 1.0
        for threshold, mult in _MDD_THRESHOLDS:
            if mdd > threshold:
                multiplier = mult
                break

        # 연속 손실 추가 감소
        if consecutive_losses >= _MAX_CONSECUTIVE_LOSSES:
            multiplier = 0.0
        elif consecutive_losses >= 3:
            multiplier = min(multiplier, 0.7)

        return multiplier
