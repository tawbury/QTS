"""feedback/sheet_adapter.py 단위 테스트 — JsonlFeedbackDB."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.feedback.contracts import FeedbackData, FeedbackSummary
from src.feedback.sheet_adapter import JsonlFeedbackDB


def _make_feedback(symbol: str = "005930", **overrides) -> FeedbackData:
    now = datetime.now(timezone.utc)
    defaults = dict(
        symbol=symbol,
        execution_start=now,
        execution_end=now,
        feedback_generated_at=now,
        total_slippage_bps=6.67,
        avg_fill_latency_ms=45.0,
        partial_fill_ratio=0.0,
        total_filled_qty=Decimal("100"),
        avg_fill_price=Decimal("75050"),
        execution_quality_score=0.92,
        market_impact_bps=3.2,
        strategy_tag="SCALP_RSI",
    )
    defaults.update(overrides)
    return FeedbackData(**defaults)


class TestJsonlFeedbackDBStore:
    def test_store_creates_file(self, tmp_path):
        path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(path)
        db.store_feedback(_make_feedback())
        assert path.exists()

    def test_store_appends_lines(self, tmp_path):
        path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(path)
        db.store_feedback(_make_feedback())
        db.store_feedback(_make_feedback(symbol="035720"))
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_store_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "nested" / "dir" / "feedback.jsonl"
        db = JsonlFeedbackDB(path)
        db.store_feedback(_make_feedback())
        assert path.exists()


class TestJsonlFeedbackDBFetch:
    def test_fetch_empty_file_returns_none(self, tmp_path):
        path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(path)
        result = db.fetch_feedback_summary("005930", 30)
        assert result is None

    def test_fetch_nonexistent_file_returns_none(self, tmp_path):
        path = tmp_path / "nonexistent.jsonl"
        db = JsonlFeedbackDB(path)
        result = db.fetch_feedback_summary("005930", 30)
        assert result is None

    def test_fetch_returns_summary(self, tmp_path):
        path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(path)
        db.store_feedback(_make_feedback())
        db.store_feedback(_make_feedback())

        summary = db.fetch_feedback_summary("005930", 30)
        assert summary is not None
        assert summary.sample_count == 2
        assert pytest.approx(summary.avg_slippage_bps, abs=0.1) == 6.67

    def test_fetch_filters_by_symbol(self, tmp_path):
        path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(path)
        db.store_feedback(_make_feedback(symbol="005930"))
        db.store_feedback(_make_feedback(symbol="035720"))
        db.store_feedback(_make_feedback(symbol="005930"))

        summary = db.fetch_feedback_summary("005930", 30)
        assert summary is not None
        assert summary.sample_count == 2

    def test_fetch_filters_by_lookback_days(self, tmp_path):
        path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(path)

        # Recent feedback
        db.store_feedback(_make_feedback())

        # Old feedback (manually write)
        import json
        old_ts = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        old_record = {
            "symbol": "005930",
            "timestamp": old_ts,
            "slippage_bps": 20.0,
            "fill_latency_ms": 100.0,
            "fill_ratio": 0.8,
            "quality_score": 0.5,
            "impact_bps": 10.0,
            "strategy_tag": "SCALP_OLD",
            "filled_qty": "50",
        }
        with path.open("a") as f:
            f.write(json.dumps(old_record) + "\n")

        summary = db.fetch_feedback_summary("005930", 30)
        assert summary is not None
        assert summary.sample_count == 1  # only recent

    def test_fetch_skips_corrupt_lines(self, tmp_path):
        path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(path)
        db.store_feedback(_make_feedback())

        # Append corrupt line
        with path.open("a") as f:
            f.write("NOT_JSON\n")
            f.write("\n")  # blank line

        db.store_feedback(_make_feedback())

        summary = db.fetch_feedback_summary("005930", 30)
        assert summary is not None
        assert summary.sample_count == 2

    def test_fetch_summary_fields(self, tmp_path):
        path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(path)

        db.store_feedback(_make_feedback(
            total_slippage_bps=5.0,
            avg_fill_latency_ms=30.0,
            partial_fill_ratio=0.0,
            execution_quality_score=0.95,
            market_impact_bps=2.0,
        ))
        db.store_feedback(_make_feedback(
            total_slippage_bps=15.0,
            avg_fill_latency_ms=70.0,
            partial_fill_ratio=0.2,
            execution_quality_score=0.75,
            market_impact_bps=8.0,
        ))

        summary = db.fetch_feedback_summary("005930", 30)
        assert summary is not None
        assert pytest.approx(summary.avg_slippage_bps, abs=0.1) == 10.0
        assert pytest.approx(summary.avg_fill_latency_ms, abs=0.1) == 50.0
        assert pytest.approx(summary.avg_quality_score, abs=0.01) == 0.85
        assert pytest.approx(summary.avg_market_impact_bps, abs=0.1) == 5.0


class TestJsonlFeedbackDBRoundTrip:
    def test_store_and_fetch_cycle(self, tmp_path):
        path = tmp_path / "feedback.jsonl"
        db = JsonlFeedbackDB(path)

        for i in range(10):
            db.store_feedback(_make_feedback(
                total_slippage_bps=5.0 + i,
                execution_quality_score=0.90 - i * 0.01,
            ))

        summary = db.fetch_feedback_summary("005930", 30)
        assert summary is not None
        assert summary.sample_count == 10
        assert 5.0 < summary.avg_slippage_bps < 15.0
