from __future__ import annotations

from runtime.strategy.simple_strategy import SimpleStrategy
from runtime.strategy.interfaces.strategy import MarketContext, ExecutionContext


def test_simple_strategy_generates_buy_intent_when_price_below_threshold_and_no_position() -> None:
    strategy = SimpleStrategy(buy_below=100.0, sell_above=110.0, qty=2)

    market = MarketContext(symbol="TEST", price=99.0)
    execution = ExecutionContext(position_qty=0, cash=1_000_000.0)

    intents = list(strategy.generate_intents(market=market, execution=execution))

    assert len(intents) == 1
    intent = intents[0]
    assert intent.symbol == "TEST"
    assert intent.side == "BUY"
    assert intent.qty == 2
    assert "simple_buy_below" in intent.reason


def test_simple_strategy_generates_sell_intent_when_price_above_threshold_and_has_position() -> None:
    strategy = SimpleStrategy(buy_below=100.0, sell_above=110.0, qty=1)

    market = MarketContext(symbol="TEST", price=111.0)
    execution = ExecutionContext(position_qty=5, cash=0.0)

    intents = list(strategy.generate_intents(market=market, execution=execution))

    assert len(intents) == 1
    intent = intents[0]
    assert intent.symbol == "TEST"
    assert intent.side == "SELL"
    # Phase 5: SELL은 보유 수량 전량 청산(샘플 구현 기준)
    assert intent.qty == 5
    assert "simple_sell_above" in intent.reason


def test_simple_strategy_generates_no_intents_when_conditions_not_met() -> None:
    strategy = SimpleStrategy(buy_below=100.0, sell_above=110.0, qty=1)

    # 가격이 buy_below보다 높고, 포지션도 없으면 아무것도 하지 않음
    market = MarketContext(symbol="TEST", price=105.0)
    execution = ExecutionContext(position_qty=0, cash=1_000.0)

    intents = list(strategy.generate_intents(market=market, execution=execution))

    assert intents == []
