"""
Circuit Breaker 패턴.

근거: docs/arch/sub/19_Caching_Architecture.md §6.2
- CLOSED: 정상 동작
- OPEN: 장애 감지 (fallback)
- HALF_OPEN: 복구 시도
- 5회 연속 실패 → OPEN, 60초 후 HALF_OPEN
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit Breaker 상태."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreaker:
    """Circuit Breaker 구현."""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds

    state: CircuitState = field(default=CircuitState.CLOSED)
    failure_count: int = field(default=0)
    last_failure_at: datetime | None = field(default=None)
    _success_count_in_half_open: int = field(default=0)

    def can_execute(self) -> bool:
        """실행 가능 여부. OPEN 상태에서는 recovery_timeout 경과 시 HALF_OPEN."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.HALF_OPEN:
            return True

        # OPEN → recovery_timeout 경과 여부 확인
        if self.last_failure_at is not None:
            elapsed = (
                datetime.now(timezone.utc) - self.last_failure_at
            ).total_seconds()
            if elapsed >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self._success_count_in_half_open = 0
                logger.info("Circuit breaker: OPEN → HALF_OPEN")
                return True

        return False

    def record_success(self) -> None:
        """성공 기록."""
        if self.state == CircuitState.HALF_OPEN:
            self._success_count_in_half_open += 1
            # HALF_OPEN에서 1회 성공 → CLOSED
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_at = None
            logger.info("Circuit breaker: HALF_OPEN → CLOSED")
        elif self.state == CircuitState.CLOSED:
            # 연속 실패 카운터 리셋
            self.failure_count = 0

    def record_failure(self) -> None:
        """실패 기록."""
        self.failure_count += 1
        self.last_failure_at = datetime.now(timezone.utc)

        if self.state == CircuitState.HALF_OPEN:
            # HALF_OPEN에서 실패 → 즉시 OPEN
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker: HALF_OPEN → OPEN")
        elif (
            self.state == CircuitState.CLOSED
            and self.failure_count >= self.failure_threshold
        ):
            self.state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker: CLOSED → OPEN (failures=%d)",
                self.failure_count,
            )

    def reset(self) -> None:
        """수동 리셋."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_at = None
        self._success_count_in_half_open = 0
