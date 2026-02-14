from __future__ import annotations

from src.pipeline.execution_route import ExecutionRoute
from src.provider.brokers.noop_broker import NoopBroker
from src.provider.models.response import ExecutionResponse


def test_phase3_execution_route_intent_flow():
    """
    Phase 3 Gate D test.

    Verifies:
    - ExecutionRoute accepts ops payload
    - Intent transformation succeeds
    - BrokerEngine(NoopBroker) is invoked
    - A valid ExecutionResponse is returned
    """

    broker = NoopBroker()
    route = ExecutionRoute(broker=broker)

    ops_payload = {
        "symbol": "005930",
        "side": "BUY",
        "qty": 1,
        "order_type": "MARKET",
    }

    result = route.run_once(ops_payload)

    # ExecutionResponse contract validation
    assert isinstance(result.response, ExecutionResponse)

    # Phase 1/3 noop broker always rejects execution by design
    assert result.response.accepted is False
    assert result.response.broker == "noop-broker"

    # Ops payload normalization preserved
    assert result.ops_payload["symbol"] == "005930"
