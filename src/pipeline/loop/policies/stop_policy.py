from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class StopPolicy(Protocol):
    def should_stop(self, iteration: int) -> bool: ...


@dataclass(frozen=True)
class MaxIterationsStopPolicy:
    max_iterations: int

    def should_stop(self, iteration: int) -> bool:
        return iteration >= self.max_iterations
