"""
틱 데이터 분석.

근거: docs/arch/sub/20_Feedback_Loop_Architecture.md §2.1
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.feedback.contracts import TickRecord


def calculate_volatility(ticks: list[TickRecord]) -> float:
    """ATR 기반 변동성 계산."""
    if len(ticks) < 2:
        return 0.0
    prices = [float(t.price) for t in ticks]
    avg_price = sum(prices) / len(prices)
    if avg_price == 0:
        return 0.0
    return (max(prices) - min(prices)) / avg_price


def calculate_spread_bps(ticks: list[TickRecord]) -> float:
    """Bid-Ask Spread (bps) 계산."""
    bid_prices = [float(t.price) for t in ticks if t.side == "BID"]
    ask_prices = [float(t.price) for t in ticks if t.side == "ASK"]
    if not bid_prices or not ask_prices:
        return 0.0
    avg_bid = sum(bid_prices) / len(bid_prices)
    avg_ask = sum(ask_prices) / len(ask_prices)
    if avg_bid == 0:
        return 0.0
    return (avg_ask - avg_bid) / avg_bid * 10000


def calculate_depth(ticks: list[TickRecord], top_n: int = 5) -> int:
    """호가창 깊이 (상위 N단계 거래량 합)."""
    sorted_ticks = sorted(ticks, key=lambda t: t.volume, reverse=True)
    return sum(int(t.volume) for t in sorted_ticks[:top_n])
