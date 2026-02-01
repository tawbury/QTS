# QTS Next-Gen Phase Tasks

본 폴더는 **Next-Gen Roadmap v2.0.0** 기반의 Phase Task 문서를 관리합니다.

## 폴더 구조

```
phases/
├── README.md (본 파일)
├── NG-0_E2E_Stabilization/      # E2E Testing & Stabilization
├── NG-1_Event_Priority/         # Event Priority System (17번)
├── NG-2_Micro_Risk_Loop/        # Micro Risk Loop (16번)
├── NG-3_Data_Layer/             # Data Layer Migration (18-2번)
├── NG-4_Caching/                # Caching Layer (19번)
├── NG-5_Capital_Flow/           # Capital Flow Engine (14번)
├── NG-6_Scalp_Execution/        # Scalp Execution Micro-Pipeline (15번)
├── NG-7_System_State/           # System State Promotion (18-1번)
└── NG-8_Feedback_Loop/          # Feedback Loop (20번)
```

## Phase 진행 순서

```
NG-0 (Foundation)
    ↓
┌───┴───┐
↓       ↓
NG-1    NG-3 (병렬 경로)
↓       ↓
NG-2    NG-4
↓       ↓
└───┬───┘
    ↓
NG-5 → NG-7 (Capital/State 경로)
    ↓
NG-6 (NG-1, NG-4 완료 후)
    ↓
NG-8 (마지막)
```

## Phase 상태 범례

- 🟡 진행 예정 (Pending)
- 🔵 진행 중 (In Progress)
- ✅ 완료 (Completed)
- ⏸️ 보류 (On Hold)

## 현재 상태

| Phase | 이름 | 상태 | 의존성 |
|-------|------|------|--------|
| NG-0 | E2E Testing & Stabilization | 🟡 | - |
| NG-1 | Event Priority System | 🟡 | NG-0 |
| NG-2 | Micro Risk Loop | 🟡 | NG-1 |
| NG-3 | Data Layer Migration | 🟡 | NG-0 |
| NG-4 | Caching Layer | 🟡 | NG-3 |
| NG-5 | Capital Flow Engine | 🟡 | NG-3, NG-7 |
| NG-6 | Scalp Execution Micro-Pipeline | 🟡 | NG-1, NG-4 |
| NG-7 | System State Promotion | 🟡 | NG-5 |
| NG-8 | Feedback Loop | 🟡 | NG-3, NG-6 |

## 참조 문서

- **Roadmap**: `docs/Roadmap.md` — Next-Gen Roadmap v2.0.0
- **아키텍처**: `docs/arch/sub/14~20_*.md`
- **레거시 Phase**: `docs/tasks/finished/phases_no1/`, `phases_no2/`

---

**최종 갱신:** 2026-01-31
