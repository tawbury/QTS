# Phase 10 — 테스트 스위트 구조 및 실행 절차

> **목적**: 테스트 계층(Unit/Engine/Contract/Integration/E2E)을 아키텍처 문서 기준으로 정리하고, 실행 절차를 단일 문서로 고정한다.  
> **근거**: [docs/arch/10_Testability_Architecture.md](../../../arch/10_Testability_Architecture.md)

---

## 1. 테스트 계층별 경로·규칙

아키텍처의 9계층과 `tests/` 하위 경로 매핑 및 규칙이다.

| 계층 | 아키텍처 명칭 | tests/ 경로 | 규칙·비고 |
|------|----------------|-------------|-----------|
| **L1** | Unit Test | `tests/config/`, `tests/runtime/risk/calculators/`, `tests/runtime/schema_auto/`, `tests/google_sheets_integration/` (일부) | 단일 모듈·함수 검증. Mock 기반. |
| **L2** | Engine Test | `tests/engines/`, `tests/runtime/strategy/`, `tests/runtime/risk/` | Strategy/Risk/Portfolio/Performance 엔진 입출력 검증. |
| **L3** | Contract Test | `tests/contracts/`, `tests/fixtures/contracts.py`, `tests/api/test_response_shapes.py` | Raw/Calc/Engine I/O/UI Contract 구조 검증. Fixture 기반 조기 감지. |
| **L4** | ETEDA Pipeline Integration | `tests/runtime/execution_loop/`, `tests/runtime/execution/`, `tests/runtime/integration/` | 5단계 결합·Phase 경계 통합. |
| **L5** | Broker Integration | `tests/runtime/broker/` | Mock Broker + opt-in 실 브로커 스모크. |
| **L6** | Safety Layer Test | `tests/ops/safety/` | Fail-Safe/Guardrail/Anomaly 조건. |
| **L7** | UI Rendering Test | (현재 UI Contract·렌더 로직 테스트 산재) | UI Contract 기반 표시 검증. |
| **L8** | Ops/Automation Test | `tests/ops/automation/`, `tests/ops/maintenance/`, `tests/ops/decision/` | Auto-Check/Sync/Report/Scheduler. |
| **L9** | End-to-End Test | `tests/runtime/integration/`, `tests/ops/maintenance/test_automation_e2e.py` | Strategy → ETEDA → Broker → Ledger → UI. |

### 1.1 디렉터리 규칙

- **파일명**: `test_*.py` (pytest 기본).
- **계층 혼합 금지**: 한 디렉터리는 한 계층에 대응하도록 유지. 예: `tests/engines/`는 Engine만, `tests/runtime/broker/`는 Broker 통합만.
- **conftest.py**: 루트 `tests/conftest.py`에 공통 마커·경로 설정; 하위 `conftest.py`는 해당 계층 전용 fixture.

---

## 2. Flaky·환경 의존 테스트 분리 정책

### 2.1 원칙

- **CI 기본 실행**: 외부 서비스·실 계좌·실 API 없이 재현 가능한 테스트만 실행.
- **환경 의존 테스트**: 마커로 표시하고, opt-in으로만 실행.

### 2.2 마커 정의 (tests/conftest.py)

| 마커 | 의미 | 실행 방법 | 비고 |
|------|------|-----------|------|
| `live_sheets` | Google Sheets 실 API 연동 필요 | `pytest -m live_sheets` | CI 기본 제외. env 미설정 시 스킵. |
| `real_broker` | 실 브로커(KIS 등) 스모크 | `pytest -m real_broker` 또는 `QTS_RUN_REAL_BROKER=1` | CI 기본 제외. |

### 2.3 Flaky 대응

- **Flaky 의심 케이스**: `@pytest.mark.flaky` 또는 별도 마커(예: `flaky`)로 표시 후, CI에서는 스킵하거나 재시도 정책 적용.
- **타이밍/네트워크 의존**: 가능하면 Mock·고정 fixture로 대체; 불가 시 위 마커로 분리.

### 2.4 정리

- **환경 의존** = `live_sheets`, `real_broker` 등 마커 사용.
- **Flaky** = 표시 후 스킵 또는 재시도로 분리. 신규 테스트는 flaky 없이 작성하는 것을 목표로 한다.

---

## 3. 테스트 실행 절차 (단일 참조)

### 3.1 사전 조건

- 프로젝트 루트에서 실행.
- `PYTHONPATH`에 프로젝트 루트 및 `src` 포함 (또는 `pip install -e .`).  
  `tests/conftest.py`가 루트/`src`를 `sys.path`에 넣어 주므로, **프로젝트 루트에서 `pytest`만 호출하면 됨.**

### 3.2 기본 실행 (CI·일반 회귀)

```bash
# 전체 (환경 의존 제외)
pytest tests/ -v -m "not live_sheets and not real_broker"

# 특정 계층만
pytest tests/engines/ -v
pytest tests/ops/safety/ -v
pytest tests/runtime/broker/ -v -m "not real_broker"
pytest tests/google_sheets_integration/ tests/runtime/data/test_google_sheets_client.py -v -m "not live_sheets"
```

### 3.3 환경 의존 테스트 (opt-in)

```bash
# 실 Google Sheets 연동
pytest -m live_sheets -v

# 실 브로커 스모크
pytest -m real_broker -v
# 또는
set QTS_RUN_REAL_BROKER=1
pytest tests/runtime/broker/ -v
```

### 3.4 계층별 빠른 실행 예시

| 목적 | 명령 |
|------|------|
| Unit·Engine만 | `pytest tests/config/ tests/engines/ tests/runtime/strategy/ tests/runtime/risk/ -v` |
| Safety만 | `pytest tests/ops/safety/ -v` |
| Broker(Mock만) | `pytest tests/runtime/broker/ -v -m "not real_broker"` |
| Pipeline·ETEDA | `pytest tests/runtime/execution_loop/ tests/runtime/execution/ tests/runtime/integration/ -v` |
| Ops·Maintenance | `pytest tests/ops/automation/ tests/ops/maintenance/ tests/ops/decision/ -v` |

### 3.5 CI 권장

- 기본: `pytest tests/ -v -m "not live_sheets and not real_broker"`.
- 커버리지: `pytest tests/ ... --cov=src --cov-report=...` (선택).
- 실패 시: 실패한 계층 경로만 재실행하여 원인 범위 축소.

---

## 4. 코드 품질 — 테스트·코드 인터페이스 정합성

- 테스트는 **실제 코드의 공개 인터페이스**만 사용한다. 내부 구현(비공개 함수·클래스)에 직접 의존하지 않는다.
- 리팩터링 시 **Contract/Enum/정책 클래스** 변경이 있으면 해당 테스트를 함께 수정한다.
  - 예: `DataRetentionPolicy` / `FileRetentionPolicy` 사용처는 `ops.retention.policy` 기준으로 유지. (기존 `RetentionPolicy` 별칭은 하위 호환용.)
- 신규 테스트 작성 시: 대상 모듈의 **export된 API**만 import하여 사용한다.

---

## 5. 관련 문서

- [10_Testability_Architecture.md](../../../arch/10_Testability_Architecture.md) — 계층 정의·범위
- [tests/runtime/broker/README.md](../../../../tests/runtime/broker/README.md) — Broker Mock vs Real
- [tests/google_sheets_integration/README.md](../../../../tests/google_sheets_integration/README.md) — Google Sheets 테스트
- [task_01_test_suite_structure.md](./task_01_test_suite_structure.md) — 본 작업 태스크

---

**문서 버전**: 1.0  
**최종 갱신**: 2026-01-31
