"""
이벤트 데이터 계약.

근거: docs/arch/sub/17_Event_Priority_Architecture.md §2, §3
- P0~P3 4단계 이벤트 우선순위
- EventType → Priority 매핑
- 오버플로우 정책, 성능 저하 레벨
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Optional


class EventPriority(IntEnum):
    """이벤트 우선순위 레벨. 숫자가 낮을수록 높은 우선순위."""

    P0_CRITICAL = 0  # Execution & Fill (<10ms)
    P1_HIGH = 1  # Market Data (<50ms)
    P2_MEDIUM = 2  # Strategy (<500ms)
    P3_LOW = 3  # UI & Logging (best-effort)


class EventType(str, Enum):
    """이벤트 타입 정의."""

    # P0: Execution & Fill
    FILL_CONFIRMED = "FILL_CONFIRMED"
    FILL_PARTIAL = "FILL_PARTIAL"
    ORDER_REJECTED = "ORDER_REJECTED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    POSITION_UPDATE = "POSITION_UPDATE"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    BROKER_DISCONNECT = "BROKER_DISCONNECT"

    # P1: Market Data
    PRICE_TICK = "PRICE_TICK"
    ORDERBOOK_UPDATE = "ORDERBOOK_UPDATE"
    VOLUME_UPDATE = "VOLUME_UPDATE"
    INDEX_UPDATE = "INDEX_UPDATE"
    VIX_UPDATE = "VIX_UPDATE"

    # P2: Strategy
    ETEDA_CYCLE_START = "ETEDA_CYCLE_START"
    STRATEGY_EVALUATE = "STRATEGY_EVALUATE"
    RISK_EVALUATE = "RISK_EVALUATE"
    PORTFOLIO_EVALUATE = "PORTFOLIO_EVALUATE"
    INDICATOR_UPDATE = "INDICATOR_UPDATE"
    SIGNAL_GENERATED = "SIGNAL_GENERATED"

    # P3: UI & Logging
    DASHBOARD_UPDATE = "DASHBOARD_UPDATE"
    LOG_WRITE = "LOG_WRITE"
    REPORT_GENERATE = "REPORT_GENERATE"
    NOTIFICATION_SEND = "NOTIFICATION_SEND"
    METRIC_RECORD = "METRIC_RECORD"


# EventType → Priority 매핑 (§3.1)
EVENT_PRIORITY_MAP: dict[EventType, EventPriority] = {
    # P0
    EventType.FILL_CONFIRMED: EventPriority.P0_CRITICAL,
    EventType.FILL_PARTIAL: EventPriority.P0_CRITICAL,
    EventType.ORDER_REJECTED: EventPriority.P0_CRITICAL,
    EventType.ORDER_CANCELLED: EventPriority.P0_CRITICAL,
    EventType.POSITION_UPDATE: EventPriority.P0_CRITICAL,
    EventType.EMERGENCY_STOP: EventPriority.P0_CRITICAL,
    EventType.BROKER_DISCONNECT: EventPriority.P0_CRITICAL,
    # P1
    EventType.PRICE_TICK: EventPriority.P1_HIGH,
    EventType.ORDERBOOK_UPDATE: EventPriority.P1_HIGH,
    EventType.VOLUME_UPDATE: EventPriority.P1_HIGH,
    EventType.INDEX_UPDATE: EventPriority.P1_HIGH,
    EventType.VIX_UPDATE: EventPriority.P1_HIGH,
    # P2
    EventType.ETEDA_CYCLE_START: EventPriority.P2_MEDIUM,
    EventType.STRATEGY_EVALUATE: EventPriority.P2_MEDIUM,
    EventType.RISK_EVALUATE: EventPriority.P2_MEDIUM,
    EventType.PORTFOLIO_EVALUATE: EventPriority.P2_MEDIUM,
    EventType.INDICATOR_UPDATE: EventPriority.P2_MEDIUM,
    EventType.SIGNAL_GENERATED: EventPriority.P2_MEDIUM,
    # P3
    EventType.DASHBOARD_UPDATE: EventPriority.P3_LOW,
    EventType.LOG_WRITE: EventPriority.P3_LOW,
    EventType.REPORT_GENERATE: EventPriority.P3_LOW,
    EventType.NOTIFICATION_SEND: EventPriority.P3_LOW,
    EventType.METRIC_RECORD: EventPriority.P3_LOW,
}


def priority_for(event_type: EventType) -> EventPriority:
    """EventType에 대한 우선순위 반환."""
    return EVENT_PRIORITY_MAP[event_type]


@dataclass(frozen=True)
class Event:
    """이벤트 데이터 계약 (§2.1)."""

    event_type: EventType
    priority: EventPriority
    source: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    requires_ack: bool = False
    max_process_time_ms: int = 0
    can_batch: bool = False
    can_collapse: bool = False
    can_drop: bool = False


def create_event(
    event_type: EventType,
    source: str = "",
    payload: Optional[dict[str, Any]] = None,
    **kwargs: Any,
) -> Event:
    """편의 팩토리: EventType으로부터 Event 생성 (priority 자동 설정)."""
    priority = priority_for(event_type)
    defaults: dict[str, Any] = {}
    if priority == EventPriority.P0_CRITICAL:
        defaults.update(requires_ack=True, max_process_time_ms=10)
    elif priority == EventPriority.P1_HIGH:
        defaults.update(can_batch=True)
    elif priority == EventPriority.P2_MEDIUM:
        defaults.update(can_collapse=True)
    elif priority == EventPriority.P3_LOW:
        defaults.update(can_drop=True)
    defaults.update(kwargs)
    return Event(
        event_type=event_type,
        priority=priority,
        source=source,
        payload=payload or {},
        **defaults,
    )


class OverflowPolicy(str, Enum):
    """큐 오버플로우 정책 (§4.2)."""

    BLOCK = "BLOCK"  # P0: 프로듀서 대기
    DROP_OLDEST = "DROP_OLDEST"  # P1: 가장 오래된 것 버림
    COLLAPSE = "COLLAPSE"  # P2: 같은 타입 병합
    SAMPLE = "SAMPLE"  # P3: 샘플링 (10%)


class DegradationLevel(str, Enum):
    """성능 저하 레벨 (§7.1)."""

    NORMAL = "NORMAL"  # 모든 우선순위 처리
    P3_PAUSED = "P3_PAUSED"  # P3 일시 중단
    P2_P3_PAUSED = "P2_P3_PAUSED"  # P2+P3 일시 중단
    CRITICAL_ONLY = "CRITICAL_ONLY"  # P0만 처리
