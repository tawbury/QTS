# QTS Tasks 문서 체계

본 폴더는 QTS 프로젝트의 **모든 Task 관련 문서**를 관리합니다.

## 폴더 구조

```
tasks/
├── README.md (본 파일)
├── finished/                 # 완료된 Phase Task 문서
│   ├── README.md
│   ├── phases_no1/          # Phase 1-10 초기 완료본 (2026-01-26~29)
│   └── phases_no2/          # Phase 1-10 로드맵 정리본 (2026-01-31)
├── archive/                 # 히스토리컬 아카이브
│   ├── README.md
│   ├── historical/          # 레거시 체크리스트 (날짜 기반 리네이밍)
│   └── phases_no1_completed/ # phases_no1 백업 복사본
└── backups/                 # (삭제 예정) 초기 백업 폴더
```

## 폴더별 용도

### finished/ (완료된 Task)
- **용도**: 완료된 Phase Task의 시간순 버전 관리
- **상태**: 원본 파일명 유지, Git 히스토리 연결
- **참조 가치**: 높음
- **주요 문서**:
  - Exit Criteria (SSOT)
  - Policy 문서 (Act Stage, R_Dash, Dashboard Delivery)
  - Contract 문서 (Google Sheets, Act I/O)
  - 운영 체크 문서

### archive/ (아카이브)
- **용도**: 히스토리 보존 및 백업
- **상태**: 수정 금지, 참조 전용
- **참조 가치**: 중간~낮음
- **하위 폴더**:
  - `historical/`: 레거시 체크리스트 (날짜 기반 리네이밍)
  - `phases_no1_completed/`: phases_no1의 백업 복사본

### backups/ (삭제 예정)
- **상태**: `archive/historical/`로 이미 이동됨
- **조치**: 향후 삭제 가능

## 문서 참조 가이드

### 1. Phase 완료 기준 확인
→ `finished/phases_no1/Phase_10_Test_Governance/Phase_Exit_Criteria.md` (SSOT)

### 2. 정책/계약 문서 참조
→ `finished/phases_no1/Phase_XX/` (Policy, Contract 파일)

### 3. 운영 체크리스트
→ `finished/phases_no2/Phase_XX/` (운영_체크.md 파일)

### 4. 구현 세부 기록
→ `finished/phases_no1/Phase_XX/task_XX_*.md`

## 현행 개발 문서

- **Roadmap**: `docs/Roadmap.md` — Next-Gen Roadmap v2.0.0 (NG-0 ~ NG-8)
- **Architecture**: `docs/arch/` — 아키텍처 문서
- **Reports**: `docs/reports/` — 분석 보고서

## 문서 진화 타임라인

```
2026-01-26~29: Phase 1-10 구현 완료 (phases_no1)
         ↓
2026-01-31: 로드맵 기준 Task 정리 (phases_no2)
         ↓
2026-01-31: Next-Gen Roadmap v2.0.0
         ↓
2026-01-31: 문서 아카이빙 및 체계화
```

## 폴더 정리 이력

| 날짜 | 작업 | 비고 |
|------|------|------|
| 2026-01-31 | `backups/` → `archive/historical/` 이동 | 날짜 기반 리네이밍 |
| 2026-01-31 | `finished/phases_no1/` → `archive/phases_no1_completed/` 복사 | 백업 목적 |
| 2026-01-31 | `phases/` → `finished/phases_no2/` 이동 | 버전 관리 |

---

**최종 갱신:** 2026-01-31
**관리 원칙**: 완료된 문서는 finished/로, 오래된 백업은 archive/로
