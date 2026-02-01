# Ops & Automation Architecture

**Version:** v2.0.0
**Status:** Updated - Observer Separated
**Last Updated:** 2026-01-28

---

## Observer (독립 프로젝트로 분리)

> **Notice:** Observer 모듈은 독립 프로젝트로 분리되었습니다.
>
> Observer는 "판단 없는 관찰/기록 시스템"으로, QTS 본 프로젝트와 독립적으로 운영됩니다.
> Observer 아키텍처 및 구현 세부사항은 해당 독립 프로젝트를 참조하세요.

**분리 일자:** 2026-01-28

---

## 1. Ops Layer 개요

QTS Ops 레이어는 시스템 운영 및 자동화를 담당합니다.

### 1.1 현재 구성요소

| 모듈 | 경로 | 역할 |
|------|------|------|
| Backup Manager | `src/ops/backup/` | 데이터셋 백업 관리 |
| Maintenance Coordinator | `src/ops/maintenance/` | 유지보수 작업 조정 |
| Retention Policy | `src/ops/retention/` | 데이터 보관 정책 |
| Decision Pipeline | `src/ops/decision_pipeline/` | ETEDA 의사결정 파이프라인 |
| Safety Guard | `src/ops/safety/` | 안전 가드 |
| Logging (Central) | `src/runtime/monitoring/central_logger.py` | 중앙 로깅 및 파일 로그 출력 |
| Runtime Bridge | `src/ops/runtime/` | Ops↔Runtime 연동 |

### 1.2 제거된 구성요소

- `src/ops/observer/` — 독립 프로젝트로 분리됨

---

## 2. Decision Pipeline

ETEDA (Extract → Transform → Evaluate → Decide → Act) 파이프라인:

```
src/ops/decision_pipeline/
├── contracts/          # 데이터 계약
│   ├── decision_snapshot.py
│   ├── execution_hint.py
│   └── order_decision.py
├── execution_stub/     # 실행 스텁
│   ├── noop_executor.py
│   ├── sim_executor.py
│   └── virtual_executor.py
└── pipeline/           # 파이프라인 단계
    ├── extract.py
    ├── transform.py
    ├── evaluate.py
    ├── decide.py
    └── runner.py
```

---

## 3. Backup & Retention

### 3.1 Backup Manager

- 정기 백업 스케줄링
- 증분/전체 백업 지원
- 복구 절차 관리

### 3.2 Retention Policy

- 데이터 보관 기간 정책
- 자동 정리 스케줄링
- 저장 공간 관리

---

## 4. Maintenance

### 4.1 Coordinator

- 유지보수 작업 조정
- 시스템 상태 점검
- 자동화된 정리 작업

---

## 5. Runtime Bridge

Ops 레이어와 Runtime 레이어 간 연동:

- `src/ops/runtime/config_bridge.py` — Config 연동
- `src/ops/runtime/maintenance_runner.py` — 유지보수 실행기

---

## 6. Logging Infrastructure (파일 로그)

### 6.1 개요

QTS는 실행 로그를 **콘솔과 파일**에 동시에 출력한다.  
구현: `src/runtime/monitoring/central_logger.py`의 `configure_central_logging()`.

### 6.2 파일 로그 스펙

| 항목 | 내용 |
|------|------|
| **저장 경로** | `{project_root}/logs/` |
| **파일명** | `qts_{YYYY-MM-DD}.log` (일별 단일 파일) |
| **포맷** | `%(asctime)s [%(levelname)s] %(name)s: %(message)s` |
| **핸들러** | `logging.handlers.TimedRotatingFileHandler` (자정 기준 일별 로테이션) |
| **보관** | 기본 7일 (backupCount), 환경 변수 `QTS_LOG_RETENTION_DAYS`로 조정 가능 |
| **인코딩** | UTF-8 |

### 6.3 적용 시점

- `main.py` 진입 시 `configure_central_logging(log_file=...)` 호출
- `log_file=None`이면 파일 로그 비활성화 (콘솔만)
- `--local-only` 포함 여부와 무관하게 파일 로그 활성화

### 6.4 근거

- [00_Architecture.md](./00_Architecture.md) §3.3.1 Logging Core
- [07_FailSafe_Architecture.md](./07_FailSafe_Architecture.md) §9.2 — "모든 기록은 JSON 및 파일 로그에도 저장"

---

## 7. 관련 문서

- **Logging Core**: [00_Architecture.md](./00_Architecture.md) §3.3.1
- **ETEDA Pipeline**: [03_Pipeline_ETEDA_Architecture.md](./03_Pipeline_ETEDA_Architecture.md)
- **Fail-Safe & Safety**: [07_FailSafe_Architecture.md](./07_FailSafe_Architecture.md)
- **Testability**: [10_Testability_Architecture.md](./10_Testability_Architecture.md)
- **Change Management**: [11_Architecture_Change_Management.md](./11_Architecture_Change_Management.md)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-28 | v2.0.0 | Observer 독립 프로젝트 분리, 문서 재구성 |
| 2026-01-09 | v1.0.0 | 초기 Observer Architecture 통합 문서 |
