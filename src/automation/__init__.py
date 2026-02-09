"""
Ops Automation (Phase 9).

- MinimalScheduler: interval-based scheduler with failure backoff.
- Schedule targets: Pipeline, Broker heartbeat, Dashboard update, Backup/Maintenance
  (inject as callables; see scheduler.TARGET_*).
- HealthMonitor: health checks (sheets, repository, broker, eteda latency) + alert on failure.
- AlertChannel: send_critical/send_warning; LogOnlyAlertChannel (minimal).
"""

from src.automation.scheduler import (
    TARGET_BACKUP_MAINTENANCE,
    TARGET_BROKER_HEARTBEAT,
    TARGET_DASHBOARD_UPDATE,
    TARGET_PIPELINE,
    MinimalScheduler,
    ScheduleTarget,
)
from src.automation.health import (
    CHECK_BROKER_HEARTBEAT,
    CHECK_ETEDA_LOOP_LATENCY,
    CHECK_GOOGLE_SHEETS,
    CHECK_REPOSITORY_HEALTH,
    HealthCheckResult,
    HealthMonitor,
)
from src.automation.alerts import AlertChannel, LogOnlyAlertChannel

__all__ = [
    "AlertChannel",
    "HealthCheckResult",
    "HealthMonitor",
    "LogOnlyAlertChannel",
    "MinimalScheduler",
    "ScheduleTarget",
    "TARGET_BACKUP_MAINTENANCE",
    "TARGET_BROKER_HEARTBEAT",
    "TARGET_DASHBOARD_UPDATE",
    "TARGET_PIPELINE",
    "CHECK_GOOGLE_SHEETS",
    "CHECK_REPOSITORY_HEALTH",
    "CHECK_BROKER_HEARTBEAT",
    "CHECK_ETEDA_LOOP_LATENCY",
]
