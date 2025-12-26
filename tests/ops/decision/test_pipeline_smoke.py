import os
import shutil
import tempfile
from datetime import datetime, timezone

from ops.observer.analysis.decision_pipeline import (
    DecisionPipeline,
    DecisionConfig,
)


def test_decision_pipeline_smoke():
    """
    Phase 6 (Decision) Smoke Test

    Verifies:
      - raw JSONL persistence
      - feature build
      - parquet persistence
      - parquet loadability
    """

    tmp_dir = tempfile.mkdtemp(prefix="qts_decision_test_")

    try:
        cfg = DecisionConfig(
            base_dir=tmp_dir,
        )
        pipeline = DecisionPipeline(cfg)

        # --------------------------------------------------
        # dummy raw records
        # --------------------------------------------------
        base_ts = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())
        records = [
            {"timestamp": base_ts + 0, "price": 100},
            {"timestamp": base_ts + 10, "price": 101},
            {"timestamp": base_ts + 25, "price": 102},
        ]

        # --------------------------------------------------
        # persist raw
        # --------------------------------------------------
        raw_path = pipeline.persist_raw(
            build_id="build_test",
            session_id="session_test",
            date_yyyymmdd="2025-01-01",
            symbol="TEST",
            records=records,
        )

        assert os.path.exists(raw_path)
        assert raw_path.endswith(".jsonl")

        # --------------------------------------------------
        # build & persist features
        # --------------------------------------------------
        feature_path = pipeline.build_and_persist_features_from_records(
            build_id="build_test",
            session_id="session_test",
            date_yyyymmdd="2025-01-01",
            symbol="TEST",
            records=records,
        )

        assert os.path.exists(feature_path)
        assert feature_path.endswith(".parquet")

        # --------------------------------------------------
        # load parquet (via DecisionPipeline)
        # --------------------------------------------------
        rows = pipeline.load_features(
            build_id="build_test",
            session_id="session_test",
            date_yyyymmdd="2025-01-01",
            symbol="TEST",
        )

        assert isinstance(rows, list)
        assert len(rows) == 1
        assert rows[0]["record_count"] == 3

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
