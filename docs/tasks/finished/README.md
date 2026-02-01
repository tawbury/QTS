# QTS Finished Tasks

본 폴더는 **완료된 Phase Task 문서**들을 시간순으로 보관합니다.

## 폴더 구조

```
finished/
├── README.md (본 파일)
├── phases_no1/              # Phase 1-10 초기 완료본 (2026-01-26 ~ 2026-01-29)
│   ├── Phase_00_Observer/
│   ├── Phase_01_Schema_Sheet_Mapping/
│   ├── Phase_02_Config_Sheet/
│   ├── Phase_03_Config_Local/
│   ├── Phase_04_Engine_Layer/
│   ├── Phase_05_ETEDA_Pipeline/
│   ├── Phase_06_UI_Dashboard/
│   ├── Phase_07_Safety_Risk/
│   ├── Phase_08_Broker_Integration/
│   ├── Phase_09_Ops_Automation/
│   └── Phase_10_Test_Governance/
└── phases_no2/              # Phase 1-10 로드맵 정리본 (2026-01-31)
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

## 버전별 설명

### phases_no1 (초기 완료본)
- **기간**: 2026-01-26 ~ 2026-01-29 (4일간 집중 구현)
- **내용**: Phase 1~10 구현 과정의 모든 Task 문서 (57개 파일)
- **특징**:
  - 정책 문서: Act Stage Policy, R_Dash Update Policy, Dashboard Delivery Channel Policy
  - 계약 문서: Google Sheets Contract, Act I/O Contract
  - Exit Criteria: Phase 완료 판정 기준 (SSOT)
  - 시나리오: Baseline/Simulation Stress Execution
- **참조 가치**: 높음 (Exit Criteria, Policy, Contract는 현재도 참조됨)

### phases_no2 (로드맵 정리본)
- **기간**: 2026-01-31
- **내용**: Phase 1~10의 로드맵 기준 Task 문서
- **특징**:
  - Roadmap Section 2 기반 업무 현황 정리
  - Wiring 요약 (컴포넌트별 진입점/의존성)
  - 미결 사항 및 완료 조건 명시
  - 운영 체크 문서 통합 (Config Sheet, ETEDA, FailSafe, Broker, Ops)
- **참조 가치**: 중간 (운영 체크리스트로 활용 가능)

## 문서 진화 타임라인

```
2026-01-26 ~ 01-29: Phase 1-10 구현 완료 (phases_no1)
          ↓
2026-01-31: 로드맵 기준 Task 정리 (phases_no2)
          ↓
2026-01-31: Next-Gen Roadmap v2.0.0 (NG-0 ~ NG-8)
```

## 현행 문서 위치

- **Next-Gen Roadmap**: `docs/Roadmap.md` v2.0.0
- **아카이브**: `docs/tasks/archive/` (레거시 체크리스트, phases_no1 복사본)
- **Exit Criteria (SSOT)**: `finished/phases_no1/Phase_10_Test_Governance/Phase_Exit_Criteria.md`

## 참조 우선순위

1. **Exit Criteria 참조**: `phases_no1/Phase_10_Test_Governance/Phase_Exit_Criteria.md`
2. **정책/계약 참조**: `phases_no1/Phase_XX/` (Policy, Contract 문서)
3. **운영 체크리스트**: `phases_no2/Phase_XX/` (운영_체크.md 파일)
4. **구현 기록**: `phases_no1/Phase_XX/task_XX_*.md` (Task별 세부 기록)

---

**최종 갱신:** 2026-01-31
