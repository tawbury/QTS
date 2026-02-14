from dataclasses import dataclass
from typing import Any, Dict

from src.provider.models.response import ExecutionResponse
from src.pipeline.loop.loop import ExecutionLoop
from src.pipeline.loop.controller import ExecutionLoopController
from src.pipeline.loop.policies.stop_policy import MaxIterationsStopPolicy
from src.risk.noop_risk_gate import NoopRiskGate


@dataclass(frozen=True)
class FakeRouteResult:
    ops_payload: Dict[str, Any]
    response: ExecutionResponse


class FakeExecutionRoute:
    def run_once(self, ops_payload: Dict[str, Any]) -> FakeRouteResult:
        accepted = bool(ops_payload.get("accepted", True))
        resp = ExecutionResponse(intent_id=str(ops_payload.get("intent_id", "x")), accepted=accepted, broker="FAKE", message="ok")
        return FakeRouteResult(ops_payload=ops_payload, response=resp)


def test_phase4_loop_runs_to_completion():
    def payload_source(i: int) -> Dict[str, Any]:
        return {"intent_id": f"i{i}", "accepted": True}

    controller = ExecutionLoopController(
        payload_source=payload_source,
        route=FakeExecutionRoute(),   # Phase 3 route로 나중에 교체
        risk_gate=NoopRiskGate(),
    )

    loop = ExecutionLoop(controller, MaxIterationsStopPolicy(max_iterations=3))
    report = loop.run()

    assert len(report.results) == 3
    assert controller.state_machine.state.value == "TERMINAL"
