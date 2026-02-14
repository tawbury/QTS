"""PerformanceFeedbackProvider 단위 테스트.

근거: docs/02-design/features/eteda-db-feedback-loop.design.md T-03
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.feedback.performance_feedback import (
    PerformanceFeedbackProvider,
    PerformanceSnapshot,
)


def _make_provider(trades: list[dict]) -> PerformanceFeedbackProvider:
    """테스트용 Provider 생성."""
    mock_ledger = MagicMock()
    mock_ledger.get_all.return_value = trades
    mock_config = MagicMock()
    return PerformanceFeedbackProvider(mock_ledger, mock_config)


def _today_trade(pnl: float) -> dict:
    """당일 매매 기록 생성."""
    from datetime import date
    return {
        "timestamp": f"{date.today().isoformat()}T10:00:00",
        "pnl": pnl,
    }


class TestSizingMultiplier:
    def test_normal_mdd(self):
        """MDD < 2% -> multiplier 1.0."""
        # 소폭 손실 (MDD ~= 0.01%)
        trades = [_today_trade(100_000), _today_trade(-50_000)]
        provider = _make_provider(trades)
        assert provider.get_sizing_multiplier() == 1.0

    def test_warning_mdd(self):
        """MDD > 2% -> multiplier 0.7."""
        # MDD ~= 2.5% (base capital = 100M)
        trades = [_today_trade(-2_500_000)]
        provider = _make_provider(trades)
        mult = provider.get_sizing_multiplier()
        assert mult == 0.7

    def test_critical_mdd(self):
        """MDD > 3% -> multiplier 0.5."""
        trades = [_today_trade(-3_500_000)]
        provider = _make_provider(trades)
        mult = provider.get_sizing_multiplier()
        assert mult == 0.5

    def test_blocking_mdd(self):
        """MDD > 5% -> multiplier 0.0."""
        trades = [_today_trade(-6_000_000)]
        provider = _make_provider(trades)
        mult = provider.get_sizing_multiplier()
        assert mult == 0.0


class TestBlockNewEntry:
    def test_mdd_over_5pct(self):
        """MDD > 5% -> 차단."""
        trades = [_today_trade(-6_000_000)]
        provider = _make_provider(trades)
        assert provider.should_block_new_entry() is True

    def test_consecutive_losses(self):
        """연속 5회 손실 -> 차단."""
        trades = [
            _today_trade(100_000),  # 이익 (무시)
            _today_trade(-10_000),
            _today_trade(-10_000),
            _today_trade(-10_000),
            _today_trade(-10_000),
            _today_trade(-10_000),
        ]
        provider = _make_provider(trades)
        assert provider.should_block_new_entry() is True

    def test_normal_no_block(self):
        """정상 상태 -> 차단 안함."""
        trades = [_today_trade(100_000), _today_trade(-50_000)]
        provider = _make_provider(trades)
        assert provider.should_block_new_entry() is False

    def test_no_trades(self):
        """매매 없음 -> 차단 안함."""
        provider = _make_provider([])
        assert provider.should_block_new_entry() is False


class TestPerformanceSnapshot:
    def test_snapshot_defaults(self):
        """기본값 확인."""
        snap = PerformanceSnapshot()
        assert snap.daily_pnl == Decimal("0")
        assert snap.daily_mdd == 0.0
        assert snap.consecutive_losses == 0
        assert snap.sizing_multiplier == 1.0

    def test_snapshot_frozen(self):
        """frozen dataclass."""
        snap = PerformanceSnapshot()
        with pytest.raises(AttributeError):
            snap.daily_pnl = Decimal("100")  # type: ignore[misc]


class TestConsecutiveLosses:
    def test_count_from_end(self):
        """끝에서부터 연속 손실 카운트."""
        trades = [
            _today_trade(100_000),
            _today_trade(-10_000),
            _today_trade(-20_000),
            _today_trade(-30_000),
        ]
        provider = _make_provider(trades)
        snap = provider.get_realtime_metrics()
        assert snap.consecutive_losses == 3

    def test_interrupted_by_profit(self):
        """이익이 끼면 카운트 중단."""
        trades = [
            _today_trade(-10_000),
            _today_trade(-20_000),
            _today_trade(50_000),  # 이익
            _today_trade(-10_000),
        ]
        provider = _make_provider(trades)
        snap = provider.get_realtime_metrics()
        assert snap.consecutive_losses == 1


class TestConsecutiveLossMultiplier:
    def test_3_consecutive_losses_caps_at_0_7(self):
        """연속 3회 손실 -> multiplier <= 0.7."""
        trades = [
            _today_trade(100_000),
            _today_trade(-10_000),
            _today_trade(-10_000),
            _today_trade(-10_000),
        ]
        provider = _make_provider(trades)
        mult = provider.get_sizing_multiplier()
        assert mult <= 0.7
