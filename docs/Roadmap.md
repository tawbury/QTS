
---

# QTS 메인 페이즈 상태 정리 문서

_(Session Consolidation Report — Main Phase View)_

**최종 갱신:** 2026-01-31 — Phase 0~10 Task 문서 정리 완료, `docs/tasks/finished/phases/` 이관 반영.

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
| Phase 1. Schema & Sheet Mapping      | ✅ 구현 완료 |
| Phase 2. Config Architecture (Sheet) | ✅ 구현 완료 |
| Phase 3. Config Architecture (Local) | ✅ 구현 완료 |
| Phase 4. Engine Layer                | ✅ 구현 완료 |
| Phase 5. Execution Pipeline (ETEDA)  | ✅ 구현 완료 |
| Phase 6. Dashboard / Visualization   | ✅ 구현 완료 |
| Phase 7. Safety & Risk Core          | ✅ 구현 완료 |
| Phase 8. Multi-Broker Integration    | ✅ 구현 완료 |
| Phase 9. Ops & Automation            | ✅ 구현 완료 |
| Phase 10. Test & Governance          | ✅ 구현 완료 |

---

## 1.1 Phase Task 문서 위치

- **로드맵 기준 구현 Task(현행):** `docs/tasks/phases/` — [README](tasks/phases/README.md)
- **정리 완료(이관):** `docs/tasks/finished/phases/` — [README](tasks/finished/phases/README.md)
- **현황:** 로드맵 기준 Phase별 Task 문서는 `docs/tasks/phases/` 에 신규 생성됨. 이전 정리 완료 문서는 `finished/phases/` 에 보관.

---

## 1.2 로드맵 진행 현황 (2026-01-31 기준)

| 구분 | 진행률 | 비고 |
|------|--------|------|
| **Task 문서화** | 100% | Phase 0~10 상세 Task·정책 문서 정리 완료, `finished/phases/` 보관 |
| **구현(Exit Criteria 기준)** | Phase 1·2·3·4·5·6·7·8·9·10 완료(✅), Phase 0 분리(↗️) | Exit Criteria 충족 시에만 ✅ 전환 |

---

## 2. 코드베이스 대조 기준 구현 현황 (Single Source of Truth)

**대조 기준일:** 2026-01-31  
**대조 범위:** `src/`, `config/`, `tests/`  
**판정 기준:**  
Phase 상태(✅/🟡) 변경은 **객관적 Exit Criteria**에 따른다. 상세: [Phase 10 — Phase Exit Criteria](tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md).

- **구현 완료(✅)**
  - 해당 Phase의 Exit Criteria(필수 테스트 통과, 운영 체크, 문서 SSOT 반영)를 **모두** 만족할 때만 적용.
  - 기능의 핵심 코드 존재, 주요 진입점에서 호출(또는 명확한 wiring) 가능, 최소한의 테스트/검증 근거 존재.
- **부분 구현(🟡)**
  - 코드 자산은 존재하나,
    - wiring(생성자 시그니처/호출 경로) 불일치, 또는
    - 기능 일부 누락(스케줄러/정책/렌더러 등), 또는
    - 테스트/문서가 현 구현과 불일치
  - Exit Criteria 체크리스트 중 하나라도 미충족 시 🟡 유지.
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
| Google Sheets 클라이언트 모듈 | ✅ | 2026-01-31 | `src/runtime/data/google_sheets_client.py`, Google_Sheets_Contract.md, data/README.md |
| 시트 리포지토리(포지션/레저/히스토리 등) | ✅ | 2026-01-31 | `src/runtime/data/repositories/`, BaseSheetRepository Range/Headers/Row 규칙 |
| 스키마 로더/레지스트리 | ✅ | 2026-01-31 | `src/runtime/config/schema_loader.py`, get_schema_loader(project_root) |

**비고:** Phase 10 Exit Criteria §2.1·§2.2·§2.3 충족. 생성자 시그니처·예외·wiring 문서화(Google_Sheets_Contract, src/runtime/data/README.md). 테스트: `tests/google_sheets_integration/`, `tests/runtime/data/` 통과.

---

### Phase 2. Config Architecture (Sheet)

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Config 3분할 모델/머지 로직 | ✅ | 2026-01-31 | `config_loader.load_unified_config`, _merge_configs(Local 우선). 13_Config_3분할 §3.3 |
| Sheet 기반 Config 로딩 | ✅ | 2026-01-31 | `sheet_config.load_sheet_config(..., client=None)`. GoogleSheetsClient 인터페이스 정합 |

**비고:** Phase 10 Exit Criteria §2.1·§2.2·§2.3 충족. 테스트: `tests/config/` (test_sheet_config Mock). 운영 체크: [Config_Sheet_운영_체크.md](tasks/phases/Phase_02_Config_Sheet/Config_Sheet_운영_체크.md).

---

### Phase 3. Config Architecture (Local)

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Local Config 파일/로더 | ✅ | (기존) | `config/local/config_local.json`, `src/runtime/config/local_config.py`. `tests/config/test_local_config.py` |
| Config 머지 오케스트레이터(로컬 우선) | 🟡 |  | `config_loader.load_unified_config`·`load_local_only_config`. Phase 2에서 Sheet·머지 정합 검증. 별도 Exit Criteria 적용 가능 |

---

### Phase 4. Engine Layer

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Portfolio Engine | ✅ | 2026-01-31 | `portfolio_engine.py`, tests/engines/test_portfolio_engine.py, engines/README.md |
| Performance Engine | ✅ | 2026-01-31 | `performance_engine.py`, tests/engines/test_performance_engine.py |
| Strategy Engine | ✅ | 2026-01-31 | `strategy_engine.py`, ETEDARunner 연동. tests/runtime/strategy/ |

**비고:** Phase 10 Exit Criteria §2.1·§2.2·§2.3 충족. 테스트–생성자 정합(79 passed). wiring·execute I/O: [src/runtime/engines/README.md](src/runtime/engines/README.md).

---

### Phase 5. Execution Pipeline (ETEDA)

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| ETEDA Runner(런타임) | ✅ | 2026-01-31 | `eteda_runner.py`, pipeline/README.md, 리포지토리 생성/DI 정합 |
| 실행 루프/제어 | ✅ | 2026-01-31 | `execution_loop/`, run_eteda_loop, ETEDALoopPolicy, Config 키 |
| Ops Decision Pipeline | ✅ | 2026-01-31 | `ops/decision_pipeline/`, pipeline/README.md §4 |

**비고:** Phase 10 Exit Criteria §2.1·§2.2·§2.3 충족. 테스트 15 passed. Runner–리포지토리 정합·wiring·설정 경로·실패/복구: [pipeline/README.md](src/runtime/pipeline/README.md), [ETEDA_파이프라인_운영_체크.md](tasks/phases/Phase_05_ETEDA_Pipeline/ETEDA_파이프라인_운영_체크.md).

---

### Phase 6. Dashboard / Visualization

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| R_Dash 리포지토리 | ✅ | 2026-01-31 | `r_dash_repository.py`, RepositoryManager 등록. ui/README.md |
| Zero-Formula UI 렌더링/계약 빌더 | ✅ | 2026-01-31 | `contract_builder`, `contract_schema`, `renderers/`, `r_dash_writer`, `zero_formula_base`. tests/contracts·tests/runtime/ui |

**비고:** Phase 10 Exit Criteria §2.1·§2.2·§2.3 충족. UI Contract/렌더러 테스트·UI 실패 시 매매 중단 아님: [ui/README.md](src/runtime/ui/README.md), [UI_실패_정책.md](tasks/phases/Phase_06_UI_Dashboard/UI_실패_정책.md).

---

### Phase 7. Safety & Risk Core

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Risk 구성요소(계산기/게이트/정책) | ✅ | 2026-01-31 | `runtime/risk/`, tests/runtime/risk/. ops/safety/README.md |
| Ops Safety Guard | ✅ | 2026-01-31 | `ops/safety/guard.py`, layer, state, codes, notifier. tests/ops/safety/ 55 passed |
| Lockdown/Fail-Safe 상태 머신(완전판) | ✅ | 2026-01-31 | state.py NORMAL/WARNING/FAIL/LOCKDOWN, 2회→LOCKDOWN, request_recovery(operator_approved). [FailSafe_Lockdown_운영_체크.md](tasks/phases/Phase_07_Safety_Risk/FailSafe_Lockdown_운영_체크.md) |

**비고:** Phase 10 Exit Criteria §2.1·§2.2·§2.3 충족. 상태 머신 완전판·복구·operator_approved: [ops/safety/README.md](src/ops/safety/README.md).

---

### Phase 8. Multi-Broker Integration

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Broker 어댑터 베이스/구현(KIS) | ✅ | 2026-01-31 | `src/runtime/broker/`, create_broker_for_execution, tests/runtime/broker/ 45 passed (Mock), real_broker opt-in |

**비고:** Phase 10 Exit Criteria §2.1·§2.2·§2.3 충족. wiring·KIS 페이로드/에러 매핑·실 주문/rollback: [broker/README.md](src/runtime/broker/README.md), [실_주문_rollback_운영_체크.md](tasks/phases/Phase_08_Broker_Integration/실_주문_rollback_운영_체크.md).

---

### Phase 9. Ops & Automation

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| Backup / Maintenance / Retention | ✅ | 2026-01-31 | `src/ops/backup/`, `src/ops/maintenance/`, `src/ops/retention/`, src/ops/README.md |
| Ops 자동화(스케줄러/트리거) | ✅ | 2026-01-31 | `src/ops/automation/` — MinimalScheduler, HealthMonitor, LogOnlyAlertChannel |

**비고:** Phase 10 Exit Criteria §2.1·§2.2·§2.3 충족. 최소 구현 범위·wiring·운영 체크: [Ops_최소_구현_범위.md](tasks/phases/Phase_09_Ops_Automation/Ops_최소_구현_범위.md), [src/ops/README.md](src/ops/README.md), [백업_스케줄_알림_운영_체크.md](tasks/phases/Phase_09_Ops_Automation/백업_스케줄_알림_운영_체크.md). tests/ops/automation, tests/ops/maintenance 22 passed.

---

### Phase 10. Test & Governance

| 업무 | 상태 | 완료일 | 근거 |
|---|---|---|---|
| 테스트 폴더 구조/테스트 자산 | ✅ | 2026-01-31 | `tests/` — Test_Suite_Structure §1 정합, 328 passed |
| 거버넌스(Phase 종료 기준/검증 기준) 문서 | ✅ | 2026-01-31 | Phase_Exit_Criteria, Test_Suite_Structure, Fixtures_and_Contract_Policy |

**비고:** Phase 10 Exit Criteria §2.1·§2.2·§2.3 충족. 기본 실행 `pytest tests/ -m "not live_sheets and not real_broker"` 328 passed. api/conftest QTS_API_TEST skip 범위를 tests/api/로 제한. 거버넌스 문서: [Phase_Exit_Criteria.md](tasks/finished/phases_no1/Phase_10_Test_Governance/Phase_Exit_Criteria.md), [Test_Suite_Structure_and_Execution.md](tasks/finished/phases_no1/Phase_10_Test_Governance/Test_Suite_Structure_and_Execution.md), [Fixtures_and_Contract_Policy.md](tasks/finished/phases_no1/Phase_10_Test_Governance/Fixtures_and_Contract_Policy.md).

---

## 3. 다음 우선순위 (Roadmap Items)

**현황:** Phase 0~10 Task 문서화는 완료됨. 아래는 구현·정합성 확보 우선순위.

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
| 18_Data_Layer_Architecture.md | 데이터 레이어; 리포지토리·매니저·Runner 인터페이스 |
| 19_Caching_Architecture.md | 캐싱; 캐시 정책·계층·무효화 |
| 20_Feedback_Loop_Architecture.md | 피드백 루프; 실행 결과·모니터링·보정 |

이 문서들은 **페이즈 완료를 나타내지 않으며**, 아키텍처 준비 상태만을 반영한다.

### 4.1 Phase Dependency Clarification

일부 페이즈는 위 아키텍처 문서에서 기술한 **명시적 아키텍처 전제**를 갖는다. 예: Phase 5 (ETEDA)는 파이프라인 순서를 위해 Event Priority Architecture를 전제하고, Phase 7 (Safety & Risk Core)은 고주기 리스크 제어를 위해 Micro Risk Loop를 전제하며, 페이즈 전이 및 상태 생명주기는 System State Promotion 모델을 전제한다. 위 매핑은 설명 목적이며, 작업 지시나 순서 명령을 도입하지 않는다.

### 4.2 Roadmap Interpretation Guardrail

본 Roadmap은 **구조적 준비 상태**를 반영하며, 실행 순서를 규정하지 않는다. 아키텍처 문서의 완성은 구현 완료를 의미하지 않는다. 페이즈 상태(✅ 🟡 ↗️)는 아키텍처 문서 존재만으로 변경되지 않는다. 이 구분은 Roadmap 오해를 방지하기 위한 것이다.
