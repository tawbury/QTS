from __future__ import annotations

from runtime.execution.brokers.mock_broker import MockBroker
from runtime.pipeline.execution_route import ExecutionRoute


def test_phase1_execution_route_with_mock_broker_accept():
    """
    Phase 1 Gate A:
    - ops payload → ExecutionIntent → MockBroker
    - 정상 수량이면 구조적으로 '수용'됨을 증명
    """

    ops_payload = {
        "ticker": "MSFT",   # symbol 대신 ticker 사용
        "side": "SELL",
        "qty": 5,           # quantity 대신 qty 사용
    }

    broker = MockBroker()
    route = ExecutionRoute(broker=broker)

    result = route.run_once(ops_payload)
    response = result.response

    assert response.broker == "mock-broker"
    assert response.accepted is True
    assert response.intent_id is not None


def test_phase1_execution_route_with_mock_broker_reject():
    """
    Phase 1 safety:
    - 수량 <= 0 인 경우 NOOP 강등
    - MockBroker라도 거부됨
    """

    ops_payload = {
        "symbol": "TSLA",
        "side": "BUY",
        "quantity": 0,
    }

    broker = MockBroker()
    route = ExecutionRoute(broker=broker)

    result = route.run_once(ops_payload)
    response = result.response

    assert response.broker == "mock-broker"
    assert response.accepted is False
