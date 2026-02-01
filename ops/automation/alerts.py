"""
알림 채널 최소 구현 (Phase 9 — Monitoring & Alerts).

- AlertChannel 프로토콜: send_critical, send_warning
- 최소 구현: LogOnlyAlertChannel (로깅만; Slack/Telegram은 추후 확장)
- 근거: docs/arch/09_Ops_Automation_Architecture.md, 07_FailSafe_Architecture.md
"""

from __future__ import annotations

import logging
from typing import Protocol

_log = logging.getLogger("ops.automation.alerts")


class AlertChannel(Protocol):
    """알림 채널 최소 규격. 구현체: LogOnlyAlertChannel, Slack/Telegram 등(추후)."""

    def send_critical(self, message: str) -> None:
        """치명적 장애 알림 — 운영자에게 전달."""
        ...

    def send_warning(self, message: str) -> None:
        """경고 알림."""
        ...


class LogOnlyAlertChannel:
    """
    로깅만 수행하는 알림 채널 (최소 구현).

    - send_critical → logging.critical
    - send_warning → logging.warning
    - 민감정보는 로그에 포함하지 않음(호출부 책임).
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._log = logger or _log

    def send_critical(self, message: str) -> None:
        self._log.critical("ALERT CRITICAL: %s", message)

    def send_warning(self, message: str) -> None:
        self._log.warning("ALERT WARNING: %s", message)
