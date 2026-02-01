# QTS Phase 1-10 완료 문서 아카이브 (phases_no1)

본 폴더는 **Phase 1~10 완료 후 생성된 모든 Task 문서**를 보관합니다.

## 폴더 구조

```
phases_no1_completed/
├── README.md (본 파일)
├── Phase_00_Observer/
├── Phase_01_Schema_Sheet_Mapping/
├── Phase_02_Config_Sheet/
├── Phase_03_Config_Local/
├── Phase_04_Engine_Layer/
├── Phase_05_ETEDA_Pipeline/
├── Phase_06_UI_Dashboard/
├── Phase_07_Safety_Risk/
├── Phase_08_Broker_Integration/
├── Phase_09_Ops_Automation/
└── Phase_10_Test_Governance/
```

## 완료 일정 (Git Log 기준)

| Phase | 완료일 | 커밋 해시 | 비고 |
|-------|--------|-----------|------|
| 0 | 2026-01-26 | 8d52256 | Observer boundary 정의 |
| 1 | 2026-01-26 | 8d52256 | Sheets contract, repo tests, Scalp naming |
| 2-3 | 2026-01-27 | 300807e | Config Sheet + Local |
| 4 | 2026-01-27 | 4e09968 | Engine Layer & Data Layer |
| 5 | 2026-01-28 | fd5286e | ETEDA Pipeline (wiring, loop, Act policy) |
| 6 | 2026-01-28 | 85ed80c | UI Dashboard (Contract, Renderers, Zero-Formula) |
| 7 | 2026-01-29 | 6bef8d6 | Safety/Risk (Guardrail, Fail-Safe, State Machine) |
| 8 | 2026-01-29 | 6a6f273 | Broker Integration (payload, status, multi-broker) |
| 9 | 2026-01-29 | feb9c14 | Ops (scheduler, health/alerts, backup/retention) |
| 10 | 2026-01-29 | 7e3609c | Test Governance (structure, fixtures, exit criteria) |

**전체 통합 완료:** 2026-01-29 (커밋 26679b5)

## 주요 문서 유형별 분류

### 정책 문서 (Policy)
- `Phase_05_ETEDA_Pipeline/act_stage_policy.md`
- `Phase_06_UI_Dashboard/R_Dash_Update_Policy.md`
- `Phase_06_UI_Dashboard/Dashboard_Delivery_Channel_Policy.md`
- `Phase_10_Test_Governance/Fixtures_and_Contract_Policy.md`

### 계약 문서 (Contract)
- `Phase_01_Schema_Sheet_Mapping/Google_Sheets_Contract.md`
- `Phase_05_ETEDA_Pipeline/act_io_contract.md`

### Exit Criteria
- `Phase_10_Test_Governance/Phase_Exit_Criteria.md` — **SSOT for Phase 완료 판정**

### Task 문서
- 각 Phase별 `task_XX_*.md` — 세부 작업 체크리스트

### 시나리오 문서
- `Phase_10_Test_Governance/scenario1_baseline_execution.md`
- `Phase_10_Test_Governance/scenario2_simulation_stress_execution.md`
- `Phase_10_Test_Governance/deployment_validation_task10.md`

## 파일명 규칙

본 아카이브는 **원본 파일명을 유지**합니다. 리네이밍하지 않습니다.

이유:
1. 다른 문서에서 상대 경로로 참조됨 (`docs/tasks/phases/` 등)
2. Git 히스토리와 연결성 유지
3. 정책/계약 문서는 의미 있는 이름을 이미 가짐

## 용도

- **참조 전용**: Phase 1~10 구현 과정의 상세 기록
- **수정 금지**: 히스토리 보존 목적
- **현행 활용**: Phase Exit Criteria 등 일부 문서는 여전히 참조됨

## 현행 문서 위치

- **Active Operational Docs**: `docs/tasks/phases/` — 현재 운영 중인 Phase Task
- **Roadmap**: `docs/Roadmap.md` — Next-Gen Roadmap v2.0.0
- **Exit Criteria**: 본 폴더의 `Phase_10_Test_Governance/Phase_Exit_Criteria.md` (SSOT)

---

**아카이브 생성일:** 2026-01-31
**원본 폴더:** `docs/tasks/finished/phases_no1/`
