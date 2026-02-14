from __future__ import annotations

from dataclasses import dataclass

from src.strategy.registry.strategy_registry import StrategyRegistry


@dataclass
class DummyStrategy:
    strategy_id: str
    name: str
    enabled: bool = True

    def is_enabled(self) -> bool:
        return self.enabled


def test_registry_register_unregister():
    reg = StrategyRegistry()
    s1 = DummyStrategy("s1", "S1")
    reg.register(s1)

    assert len(reg) == 1
    assert reg.get("s1") is s1

    reg.unregister("s1")
    assert len(reg) == 0


def test_registry_active_only():
    reg = StrategyRegistry()
    reg.register(DummyStrategy("s1", "S1", enabled=True))
    reg.register(DummyStrategy("s2", "S2", enabled=False))

    act = reg.active_strategies()
    assert [a.strategy_id for a in act] == ["s1"]
