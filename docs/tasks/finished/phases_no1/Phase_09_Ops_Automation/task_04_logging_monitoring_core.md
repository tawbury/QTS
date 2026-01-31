# Phase 9 — Ops Automation: Logging & Monitoring Core

## 목표

- 중앙 로깅 시스템 및 모니터링 코어 구현
- 실시간 상태 감시 기능 확보

## 근거

- Logging & Monitoring Core가 완전히 부재함
- 실시간 모니터링 인터페이스 필요
- Ops & Safety Layer의 핵심 기능 구현 필요

## 작업

- [x] Central Logging System 구축
  - [x] `src/runtime/monitoring/central_logger.py` 구현
  - [x] ETEDA Pipeline 단계별 로깅 (로거 이름: `runtime.eteda` 등)
  - [x] Engine 실행 로그 수집 (`runtime.engine`)
  - [x] Broker 통신 로깅 (`runtime.broker`)
- [x] Metrics Collection System
  - [x] `src/runtime/monitoring/metrics_collector.py` 구현
  - [x] Engine 성능 지표 수집 (register_engine_collector)
  - [x] 시스템 리소스 모니터링 (register_system_collector)
  - [x] 비즈니스 지표(손익, 거래량 등) 수집 (register_business_collector)
- [x] Real-time Monitoring Dashboard (기반 구현됨)
  - [x] 실시간 상태 감시 UI 기반 마련 — **구현됨**: R_Dash 시트 + R_DashWriter(`src/runtime/ui/r_dash_writer.py`) + renderers(account, pipeline_status, risk, performance, meta). .env 기반 Google Sheets 접속 시 R_Dash 시트 존재·데이터 확인됨. Phase 6는 블록 확장/전송 채널 정교화.
  - [x] Alert 및 알림 시스템 구현 (task_02: HealthMonitor + AlertChannel)
  - [x] Health Check 기능 확장 (task_02: HealthMonitor)
- [ ] Log Management (추후 확장)
  - [ ] 로그 회전 및 보관 정책
  - [ ] 로그 검색 및 분석 기능
  - [ ] 에러 로그 자동 분류

## 미결 사항 — 차기 진행 단계

| 미결 항목 | 진행 단계 | 비고 |
|----------|-----------|------|
| **실시간 상태 감시 UI** | **이미 구현 (Phase 6 기반)** | R_Dash 시트·R_DashWriter·renderers로 계좌/파이프라인 상태/리스크/성과/메타 블록 갱신. .env(GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_KEY) 기반 접속 검증 완료. Phase 6 확장: MetricsCollector.snapshot/Health 시각화 블록 추가·전송 채널 정교화. |
| **로그 회전 및 보관 정책** | **Phase 9 확장 (Ops)** | 중앙 로깅에 파일 핸들러(RotatingFileHandler 등) 도입 시점에 진행. ops 정책·배포 환경에 맞춰 보관 일수/용량 정의. Phase 9 후속 task 또는 `src/runtime/monitoring/README.md` 로그 관리 전략 확장. |
| **로그 검색 및 분석** | **Phase 9 확장 또는 Phase 10** | 구조화 로그(JSON) 전환 후 검색/집계 도구 연동 시. 운영 분석은 Phase 9, 품질/회귀 분석은 Phase 10(Test & Governance)과 연계 가능. |
| **에러 로그 자동 분류** | **Phase 9 확장 (Ops)** | Fail-Safe 코드(FS0xx)·브로커 오류 등 분류 규칙을 Ops 레이어에 두고, 로그 파이프라인 또는 알림 연동 시 진행. Phase 9 후속 task. |

## 완료 조건

- [x] 중앙 로깅 시스템이 동작함
- [x] 실시간 모니터링이 가능함 (MetricsCollector.snapshot, 스텁 수집기)
- [x] Alert 및 알림 기능이 구현됨 (task_02)

## 구현 산출물

- `src/runtime/monitoring/central_logger.py`: get_logger, configure_central_logging, LOG_*, get_*_logger
- `src/runtime/monitoring/metrics_collector.py`: MetricsCollector, MetricsSnapshot
- `src/runtime/monitoring/__init__.py`, `README.md`
- `tests/runtime/monitoring/test_central_logger.py`, `test_metrics_collector.py`
