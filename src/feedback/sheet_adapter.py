"""FeedbackDBAdapter 구현체: JSONL 파일 기반 경량 저장소.

Phase 1: 빠른 파이프라인 연결을 위한 로컬 JSONL 저장.
향후 PostgreSQL/TimescaleDB 이관 시 DB Adapter만 교체하면 됨.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from src.feedback.contracts import FeedbackData, FeedbackSummary

logger = logging.getLogger(__name__)


class JsonlFeedbackDB:
    """JSONL 파일 기반 피드백 저장소.

    FeedbackDBAdapter Protocol 구현:
    - store_feedback(FeedbackData) -> None
    - fetch_feedback_summary(symbol, lookback_days) -> Optional[FeedbackSummary]
    """

    def __init__(self, storage_path: Path) -> None:
        self._path = storage_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def store_feedback(self, feedback: FeedbackData) -> None:
        """피드백 데이터를 JSONL에 append."""
        record = {
            "symbol": feedback.symbol,
            "timestamp": feedback.feedback_generated_at.isoformat(),
            "slippage_bps": feedback.total_slippage_bps,
            "fill_latency_ms": feedback.avg_fill_latency_ms,
            "fill_ratio": 1.0 - feedback.partial_fill_ratio,
            "quality_score": feedback.execution_quality_score,
            "impact_bps": feedback.market_impact_bps,
            "strategy_tag": feedback.strategy_tag,
            "filled_qty": str(feedback.total_filled_qty),
        }
        try:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            logger.exception("Failed to store feedback to JSONL")

    def fetch_feedback_summary(
        self,
        symbol: str,
        lookback_days: int,
    ) -> Optional[FeedbackSummary]:
        """종목별 최근 N일 피드백 집계."""
        if not self._path.exists():
            return None

        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        records: list[dict] = []

        try:
            with self._path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if row.get("symbol") != symbol:
                        continue
                    ts_str = row.get("timestamp", "")
                    try:
                        ts = datetime.fromisoformat(ts_str)
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        continue
                    if ts >= cutoff:
                        records.append(row)
        except Exception:
            logger.exception("Failed to read feedback JSONL")
            return None

        if not records:
            return None

        n = len(records)
        return FeedbackSummary(
            avg_slippage_bps=sum(r.get("slippage_bps", 0) for r in records) / n,
            avg_market_impact_bps=sum(r.get("impact_bps", 0) for r in records) / n,
            avg_quality_score=sum(r.get("quality_score", 0) for r in records) / n,
            avg_fill_latency_ms=sum(r.get("fill_latency_ms", 0) for r in records) / n,
            avg_fill_ratio=sum(r.get("fill_ratio", 0) for r in records) / n,
            sample_count=n,
        )
