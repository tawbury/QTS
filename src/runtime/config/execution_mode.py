from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExecutionMode(str, Enum):
    PAPER = "PAPER"
    LIVE = "LIVE"


@dataclass(frozen=True)
class LiveGateDecision:
    mode: ExecutionMode
    live_allowed: bool
    reason: str


def decide_execution_mode(
    sheet_execution_mode: str | None,
    sheet_live_enabled: str | None,
    env_live_ack: str | None,
    *,
    required_ack: str = "I_UNDERSTAND_LIVE_TRADING",
) -> LiveGateDecision:
    """
    Decide whether LIVE execution is allowed.

    Rules (AND for LIVE):
    1) sheet_execution_mode == "LIVE"
    2) sheet_live_enabled truthy ("1", "true", "yes", "on")
    3) env_live_ack matches required_ack exactly

    Default: PAPER
    """
    mode_raw = (sheet_execution_mode or "").strip().upper()
    enabled_raw = (sheet_live_enabled or "").strip().lower()

    if mode_raw != ExecutionMode.LIVE.value:
        return LiveGateDecision(
            mode=ExecutionMode.PAPER,
            live_allowed=False,
            reason="mode_not_live",
        )

    truthy = {"1", "true", "yes", "on", "y"}
    if enabled_raw not in truthy:
        return LiveGateDecision(
            mode=ExecutionMode.LIVE,
            live_allowed=False,
            reason="live_enabled_false",
        )

    if (env_live_ack or "").strip() != required_ack:
        return LiveGateDecision(
            mode=ExecutionMode.LIVE,
            live_allowed=False,
            reason="ack_missing_or_invalid",
        )

    return LiveGateDecision(
        mode=ExecutionMode.LIVE,
        live_allowed=True,
        reason="live_allowed",
    )
