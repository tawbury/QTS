from runtime.execution.brokers.live_broker import LiveBroker
from runtime.execution.models.response import ExecutionResponse


class _DummyIntent:
    """ExecutionIntent 계약 호환: intent_id 필수 (LiveBroker.submit_intent)."""
    id = "intent-test-1"
    intent_id = "intent-test-1"


class _FailingAdapter:
    def submit_intent(self, intent):
        return ExecutionResponse(
            intent_id=intent.id,
            accepted=False,
            broker="test-broker",
            message="failure",
        )


class _SuccessAdapter:
    def submit_intent(self, intent):
        return ExecutionResponse(
            intent_id=intent.id,
            accepted=True,
            broker="test-broker",
            message="success",
        )


def _intent():
    return _DummyIntent()


def test_failsafe_blocks_after_consecutive_failures():
    broker = LiveBroker(
        adapter=_FailingAdapter(),
        max_consecutive_failures=2,
    )

    r1 = broker.submit_intent(_intent())
    r2 = broker.submit_intent(_intent())
    r3 = broker.submit_intent(_intent())

    assert r1.accepted is False
    assert r2.accepted is False
    assert r3.accepted is False
    assert r3.broker == "failsafe"


def test_failsafe_resets_on_success():
    broker = LiveBroker(
        adapter=_FailingAdapter(),
        max_consecutive_failures=2,
    )

    r1 = broker.submit_intent(_intent())
    assert r1.accepted is False

    broker._adapter = _SuccessAdapter()
    r2 = broker.submit_intent(_intent())
    assert r2.accepted is True

    broker._adapter = _FailingAdapter()
    r3 = broker.submit_intent(_intent())
    assert r3.accepted is False
    assert r3.broker != "failsafe"
