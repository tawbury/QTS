# Ops Layer — 진입점·Wiring 요약 (Phase 9)

**목적:** Backup/Maintenance/Retention과 스케줄러/트리거/알림 경로를 한곳에 정리한다.  
**SSOT:** [09_Ops_Automation_Architecture.md](../../docs/arch/09_Ops_Automation_Architecture.md), [Phase_09 task](../../docs/tasks/phases/Phase_09_Ops_Automation/task.md)

---

## 1. 스케줄러·Health·Alerts (automation)

| 컴포넌트 | 진입점 | 비고 |
|----------|--------|------|
| 스케줄러 | `ops.automation.scheduler.MinimalScheduler` | `add_target(name, interval_ms, fn, error_backoff_ms, max_consecutive_errors)`, `run()`, `stop()`. 대상: TARGET_PIPELINE, TARGET_BROKER_HEARTBEAT, TARGET_DASHBOARD_UPDATE, TARGET_BACKUP_MAINTENANCE(콜러블 주입). 런타임 직접 import 없음 |
| Health | `ops.automation.health.HealthMonitor`, `run_checks()` | CHECK_GOOGLE_SHEETS, CHECK_REPOSITORY_HEALTH, CHECK_BROKER_HEARTBEAT, CHECK_ETEDA_LOOP_LATENCY(콜러블 주입). 치명적 실패 시 `alert_channel.send_critical()` |
| Alerts | `ops.automation.alerts.AlertChannel`, `LogOnlyAlertChannel` | `send_critical(message)`, `send_warning(message)` |

상세: [src/ops/automation/README.md](automation/README.md), [Ops_최소_구현_범위.md](../../docs/tasks/phases/Phase_09_Ops_Automation/Ops_최소_구현_범위.md)

---

## 2. Backup

| 컴포넌트 | 진입점 | 비고 |
|----------|--------|------|
| BackupManager | `ops.backup.manager.BackupManager(source_root, backup_root)` | tar.gz 아카이브(기본) 또는 Strategy 주입. `run()` → BackupManifest, `run_with_result()` → BackupResult |
| Backup 전략 | `ops.backup.strategy`: `ArchiveBackupStrategy`, `FileBackupStrategy`, `build_backup_plan` | coordinator 경로는 `ops.maintenance.backup.runner`에서 build_backup_plan, run_backup 사용(내부적으로 strategy 사용) |

---

## 3. Maintenance — 두 가지 진입 경로

| 경로 | 진입점 | 용도 |
|------|--------|------|
| **maintenance_runner** | `ops.runtime.maintenance_runner.run_maintenance_automation(dataset_root, backup_root, policy: DataRetentionPolicy)` | Observer 산출물 기준: 스캔 → 만료 후보 → BackupManager로 백업 → 성공 시에만 RetentionCleaner로 삭제. backup 실패 시 삭제 0 |
| **coordinator** | `ops.maintenance.coordinator.run_maintenance(data_root, backup_root, policy: FileRetentionPolicy, include_backup_globs)` | 파일 시스템 기준: build_backup_plan → run_backup(ops.maintenance.backup.runner) → scan_expired → execute_cleanup(backup_success). backup 먼저, 성공 시에만 cleanup |

공통 원칙: **backup 먼저, backup 성공 시에만 retention/cleanup 수행.** backup 실패 시 삭제는 절대 수행하지 않음.

---

## 4. Retention

| 컴포넌트 | 진입점 | 비고 |
|----------|--------|------|
| DataRetentionPolicy | `ops.retention.policy.DataRetentionPolicy` | raw_snapshot_days, pattern_record_days, decision_snapshot_days. maintenance_runner·DatasetScanner/RetentionCleaner에서 사용 |
| FileRetentionPolicy | `ops.retention.policy.FileRetentionPolicy` | coordinator·maintenance.retention.scanner에서 사용 |
| DatasetScanner / RetentionCleaner | `ops.retention.scanner.DatasetScanner`, `ops.retention.cleaner.RetentionCleaner` | maintenance_runner 경로에서 사용. Observer 산출물 경로·파일명 키워드 매핑 |

상세: [src/ops/retention/README.md](retention/README.md)

---

## 5. 운영 체크

백업/스케줄/알림 실패 시 점검·복구: [백업_스케줄_알림_운영_체크.md](../../docs/tasks/phases/Phase_09_Ops_Automation/백업_스케줄_알림_운영_체크.md)
