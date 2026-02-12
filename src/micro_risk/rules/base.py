"""리스크 규칙 베이스 Protocol.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §2.4
"""
from __future__ import annotations

from typing import Optional, Protocol

from src.micro_risk.contracts import MarketData, MicroRiskAction, PositionShadow


class RiskRule(Protocol):
    """리스크 규칙 프로토콜."""

    def evaluate(
        self, shadow: PositionShadow, market_data: MarketData,
    ) -> Optional[MicroRiskAction]: ...
