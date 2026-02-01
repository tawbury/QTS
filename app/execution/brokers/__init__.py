"""
Broker engines and factory (Phase 8).

- LiveBroker: real execution with injected adapter; fail-safe on consecutive failures.
- NoopBroker: always rejects; structural block for non-live.
- MockBroker: tests only; never used in production path.

Production path MUST use create_broker_for_execution() so that MockBroker
is never selected. MockBroker is only for pytest / test code.
"""

from __future__ import annotations

from typing import Any

from app.execution.interfaces.broker import BrokerEngine
from app.execution.brokers.live_broker import LiveBroker
from app.execution.brokers.mock_broker import MockBroker
from app.execution.brokers.noop_broker import NoopBroker


def create_broker_for_execution(
    live_allowed: bool,
    adapter: Any = None,
    *,
    max_consecutive_failures: int = 3,
) -> BrokerEngine:
    """
    Create BrokerEngine for execution route (production-safe).

    Rules:
    - live_allowed and adapter provided → LiveBroker(adapter)
    - otherwise → NoopBroker (no real orders)

    MockBroker is never returned; use only in tests by direct instantiation.
    """
    if live_allowed and adapter is not None:
        return LiveBroker(adapter=adapter, max_consecutive_failures=max_consecutive_failures)
    return NoopBroker()


__all__ = [
    "BrokerEngine",
    "LiveBroker",
    "NoopBroker",
    "MockBroker",
    "create_broker_for_execution",
]
