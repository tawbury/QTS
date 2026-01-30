# Phase 9 — Ops/Automation: Scheduler (Minimum)

## 목표

- ETEDA를 주기적으로 실행할 수 있는 최소 스케줄러를 제공

## 근거

- `docs/arch/09_Ops_Automation_Architecture.md`
- `docs/tasks/backups/Phase_09_Ops_Automation/task.md`

## 작업

- [x] Scheduler 구현 방식 확정
  - [x] Interval 기반 최소 구현 + 실패 백오프: `src/ops/automation/scheduler.py` (MinimalScheduler, per-target interval/backoff)
- [x] 스케줄 대상 정의
  - [x] Pipeline 실행: `TARGET_PIPELINE` (콜러블 주입)
  - [x] Broker heartbeat: `TARGET_BROKER_HEARTBEAT`
  - [x] Dashboard update: `TARGET_DASHBOARD_UPDATE`
  - [x] Backup/Maintenance: `TARGET_BACKUP_MAINTENANCE`
- [x] 코드 품질 개선(필수)
  - [x] 스케줄링 로직은 `src/ops/automation/` 에만 존재; 런타임은 콜러블로 주입(경계 고정)

## 완료 조건

- [x] 운영 환경에서 스케줄 실행/중지/에러 처리 규칙이 문서화되어 있다. (`src/ops/automation/README.md`)
