# Ops Automation — Scheduler (Minimum)

## 목표

ETEDA를 주기적으로 실행할 수 있는 최소 스케줄러 제공 (Phase 9).

## 구현 방식

- **Interval 기반**: 각 대상별 `interval_ms` 주기로 실행.
- **실패 백오프**: 대상 실행 예외 시 `error_backoff_ms` 대기 후 재시도, `max_consecutive_errors` 초과 시 해당 대상만 스킵(루프는 계속).

## 스케줄 대상 정의

| 대상 이름 | 상수 | 설명 |
|----------|------|------|
| Pipeline 실행 | `TARGET_PIPELINE` | ETEDA runner.run_once 등 (콜러블로 주입) |
| Broker heartbeat | `TARGET_BROKER_HEARTBEAT` | 브로커 연결/상태 점검 (콜러블로 주입) |
| Dashboard update | `TARGET_DASHBOARD_UPDATE` | 대시보드 갱신 (콜러블로 주입) |
| Backup/Maintenance | `TARGET_BACKUP_MAINTENANCE` | 백업/유지보수 (콜러블로 주입, e.g. `run_maintenance_automation`) |

대상은 **콜러블로 등록**하며, 스케줄러는 런타임 로직을 직접 참조하지 않음(경계 고정).

## 운영 환경: 실행/중지/에러 처리 규칙

### 실행

- `scheduler.add_target(name, interval_ms, fn, error_backoff_ms, max_consecutive_errors)` 로 대상 등록.
- `await scheduler.run()` 으로 루프 시작. `should_stop()` 이 True 이거나 `scheduler.stop()` 호출 시까지 동작.

### 중지

- **정상 중지**: 루프 진입 전/후에 `should_stop()` 이 True 이면 즉시 종료.
- **요청 중지**: `scheduler.stop()` 호출 시 현재 사이클 완료 후 루프 종료(즉시 중단 아님).

### 에러 처리

- 대상 `fn()` 예외 발생 시: 해당 대상의 `consecutive_errors` 증가, `error_backoff_ms` 만큼 대기 후 다음 사이클로.
- `consecutive_errors >= max_consecutive_errors` 인 동안 해당 대상은 스킵; 다른 대상은 계속 실행.
- 루프 자체는 한 대상의 연속 실패로 중단되지 않음(대상별 스킵만 적용).

## 경계

- 스케줄링 로직은 `ops/automation/` 에만 존재.
- 런타임(ETEDA runner, broker, dashboard)은 **콜러블로 주입**; 스케줄러가 app 모듈을 직접 import 하지 않음.

---

# Monitoring & Alerts (Phase 9 task_02)

## Health check 항목 정의

| 항목 | 상수 | 설명 |
|------|------|------|
| Google Sheets 연결 | `CHECK_GOOGLE_SHEETS` | 시트 클라이언트 ping/연결 (콜러블 주입) |
| Repository health | `CHECK_REPOSITORY_HEALTH` | 저장소 가용성 (콜러블 주입) |
| Broker heartbeat | `CHECK_BROKER_HEARTBEAT` | 브로커 연결/상태 (콜러블 주입) |
| ETEDA loop latency | `CHECK_ETEDA_LOOP_LATENCY` | 루프 지연 (콜러블 주입) |

각 항목은 **콜러블로 등록**; HealthMonitor는 런타임을 직접 import 하지 않음.

## 알림 채널 최소 구현

- **AlertChannel** 프로토콜: `send_critical(message)`, `send_warning(message)`.
- **LogOnlyAlertChannel**: 로깅만 (critical/warning). Slack/Telegram은 추후 확장.
- 치명적 장애: HealthMonitor.run_checks() 시 실패한 항목에 대해 `alert_channel.send_critical()` 호출 → 운영자에게 전달(로그).

## 코드 품질

- 운영 코드에서 `print`/임시 디버그 출력/민감정보 로그 여부 점검: `ops/`, `app/` 에서 `print(` 미사용 확인. 민감정보는 로그에 포함하지 않음(호출부 책임).
