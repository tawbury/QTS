from __future__ import annotations

from dataclasses import dataclass

from runtime.strategy.registry.strategy_registry import StrategyRegistry
from runtime.strategy.multiplexer.strategy_multiplexer import StrategyMultiplexer


@dataclass
class OkStrategy:
    strategy_id: str
    name: str
    enabled: bool = True

    def is_enabled(self) -> bool:
        return self.enabled

    def generate_intents(self, snapshot):
        return [("INTENT", self.strategy_id)]


@dataclass
class BadStrategy:
    strategy_id: str
    name: str
    enabled: bool = True

    def is_enabled(self) -> bool:
        return self.enabled

    def generate_intents(self, snapshot):
        raise RuntimeError("boom")


def test_multiplexer_isolates_strategy_failure():
    reg = StrategyRegistry()
    reg.register(OkStrategy("s1", "S1"))
    reg.register(BadStrategy("s2", "S2"))

    mux = StrategyMultiplexer(reg)
    out = mux.collect(snapshot={"x": 1})

    assert len(out) == 1
    assert out[0].strategy_id == "s1"
