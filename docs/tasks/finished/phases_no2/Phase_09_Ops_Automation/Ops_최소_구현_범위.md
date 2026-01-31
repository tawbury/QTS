# Phase 9 — Ops 스케줄링(automation) 최소 구현 범위

**목적:** Ops 자동화(스케줄러/트리거/알림)의 "최소 구현 범위"를 문서로 확정한다.  
**SSOT:** [09_Ops_Automation_Architecture.md](../../../arch/09_Ops_Automation_Architecture.md), [src/ops/automation/README.md](../../../src/ops/automation/README.md)

---

## 1. 최소 구현 범위 (확정)

| 영역 | 범위 | 진입점 | 비고 |
|------|------|--------|------|
| **스케줄러** | Interval 기반 + 대상별 실패 백오프 | `ops.automation.scheduler.MinimalScheduler` | `add_target(name, interval_ms, fn, ...)`, `run()`, `stop()`. 대상은 콜러블 주입 |
| **스케줄 대상** | Pipeline, Broker heartbeat, Dashboard, Backup/Maintenance | 상수: `TARGET_PIPELINE`, `TARGET_BROKER_HEARTBEAT`, `TARGET_DASHBOARD_UPDATE`, `TARGET_BACKUP_MAINTENANCE` | 런타임 직접 import 없음 |
| **Health** | 체크 항목 콜러블 주입 + 결과 수집 | `ops.automation.health.HealthMonitor`, `run_checks()` | `CHECK_GOOGLE_SHEETS`, `CHECK_REPOSITORY_HEALTH`, `CHECK_BROKER_HEARTBEAT`, `CHECK_ETEDA_LOOP_LATENCY` |
| **Alerts** | 치명적 장애 시 알림 채널 호출 | `ops.automation.alerts.AlertChannel`, `LogOnlyAlertChannel` | `send_critical(message)`, `send_warning(message)`. Slack/Telegram은 추후 확장 |

---

## 2. 경계 규칙

- **스케줄링 로직**은 `src/ops/automation/` 에만 존재.
- **런타임(ETEDA runner, broker, dashboard)** 은 콜러블로 주입; 스케줄러/HealthMonitor가 runtime 모듈을 직접 import 하지 않음.
- **실패 시:** 대상 `fn()` 예외 → 해당 대상만 `consecutive_errors` 증가, `max_consecutive_errors` 초과 시 해당 대상 스킵(루프는 계속). Health 실패 시 `alert_channel.send_critical()` 호출.

---

## 3. 확장 시 유의사항

- 새 스케줄 대상: `add_target` 으로 콜러블만 등록.
- 새 Health 항목: `add_check` 으로 콜러블만 등록.
- 알림 채널 확장: `AlertChannel` 프로토콜 구현체 추가(Slack/Telegram 등).

이 문서는 Phase 9 완료 조건(문서 SSOT 반영) 충족을 위한 "최소 구현 범위" 확정 문서이다.
