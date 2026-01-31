"""
Broker factory tests (Phase 8).

- create_broker_for_execution(live_allowed, adapter) returns LiveBroker or NoopBroker only.
- MockBroker is never returned by the factory (production-safe).
"""

from __future__ import annotations

from runtime.execution.brokers import (
    create_broker_for_execution,
    LiveBroker,
    MockBroker,
    NoopBroker,
)


def test_create_broker_live_allowed_with_adapter_returns_live_broker():
    class FakeAdapter:
        def submit_intent(self, intent):
            from runtime.execution.models.response import ExecutionResponse
            return ExecutionResponse(
                intent_id=intent.intent_id,
                accepted=True,
                broker="fake",
                message="ok",
            )

    broker = create_broker_for_execution(live_allowed=True, adapter=FakeAdapter())
    assert isinstance(broker, LiveBroker)
    assert not isinstance(broker, MockBroker)
    assert not isinstance(broker, NoopBroker)


def test_create_broker_live_not_allowed_returns_noop():
    class FakeAdapter:
        pass

    broker = create_broker_for_execution(live_allowed=False, adapter=FakeAdapter())
    assert isinstance(broker, NoopBroker)
    assert not isinstance(broker, MockBroker)


def test_create_broker_live_allowed_no_adapter_returns_noop():
    broker = create_broker_for_execution(live_allowed=True, adapter=None)
    assert isinstance(broker, NoopBroker)
    assert not isinstance(broker, MockBroker)


def test_create_broker_never_returns_mock_broker():
    for live in (True, False):
        for adapter in (None, object()):
            broker = create_broker_for_execution(live_allowed=live, adapter=adapter)
            assert not isinstance(broker, MockBroker), "Production factory must never return MockBroker"
