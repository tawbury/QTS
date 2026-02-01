from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConsecutiveFailurePolicy:
    max_failures: int = 3


class ConsecutiveFailureGuard:
    def __init__(self, policy: ConsecutiveFailurePolicy) -> None:
        self._policy = policy
        self._fails = 0
        self._blocked = False

    @property
    def blocked(self) -> bool:
        return self._blocked

    def on_success(self) -> None:
        self._fails = 0

    def on_failure(self) -> None:
        self._fails += 1
        if self._fails >= self._policy.max_failures:
            self._blocked = True
