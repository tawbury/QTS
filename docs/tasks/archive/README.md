# QTS Task Archive

본 폴더는 **완료된 히스토리컬 Task 문서**를 보관합니다.

## 폴더 구조

```
archive/
├── README.md (본 파일)
├── historical/                       # 레거시 체크리스트 (백업 복사본)
│   ├── google_sheets_integration/    # Google Sheets 초기 통합 문서
│   ├── Phase_03_Config_Local/        # 260128_03_Config_Local_Legacy_Checklist.md
│   ├── Phase_04_Engine_Layer/        # 260128_04_Engine_Layer_Legacy_Checklist.md
│   ├── Phase_05_Pipeline/            # 260128_05_Pipeline_Legacy_Checklist.md
│   ├── Phase_06_Dashboard/           # 260128_06_Dashboard_Legacy_Checklist.md
│   ├── Phase_07_Safety_Risk/         # 260128_07_Safety_Risk_Legacy_Checklist.md
│   └── Phase_09_Ops_Automation/      # 260128_09_Ops_Automation_Legacy_Checklist.md
└── phases_no1_completed/             # Phase 1-10 완료 문서 전체 (57개 파일)
    ├── README.md                     # phases_no1 아카이브 설명
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

## 파일명 규칙

`[YYMMDD]_[TaskName]_[Status].md`

- **YYMMDD**: 문서 생성/완료일
- **TaskName**: 작업 내용 요약
- **Status**: `Completed`, `Legacy_Checklist`, `Archived`

## 아카이브 유형별 용도

### historical/ (레거시 체크리스트)
- **용도**: 초기 구현 과정의 간단한 체크리스트 백업
- **상태**: 대부분 Phase별 상세 문서로 대체됨
- **참조 가치**: 낮음 (히스토리 보존 목적)

### phases_no1_completed/ (Phase 1-10 완료 문서)
- **용도**: Phase 1~10 구현의 모든 상세 Task 문서 보관
- **상태**: 원본 파일명 유지, Git 히스토리 연결
- **참조 가치**: 높음 (정책, 계약, Exit Criteria 등 SSOT)
- **특이사항**: `Phase_10_Test_Governance/Phase_Exit_Criteria.md`는 현재도 참조됨

## 현행 문서 위치

- **Active Operational Docs**: `docs/tasks/phases/` — 현재 운영 중인 Phase Task
- **Roadmap**: `docs/Roadmap.md` — Next-Gen Roadmap v2.0.0
- **Exit Criteria (SSOT)**: `archive/phases_no1_completed/Phase_10_Test_Governance/Phase_Exit_Criteria.md`

---

**최종 갱신:** 2026-01-31
