# Phase 9 — Ops/Automation: Scheduler (Minimum)

## 목표

- ETEDA를 주기적으로 실행할 수 있는 최소 스케줄러를 제공

## 근거

- `docs/arch/09_Ops_Automation_Architecture.md`
- `docs/tasks/backups/Phase_09_Ops_Automation/task.md`

## 작업

- [ ] Scheduler 구현 방식 확정
  - [ ] Interval 기반 최소 구현 + 실패 백오프
- [ ] 스케줄 대상 정의
  - [ ] Pipeline 실행
  - [ ] Broker heartbeat
  - [ ] Dashboard update
  - [ ] Backup/Maintenance
- [ ] 코드 품질 개선(필수)
  - [ ] 스케줄링 로직이 런타임 로직을 침범하지 않도록 경계 고정

## 완료 조건

- [ ] 운영 환경에서 스케줄 실행/중지/에러 처리 규칙이 문서화되어 있다.
