"""
운영 상태 시스템 설정.

근거: docs/arch/sub/18_System_State_Promotion_Architecture.md §3.3, §4
"""
from __future__ import annotations

from dataclasses import dataclass

from src.state.contracts import OperatingState


@dataclass
class StateConfig:
    """운영 상태 시스템 설정."""

    default_state: OperatingState = OperatingState.BALANCED
    override_max_duration_days: int = 7
    cooldown_hours: int = 24
    confirmation_cycles: int = 2
    aggressive_min_duration_days: int = 7
    balanced_min_duration_days: int = 5
    defensive_min_duration_days: int = 3
