
---

# QTS 메인 페이즈 상태 정리 문서

_(Session Consolidation Report — Main Phase View)_

---

## 0. 문서 목적 및 기준

본 문서는 이번 세션에서 논의·검증·확정된 내용을 기반으로  
QTS 전체를 **메인 페이즈 단위**로 나누어 다음을 명확히 한다.

- 이미 **정리·검증·확정된 영역**
    
- 아직 **정리되지 않았거나 의도적으로 미착수 상태인 영역**
    
- “누락”과 “미도달 Phase”를 구분
    

본 문서는

- 설계 변경을 포함하지 않으며
    
- 구현 지시를 포함하지 않는다.
    

---

## 1. 메인 페이즈별 상태 요약 (Overview)

| 메인 페이즈                               | 상태       |
| ------------------------------------ | -------- |
| Phase 0. Observer Infrastructure     | ↗️ 독립 프로젝트 분리 |
| Phase 1. Schema & Sheet Mapping      | 🟡 부분 구현 |
| Phase 2. Config Architecture (Sheet) | 🟡 부분 구현 |
| Phase 3. Config Architecture (Local) | ✅ 구현 완료 |
| Phase 4. Engine Layer                | 🟡 부분 구현 |
| Phase 5. Execution Pipeline (ETEDA)  | 🟡 부분 구현 |
| Phase 6. Dashboard / Visualization   | 🟡 부분 구현 |
| Phase 7. Safety & Risk Core          | 🟡 부분 구현 |
| Phase 8. Multi-Broker Integration    | 🟡 부분 구현 |
| Phase 9. Ops & Automation            | 🟡 부분 구현 |
| Phase 10. Test & Governance          | 🟡 부분 구현 |

---

## 1.1 Phase Task 문서 위치

- Phase별 상세 Task 문서: `docs/tasks/phases/`
- 인덱스: `docs/tasks/phases/README.md`

---

## 2. 코드베이스 대조 기준 구현 현황 (Single Source of Truth)

**대조 기준일:** 2026-01-29  
**대조 범위:** `src/`, `config/`, `tests/`  
**판정 기준:**

- **구현 완료(✅)**
  - 기능의 핵심 코드가 존재
  - 주요 진입점에서 호출(또는 명확한 wiring)이 가능
  - 최소한의 테스트/검증 근거가 존재
- **부분 구현(🟡)**
  - 코드 자산은 존재하나,
    - wiring(생성자 시그니처/호출 경로) 불일치, 또는
    - 기능 일부 누락(스케줄러/정책/렌더러 등), 또는
    - 테스트/문서가 현 구현과 불일치
- **분리(↗️)**
  - 본 프로젝트 범위를 벗어나 별도 프로젝트로 분리

---

### Phase 0. Observer Infrastructure

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Observer 분리 | ↗️ | 2026-01-28 | `docs/arch/09_Ops_Automation_Architecture.md` |

---

### Phase 1. Schema & Sheet Mapping

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Google Sheets 클라이언트 모듈 | 🟡 |  | `src/runtime/data/google_sheets_client.py` |
| 시트 리포지토리(포지션/레저/히스토리 등) | 🟡 |  | `src/runtime/data/repositories/` |
| 스키마 로더/레지스트리 | 🟡 |  | `src/runtime/config/schema_loader.py`, `src/runtime/schema/` |

**비고:** 코드 자산은 존재하나, 일부 호출부/매니저 계층에서 생성자 시그니처 불일치 정황이 있어 “기능 완결”로 판정하지 않음.

---

### Phase 2. Config Architecture (Sheet)

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Config 3분할 모델/머지 로직 | 🟡 |  | `src/runtime/config/config_loader.py`, `src/runtime/config/config_models.py` |
| Sheet 기반 Config 로딩 | 🟡 |  | `src/runtime/config/sheet_config.py` |

**비고:** `sheet_config.py`가 `GoogleSheetsClient`의 현재 인터페이스와 불일치하는 정황이 있어(호출/생성자), “완료”로 판정하지 않음.

---

### Phase 3. Config Architecture (Local)

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Local Config 파일/로더 | ✅ |  | `config/local/config_local.json`, `src/runtime/config/local_config.py` |
| Config 머지 오케스트레이터(로컬 우선) | 🟡 |  | `src/runtime/config/config_loader.py` |

---

### Phase 4. Engine Layer

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Portfolio Engine | 🟡 |  | `src/runtime/engines/portfolio_engine.py` |
| Performance Engine | 🟡 |  | `src/runtime/engines/performance_engine.py` |
| Strategy Engine | 🟡 |  | `src/runtime/engines/strategy_engine.py` |

**비고:** 엔진 구현은 존재하나, 테스트 코드가 현재 생성자 시그니처와 불일치하는 정황이 있어 “검증 완료”로 판정하지 않음.

---

### Phase 5. Execution Pipeline (ETEDA)

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| ETEDA Runner(런타임) | 🟡 |  | `src/runtime/pipeline/eteda_runner.py` |
| 실행 루프/제어 | 🟡 |  | `src/runtime/execution_loop/` |
| Ops Decision Pipeline | 🟡 |  | `src/ops/decision_pipeline/` |

**비고:** Runner가 일부 리포지토리 생성자 호출과 불일치하는 정황이 있어(스프레드시트 ID 등), “동작 완료”로 판정하지 않음.

---

### Phase 6. Dashboard / Visualization

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| R_Dash 리포지토리 | 🟡 |  | `src/runtime/data/repositories/r_dash_repository.py` |
| Zero-Formula UI 렌더링/계약 빌더 | 🟡 |  | (전용 렌더러/계약 빌더는 코드베이스에서 명확히 확인되지 않음) |

---

### Phase 7. Safety & Risk Core

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Risk 구성요소(계산기/게이트/정책) | 🟡 |  | `src/runtime/risk/` |
| Ops Safety Guard | 🟡 |  | `src/ops/safety/guard.py` |
| Lockdown/Fail-Safe 상태 머신(완전판) | 🟡 |  | (부분 구현 정황, 완전판 확인 필요) |

---

### Phase 8. Multi-Broker Integration

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Broker 어댑터 베이스/구현(KIS) | 🟡 |  | `src/runtime/broker/` |

---

### Phase 9. Ops & Automation

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Backup / Maintenance / Retention | 🟡 |  | `src/ops/backup/`, `src/ops/maintenance/`, `src/ops/retention/` |
| Ops 자동화(스케줄러/트리거) | 🟡 |  | `src/ops/automation/` (현재 비어 있음) |

---

### Phase 10. Test & Governance

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| 테스트 폴더 구조/테스트 자산 | 🟡 |  | `tests/` |
| 거버넌스(Phase 종료 기준/검증 기준) 문서 | 🟡 |  | (Roadmap에 명시 필요) |

---

## 3. 다음 우선순위 (Roadmap Items)

| 업무 | 상태 | 완료일 |
|---|---|---|
| 데이터 레이어/리포지토리/매니저/Runner 간 인터페이스 정합성 확보 | 🟡 |  |
| Config Sheet 로딩 경로를 현재 GoogleSheetsClient 인터페이스에 맞게 정리 | 🟡 |  |
| ETEDA Runner의 리포지토리 생성/의존성 주입 정합성 확보 | 🟡 |  |
| Ops 스케줄링(automation) 구현 범위 확정 및 최소 기능 구현 | 🟡 |  |
| Dashboard(Zero-Formula UI) 구현 범위 확정 및 최소 렌더링 경로 정의 | 🟡 |  |

---

## 4. Architecture Alignment Notes (Post-Session)

최근 추가된 아키텍처 문서(`docs/arch/sub/`)는 기존 메인 페이즈와 개념적으로 다음과 같이 대응된다.

| 문서 | 개념적 대응 |
|------|-------------|
| 14_Capital_Flow_Architecture.md | 자본 흐름 분리; 풀 배분·프로모션 관련 (Engine/Capital) |
| 15_Scalp_Execution_Micro_Architecture.md | 마이크로 실행 파이프라인; Phase 5 (ETEDA) 실행 서브단계 |
| 16_Micro_Risk_Loop_Architecture.md | 마이크로 리스크 루프; Phase 7 (Safety & Risk Core) |
| 17_Event_Priority_Architecture.md | 이벤트 우선순위; Phase 5 (ETEDA) 및 파이프라인 순서 |
| 18_System_State_Promotion_Architecture.md | 시스템 상태 프로모션; 페이즈 전이 및 상태 생명주기 |

이 문서들은 **페이즈 완료를 나타내지 않으며**, 아키텍처 준비 상태만을 반영한다.

### 4.1 Phase Dependency Clarification

일부 페이즈는 위 아키텍처 문서에서 기술한 **명시적 아키텍처 전제**를 갖는다. 예: Phase 5 (ETEDA)는 파이프라인 순서를 위해 Event Priority Architecture를 전제하고, Phase 7 (Safety & Risk Core)은 고주기 리스크 제어를 위해 Micro Risk Loop를 전제하며, 페이즈 전이 및 상태 생명주기는 System State Promotion 모델을 전제한다. 위 매핑은 설명 목적이며, 작업 지시나 순서 명령을 도입하지 않는다.

### 4.2 Roadmap Interpretation Guardrail

본 Roadmap은 **구조적 준비 상태**를 반영하며, 실행 순서를 규정하지 않는다. 아키텍처 문서의 완성은 구현 완료를 의미하지 않는다. 페이즈 상태(✅ 🟡 ↗️)는 아키텍처 문서 존재만으로 변경되지 않는다. 이 구분은 Roadmap 오해를 방지하기 위한 것이다.
