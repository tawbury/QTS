from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Protocol

from runtime.pipeline.execution_route import ExecutionRoute, ExecutionRouteResult
from runtime.execution_state.transition import OrderStateMachine
from runtime.risk.interfaces.risk_gate import RiskGate, RiskDecision


class OpsPayloadSource(Protocol):
    def __call__(self, iteration: int) -> Dict[str, Any]: ...


@dataclass
class LoopIterationResult:
    iteration: int
    risk_before_intent: RiskDecision
    risk_before_route: RiskDecision
    risk_after_response: RiskDecision
    state_prev: str
    state_next: str
    route_result: Optional[ExecutionRouteResult] = None
    blocked: bool = False


class ExecutionLoopController:
    """
    Phase 4 Controller:
    - ops_payload 생성/획득
    - Risk 훅 3지점
    - Phase 3 ExecutionRoute.run_once 호출(수정 금지)
    - ExecutionResponse를 State로 전이
    """

    def __init__(
        self,
        payload_source: OpsPayloadSource,
        route: ExecutionRoute,
        risk_gate: RiskGate,
        state_machine: Optional[OrderStateMachine] = None,
    ) -> None:
        self._payload_source = payload_source
        self._route = route
        self._risk_gate = risk_gate
        self._sm = state_machine or OrderStateMachine()

    @property
    def state_machine(self) -> OrderStateMachine:
        return self._sm

    def run_once(self, iteration: int) -> LoopIterationResult:
        ops_payload = self._payload_source(iteration)

        # Intent 생성 직전 훅(실제 생성은 route 내부 어댑터가 수행)
        r1 = self._risk_gate.before_intent(ops_payload)
        if not r1.allowed:
            return LoopIterationResult(
                iteration=iteration,
                risk_before_intent=r1,
                risk_before_route=r1,
                risk_after_response=r1,
                state_prev=self._sm.state.value,
                state_next=self._sm.state.value,
                blocked=True,
            )

        # route 호출 직전 훅
        r2 = self._risk_gate.before_route(ops_payload)
        if not r2.allowed:
            return LoopIterationResult(
                iteration=iteration,
                risk_before_intent=r1,
                risk_before_route=r2,
                risk_after_response=r2,
                state_prev=self._sm.state.value,
                state_next=self._sm.state.value,
                blocked=True,
            )

        # State: submitted (run_once를 제출 이벤트로 간주)
        prev_state = self._sm.state
        self._sm.on_submitted()

        # Phase 3 Route 호출
        result = self._route.run_once(ops_payload)

        # response 수신 직후 훅
        r3 = self._risk_gate.after_response(ops_payload)

        # State: accepted/rejected -> terminal
        self._sm.on_response(result.response)

        return LoopIterationResult(
            iteration=iteration,
            risk_before_intent=r1,
            risk_before_route=r2,
            risk_after_response=r3,
            state_prev=prev_state.value,
            state_next=self._sm.state.value,
            route_result=result,
            blocked=False,
        )
