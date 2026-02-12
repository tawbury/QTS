"""
이벤트 시스템 설정.

근거: docs/arch/sub/17_Event_Priority_Architecture.md §4, §5
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.event.contracts import EventPriority, OverflowPolicy


@dataclass(frozen=True)
class QueueConfig:
    """큐 설정."""

    priority: EventPriority
    capacity: int
    overflow_policy: OverflowPolicy
    batch_size: int = 1
    batch_timeout_ms: int = 0
    sample_rate: float = 1.0  # P3 SAMPLE 정책용


# 기본 큐 설정 (§4.1)
DEFAULT_QUEUE_CONFIGS: dict[EventPriority, QueueConfig] = {
    EventPriority.P0_CRITICAL: QueueConfig(
        priority=EventPriority.P0_CRITICAL,
        capacity=100,
        overflow_policy=OverflowPolicy.BLOCK,
    ),
    EventPriority.P1_HIGH: QueueConfig(
        priority=EventPriority.P1_HIGH,
        capacity=10_000,
        overflow_policy=OverflowPolicy.DROP_OLDEST,
        batch_size=100,
        batch_timeout_ms=10,
    ),
    EventPriority.P2_MEDIUM: QueueConfig(
        priority=EventPriority.P2_MEDIUM,
        capacity=1_000,
        overflow_policy=OverflowPolicy.COLLAPSE,
        batch_size=50,
        batch_timeout_ms=100,
    ),
    EventPriority.P3_LOW: QueueConfig(
        priority=EventPriority.P3_LOW,
        capacity=50_000,
        overflow_policy=OverflowPolicy.SAMPLE,
        batch_size=100,
        batch_timeout_ms=1_000,
        sample_rate=0.1,
    ),
}


@dataclass(frozen=True)
class BackpressureThreshold:
    """백프레셔 임계치."""

    warning: float
    critical: float


# 백프레셔 설정 (§5.3)
DEFAULT_BACKPRESSURE: dict[EventPriority, BackpressureThreshold] = {
    EventPriority.P1_HIGH: BackpressureThreshold(warning=0.70, critical=0.90),
    EventPriority.P2_MEDIUM: BackpressureThreshold(warning=0.80, critical=0.95),
}


@dataclass(frozen=True)
class QueueAlert:
    """큐 깊이 알림 임계치."""

    warning: int
    critical: int


# 큐 모니터링 알림 (§8.1)
DEFAULT_QUEUE_ALERTS: dict[EventPriority, QueueAlert] = {
    EventPriority.P0_CRITICAL: QueueAlert(warning=50, critical=80),
    EventPriority.P1_HIGH: QueueAlert(warning=7_000, critical=9_000),
    EventPriority.P2_MEDIUM: QueueAlert(warning=800, critical=950),
}

MONITORING_CHECK_INTERVAL_MS = 100


@dataclass
class EventConfig:
    """이벤트 시스템 전체 설정."""

    queue_configs: dict[EventPriority, QueueConfig] = field(
        default_factory=lambda: dict(DEFAULT_QUEUE_CONFIGS)
    )
    backpressure: dict[EventPriority, BackpressureThreshold] = field(
        default_factory=lambda: dict(DEFAULT_BACKPRESSURE)
    )
    queue_alerts: dict[EventPriority, QueueAlert] = field(
        default_factory=lambda: dict(DEFAULT_QUEUE_ALERTS)
    )
    monitoring_interval_ms: int = MONITORING_CHECK_INTERVAL_MS
