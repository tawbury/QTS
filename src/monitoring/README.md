# app/monitoring — Logging & Metrics

## 목표

- 중앙 로깅 시스템 및 메트릭 수집 코어 제공
- ETEDA/Engine/Broker 단계별 로거 통일, 실시간 메트릭 스냅샷

## Central Logging

### 로거 이름 계층

| 이름 | 상수 | 용도 |
|------|------|------|
| ETEDA Pipeline | `LOG_ETEDA` | Extract/Transform/Evaluate/Decide/Act 단계 로그 |
| Engine | `LOG_ENGINE` | Strategy/Portfolio/Performance/Trading 실행 로그 |
| Broker | `LOG_BROKER` | 주문/연결/에러 등 브로커 통신 로그 |
| Monitoring | `LOG_MONITORING` | 메트릭/헬스/모니터링 로그 |

### 사용

- `get_logger(name)` — 계층 하위 로거 (가급적 `LOG_*` 상수 사용)
- `get_eteda_logger()`, `get_engine_logger()`, `get_broker_logger()`, `get_monitoring_logger()` — 편의 함수
- `configure_central_logging(level=..., format_string=..., root=True, log_file=..., retention_days=...)` — 앱 진입 시 한 번 호출

### 파일 로그 (구현됨)

- `log_file`: Path 지정 시 `TimedRotatingFileHandler` 추가 (자정 기준 일별 로테이션)
- 기본 경로: `{project_root}/logs/qts.log`
- `retention_days`: 로테이션 후 보관 일수 (기본 7일, 환경 변수 `QTS_LOG_RETENTION_DAYS`로 조정)
- 인코딩: UTF-8

### 로그 관리 전략
- **검색/분석**: 구조화 로그(JSON) 전환 시 추후; 에러 로그 자동 분류는 별도 도구 연동 시 확장.

## Metrics Collection

- **MetricsCollector**: in-memory counters(`inc`) / gauges(`set_gauge`), `snapshot()`으로 시점 스냅샷 반환.
- **스텁 수집기**: `register_engine_collector(fn)`, `register_system_collector(fn)`, `register_business_collector(fn)` — 각각 Engine 성능, 시스템 리소스(CPU/메모리), 비즈니스(손익/거래량)용 콜러블 등록. `snapshot()` 시 pull하여 gauges/counters에 병합.
- **실시간 모니터링**: 대시보드/알림은 `snapshot()` 결과를 주기적으로 읽어 사용; UI/Alert 연동은 별도 모듈(ops automation, UI)에서 수행.

## Alert / Health 확장

- 치명적/경고 알림: `ops/automation` 의 **HealthMonitor** + **AlertChannel** 사용 (task_02).
- 중앙 로거와 연동: ETEDA/Engine/Broker에서 `get_*_logger()` 사용 시 동일 포맷·레벨 적용; Health 실패 시 `send_critical` 호출은 ops 레이어에서 처리.

## 경계

- 로깅·메트릭 코어는 `app/monitoring/` 에만 구현.
- 로그 포맷·핸들러 세부(파일/회전)는 앱 설정 또는 ops 정책에서 결정.
