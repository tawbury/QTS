from __future__ import annotations

from dataclasses import dataclass

from src.provider.models.response import ExecutionResponse
from .order_state import OrderState


@dataclass(frozen=True)
class Transition:
    prev: OrderState
    next: OrderState
    reason: str


class OrderStateMachine:
    """
    Phase 4 최소 State:
    - run_once 호출 단위로 SUBMITTED를 찍고
    - accepted에 따라 ACCEPTED/REJECTED
    - 즉시 TERMINAL까지 밀어 넣어도 됨(최소 기반선)
    """

    def __init__(self) -> None:
        self._state = OrderState.CREATED

    @property
    def state(self) -> OrderState:
        return self._state

    def on_submitted(self) -> Transition:
        prev = self._state
        self._state = OrderState.SUBMITTED
        return Transition(prev=prev, next=self._state, reason="submitted")

    def on_response(self, resp: ExecutionResponse) -> list[Transition]:
        transitions: list[Transition] = []
        prev = self._state

        if resp.accepted:
            self._state = OrderState.ACCEPTED
            transitions.append(Transition(prev=prev, next=self._state, reason="accepted"))
        else:
            self._state = OrderState.REJECTED
            transitions.append(Transition(prev=prev, next=self._state, reason="rejected"))

        prev2 = self._state
        self._state = OrderState.TERMINAL
        transitions.append(Transition(prev=prev2, next=self._state, reason="terminal"))

        return transitions
