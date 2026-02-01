# ops/ — Ops Layer

Backup/Maintenance/Retention과 스케줄러/트리거/알림 경로를 한곳에 정리.  
**SSOT:** [09_Ops_Automation_Architecture.md](../docs/arch/09_Ops_Automation_Architecture.md)

---

## 1. 스케줄러·Health·Alerts (automation)

| 컴포넌트 | 진입점 | 비고 |
|----------|--------|------|
| 스케줄러 | `ops.automation.scheduler.MinimalScheduler` | `add_target()`, `run()`, `stop()`. 대상: TARGET_PIPELINE, TARGET_BROKER_HEARTBEAT 등 (콜러블 주입) |
| Health | `ops.automation.health.HealthMonitor`, `run_checks()` | CHECK_GOOGLE_SHEETS, CHECK_BROKER_HEARTBEAT 등 (콜러블 주입). 치명적 실패 시 `alert_channel.send_critical()` |
| Alerts | `ops.automation.alerts.AlertChannel`, `LogOnlyAlertChannel` | `send_critical(message)`, `send_warning(message)` |

상세: [automation/README.md](automation/README.md)

---

## 2. Backup

| 컴포넌트 | 진입점 | 비고 |
|----------|--------|------|
| BackupManager | `ops.backup.manager.BackupManager` (구현 시) | tar.gz 아카이브. `run()` → BackupManifest |
| Backup 전략 | `ops.backup.strategy` | ArchiveBackupStrategy, FileBackupStrategy (구현 시) |

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

상세: [retention/README.md](retention/README.md)

---

## 5. 운영 체크

백업/스케줄/알림 실패 시 점검·복구: [백업_스케줄_알림_운영_체크.md](../../docs/tasks/phases/Phase_09_Ops_Automation/백업_스케줄_알림_운영_체크.md)
