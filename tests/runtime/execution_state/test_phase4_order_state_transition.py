from src.provider.state.transition import OrderStateMachine
from src.provider.models.response import ExecutionResponse


def test_phase4_order_state_minimal_accept():
    sm = OrderStateMachine()
    sm.on_submitted()

    resp = ExecutionResponse(intent_id="i1", accepted=True, broker="TEST", message="ok")
    sm.on_response(resp)

    assert sm.state.value == "TERMINAL"


def test_phase4_order_state_minimal_reject():
    sm = OrderStateMachine()
    sm.on_submitted()

    resp = ExecutionResponse(intent_id="i2", accepted=False, broker="TEST", message="no")
    sm.on_response(resp)

    assert sm.state.value == "TERMINAL"
