from __future__ import annotations

import inspect
from dataclasses import MISSING, fields, is_dataclass

from src.decision_pipeline.contracts.order_decision import OrderDecision
from src.decision_pipeline.contracts.execution_hint import ExecutionHint
from src.decision_pipeline.execution_stub.execution_context import ExecutionContext
from src.decision_pipeline.execution_stub.virtual_executor import VirtualExecutor


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


def test_virtual_executor_reject_qty_nonpositive():
    executor = VirtualExecutor()
    ctx = ExecutionContext()

    order = build_obj(OrderDecision, action="BUY", symbol="AAPL", qty=0)
    hint = build_obj(ExecutionHint)

    res = executor.execute(order=order, hint=hint, context=ctx)

    assert res.status == "REJECTED"
    assert res.blocked_by in ("G_EXE_QTY_NONPOSITIVE", "G_EXE_SYMBOL_EMPTY")


def test_virtual_executor_reject_killswitch():
    executor = VirtualExecutor()
    ctx = ExecutionContext(kill_switch=True)

    order = build_obj(OrderDecision, action="BUY", symbol="AAPL", qty=1)
    hint = build_obj(ExecutionHint)

    res = executor.execute(order=order, hint=hint, context=ctx)

    assert res.status == "REJECTED"
    assert res.blocked_by == "G_EXE_KILLSWITCH_ON"
