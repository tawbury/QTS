from __future__ import annotations

from runtime.execution.brokers.noop_broker import NoopBroker
from runtime.pipeline.execution_route import ExecutionRoute


def test_phase1_execution_route_with_noop_broker():
    """
    Phase 1 Gate A:
    - ops payload → ExecutionIntent → NoopBroker
    - 실행이 구조적으로 거부됨을 증명
    """

    # GIVEN: ops decision output (black-box payload)
    ops_payload = {
        "symbol": "AAPL",
        "side": "BUY",
        "quantity": 10,
        "confidence": 0.92,          # ops 전용 필드 (QTS 무관)
        "strategy": "mean_revert",   # ops 전용 필드
    }

    broker = NoopBroker()
    route = ExecutionRoute(broker=broker)

    # WHEN: run execution route once
    result = route.run_once(ops_payload)

    # THEN: broker explicitly rejects execution
    response = result.response

    assert response.broker == "noop-broker"
    assert response.accepted is False
    assert "disabled" in response.message.lower()

    # AND: ops payload is preserved (normalized)
    assert result.ops_payload["symbol"] == "AAPL"
    assert result.ops_payload["side"] == "BUY"
    assert result.ops_payload["quantity"] == 10
