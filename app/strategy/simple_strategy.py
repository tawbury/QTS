from __future__ import annotations

from typing import Sequence, List

from .interfaces.strategy import Strategy, MarketContext, ExecutionContext, Intent


class SimpleStrategy(Strategy):
    """
    Phase 5용 최소 전략 예시:
    - 포지션이 없고(price가 임계 이하)면 BUY intent 1개
    - 포지션이 있고(price가 임계 이상)면 SELL intent 1개
    """

    def __init__(self, buy_below: float = 100.0, sell_above: float = 110.0, qty: int = 1):
        self.buy_below = buy_below
        self.sell_above = sell_above
        self.qty = qty

    def generate_intents(
        self,
        market: MarketContext,
        execution: ExecutionContext,
    ) -> Sequence[Intent]:
        intents: List[Intent] = []

        if execution.position_qty <= 0 and market.price <= self.buy_below:
            intents.append(Intent(symbol=market.symbol, side="BUY", qty=self.qty, reason="simple_buy_below"))
        elif execution.position_qty > 0 and market.price >= self.sell_above:
            intents.append(Intent(symbol=market.symbol, side="SELL", qty=execution.position_qty, reason="simple_sell_above"))

        return intents
