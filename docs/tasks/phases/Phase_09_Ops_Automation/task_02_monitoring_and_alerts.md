# Phase 9 — Ops/Automation: Monitoring & Alerts

## 목표

- 시스템 상태(heartbeat/latency/errors)를 감시하고 최소 알림 채널을 제공

## 근거

- `docs/arch/09_Ops_Automation_Architecture.md`
- `docs/arch/07_FailSafe_Architecture.md`

## 작업

- [x] Health check 항목 정의
  - [x] Google Sheets 연결: `CHECK_GOOGLE_SHEETS` (콜러블 주입)
  - [x] Repository health: `CHECK_REPOSITORY_HEALTH`
  - [x] Broker heartbeat: `CHECK_BROKER_HEARTBEAT`
  - [x] ETEDA loop latency: `CHECK_ETEDA_LOOP_LATENCY`
  - [x] `src/ops/automation/health.py`: HealthCheckResult, HealthMonitor, check 이름 상수
- [x] 알림 채널 최소 구현 범위 확정
  - [x] AlertChannel 프로토콜 (send_critical, send_warning), LogOnlyAlertChannel (로깅만). Slack/Telegram 추후 확장.
- [x] 코드 품질 개선(필수)
  - [x] 운영 코드에서 `print`/임시 디버그 출력/민감정보 로그 점검: `src/ops`, `src/runtime` 에서 `print(` 미사용 확인. README에 민감정보 로그 금지 명시.

## 완료 조건

- [x] 치명적 장애가 운영자에게 전달된다. (HealthMonitor.run_checks() 실패 시 alert_channel.send_critical() 호출 → LogOnlyAlertChannel은 logging.critical)
