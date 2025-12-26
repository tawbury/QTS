from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

import pytest

from paths import observer_data_dir
from src.ops.decision_pipeline.pipeline.runner import DecisionPipelineRunner
from src.ops.decision_pipeline.execution_stub.execution_context import ExecutionContext
from src.ops.decision_pipeline.execution_stub.noop_executor import NoopExecutor


@pytest.fixture
def pipeline_runner() -> DecisionPipelineRunner:
    return DecisionPipelineRunner()


@pytest.fixture
def noop_executor() -> NoopExecutor:
    return NoopExecutor()


@pytest.fixture
def test_context() -> Dict[str, Any]:
    """
    Phase 7 테스트용 최소 컨텍스트
    """
    return {
        "source": "pytest",
        "session_id": "test-session-001",
        "inputs": {
            "symbol": "TEST",
            "signal": "NONE",
        },
    }


def test_phase7_decision_pipeline_e2e(
    pipeline_runner: DecisionPipelineRunner,
    noop_executor: NoopExecutor,
    test_context: Dict[str, Any],
):
    """
    Phase 7 e2e 테스트

    검증 포인트:
    1. 파이프라인이 정상 실행되는가
    2. Execution은 반드시 NOOP인가
    3. DecisionSnapshot이 생성되는가
    4. 결과 jsonl 파일이 QTS/data/observer/에 생성되는가
    """

    # -------------------------
    # 1. 파이프라인 실행
    # -------------------------
    result = pipeline_runner.run(
        test_context,
        strategy_name="test_strategy",
    )

    assert "order_decision" in result
    assert "decision_snapshot" in result
    assert "execution_hint" in result

    snapshot = result["decision_snapshot"]
    order = result["order_decision"]
    hint = result["execution_hint"]

    # -------------------------
    # 2. Execution Stub 호출
    # -------------------------
    exec_ctx = ExecutionContext()
    exec_result = noop_executor.execute(
        order=order,
        hint=hint,
        context=exec_ctx,
    )

    assert exec_result.executed is False
    assert exec_result.status == "NOOP"

    # -------------------------
    # 3. Snapshot 검증
    # -------------------------
    snapshot_dict = snapshot.to_dict()

    assert snapshot_dict["pipeline_step"] == "DECIDE"
    assert snapshot_dict["action"] == "NONE"
    assert snapshot_dict["metadata"]["phase"] == 7

    # -------------------------
    # 4. 결과 jsonl 파일 저장
    # -------------------------
    out_dir: Path = observer_data_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / "observer_test.jsonl"

    with out_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot_dict, ensure_ascii=False) + "\n")

    # -------------------------
    # 5. 파일 생성 검증
    # -------------------------
    assert out_file.exists()
    assert out_file.is_file()

    # 마지막 줄이 정상 JSON인지 확인
    with out_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()
        last = json.loads(lines[-1])

    assert last["decision_id"] == snapshot_dict["decision_id"]
