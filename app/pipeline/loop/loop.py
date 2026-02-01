from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .controller import ExecutionLoopController, LoopIterationResult
from .policies.stop_policy import StopPolicy


@dataclass
class ExecutionLoopReport:
    results: List[LoopIterationResult]


class ExecutionLoop:
    def __init__(self, controller: ExecutionLoopController, stop_policy: StopPolicy) -> None:
        self._controller = controller
        self._stop = stop_policy

    def run(self) -> ExecutionLoopReport:
        out: List[LoopIterationResult] = []
        i = 0
        while True:
            if self._stop.should_stop(i):
                break
            out.append(self._controller.run_once(i))
            i += 1
        return ExecutionLoopReport(results=out)
