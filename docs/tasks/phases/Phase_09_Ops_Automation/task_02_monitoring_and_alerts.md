# Phase 9 — Ops/Automation: Monitoring & Alerts

## 목표

- 시스템 상태(heartbeat/latency/errors)를 감시하고 최소 알림 채널을 제공

## 근거

- `docs/arch/09_Ops_Automation_Architecture.md`
- `docs/arch/07_FailSafe_Architecture.md`

## 작업

- [ ] Health check 항목 정의
  - [ ] Google Sheets 연결
  - [ ] Repository health
  - [ ] Broker heartbeat
  - [ ] ETEDA loop latency
- [ ] 알림 채널 최소 구현 범위 확정
- [ ] 코드 품질 개선(필수)
  - [ ] 운영 코드에서 `print`/임시 디버그 출력/민감정보 로그 여부 점검

## 완료 조건

- [ ] 치명적 장애가 운영자에게 전달된다.
