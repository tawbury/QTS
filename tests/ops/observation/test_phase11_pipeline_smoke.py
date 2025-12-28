from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.observer.analysis.pipeline import run_phase11_pipeline
from src.ops.observer.analysis.dataset_builder import build_observation_replay_dataset
from src.ops.observer.analysis.stats import aggregate_observation_replay_stats


def _get_input_path() -> Path:
    """
    Phase 11 smoke test input.

    NOTE:
    - paths.py 도입 이전 테스트이므로
      예외적으로 상대 경로를 허용한다.
    - 이후 paths.py 전환 시 이 함수만 수정 대상.
    """
    return Path("data/observer/observer_test.jsonl")


@pytest.mark.smoke
def test_phase11_pipeline_smoke():
    """
    Phase 11 Smoke Test

    Success criteria:
    1) observer log(JSONL)을 코드로 다시 읽을 수 있다
    2) deterministic time axis를 생성한다
    3) replay dataset을 구성할 수 있다
    4) 최소 통계를 산출할 수 있다
    """

    input_path = _get_input_path()
    assert input_path.exists(), "Smoke test input file does not exist."

    # -----------------------------------------------------------------
    # 1) Run Phase 11 pipeline (load + time axis)
    # -----------------------------------------------------------------
    result = run_phase11_pipeline(
        input_path=input_path,
        enforce_monotonic=False,
    )

    assert result["phase"] == 11
    assert "load" in result
    assert "time_axis" in result

    load = result["load"]
    time_axis = result["time_axis"]

    assert load.loaded > 0, "No records loaded in Phase 11 pipeline."
    assert time_axis.total_records == load.loaded

    # -----------------------------------------------------------------
    # 2) Build replay dataset (in-memory asset)
    # -----------------------------------------------------------------
    dataset = build_observation_replay_dataset(
        time_axis=time_axis,
        source=str(input_path),
    )

    assert "meta" in dataset
    assert "records" in dataset
    assert dataset["meta"]["phase"] == 11
    assert dataset["meta"]["total_records"] == load.loaded
    assert len(dataset["records"]) == load.loaded

    # -----------------------------------------------------------------
    # 3) Aggregate minimal replay stats
    # -----------------------------------------------------------------
    stats = aggregate_observation_replay_stats(time_axis=time_axis)

    assert stats.total_records == load.loaded
    assert stats.first_ts_utc is not None
    assert stats.last_ts_utc is not None
    assert stats.duration_seconds is not None
