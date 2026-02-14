from __future__ import annotations

import inspect
from dataclasses import MISSING, fields, is_dataclass

from src.decision_pipeline.contracts.order_decision import OrderDecision
from src.decision_pipeline.contracts.execution_hint import ExecutionHint
from src.decision_pipeline.execution_stub.execution_context import ExecutionContext
from src.decision_pipeline.execution_stub.sim_executor import SimExecutor


def build_obj(cls, **overrides):
    if is_dataclass(cls):
        kwargs = {}
        for f in fields(cls):
            if f.name in overrides:
                kwargs[f.name] = overrides[f.name]
                continue

            has_default = (
                f.default is not MISSING
                or f.default_factory is not MISSING  # type: ignore
            )
            if has_default:
                continue

            if f.type in (int, "int"):
                kwargs[f.name] = 1
            elif f.type in (float, "float"):
                kwargs[f.name] = 1.0
            elif f.type in (bool, "bool"):
                kwargs[f.name] = False
            else:
                kwargs[f.name] = "X"
        return cls(**kwargs)

    sig = inspect.signature(cls)
    kwargs = {}
    for name, p in sig.parameters.items():
        if name in overrides:
            kwargs[name] = overrides[name]
        elif p.default is inspect._empty:
            kwargs[name] = "X"
    return cls(**kwargs)


def test_sim_executor_partial_fill():
    executor = SimExecutor()

    # max_fill_qty 제한으로 PARTIAL 유도
    ctx = ExecutionContext(risk_limits={"max_fill_qty": 3})

    # ✅ ExecutionHint 확장 슬롯은 constraints
    hint = build_obj(ExecutionHint, constraints={"reference_price": 100.0})

    order = build_obj(OrderDecision, action="BUY", symbol="AAPL", qty=10)

    res = executor.execute(order=order, hint=hint, context=ctx)

    assert res.status == "ACCEPTED"
    assert res.executed is True

    sim = res.audit["simulation"]
    assert sim["result"] == "PARTIAL"
    assert sim["fill_qty"] == 3
    assert sim["requested_qty"] == 10
