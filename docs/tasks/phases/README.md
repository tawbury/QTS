# QTS Phase Tasks (로드맵 기준)

**기준 문서:** [docs/Roadmap.md](../../Roadmap.md)  
**종료 기준:** [Phase_10_Test_Governance/Phase_Exit_Criteria.md](Phase_10_Test_Governance/Phase_Exit_Criteria.md) (finished 보관본 참조: `docs/tasks/finished/phases/Phase_10_Test_Governance/`)

본 폴더는 **로드맵 기준 구현·정합성 확보**를 위한 Phase별 Task 문서를 담는다.  
이전 Task 문서(정리 완료)는 `docs/tasks/finished/phases/` 에 보관되어 있다.

---

## Phase 인덱스

| Phase | 폴더 | Roadmap 상태 | Task 문서 |
|-------|------|--------------|-----------|
| 0 | Phase_00_Observer | ↗️ 분리 | [task.md](Phase_00_Observer/task.md) |
| 1 | Phase_01_Schema_Sheet_Mapping | 🟡 부분 구현 | [task.md](Phase_01_Schema_Sheet_Mapping/task.md) |
| 2 | Phase_02_Config_Sheet | 🟡 부분 구현 | [task.md](Phase_02_Config_Sheet/task.md) |
| 3 | Phase_03_Config_Local | ✅ 구현 완료 | [task.md](Phase_03_Config_Local/task.md) |
| 4 | Phase_04_Engine_Layer | 🟡 부분 구현 | [task.md](Phase_04_Engine_Layer/task.md) |
| 5 | Phase_05_ETEDA_Pipeline | 🟡 부분 구현 | [task.md](Phase_05_ETEDA_Pipeline/task.md) |
| 6 | Phase_06_UI_Dashboard | 🟡 부분 구현 | [task.md](Phase_06_UI_Dashboard/task.md) |
| 7 | Phase_07_Safety_Risk | 🟡 부분 구현 | [task.md](Phase_07_Safety_Risk/task.md) |
| 8 | Phase_08_Broker_Integration | 🟡 부분 구현 | [task.md](Phase_08_Broker_Integration/task.md) |
| 9 | Phase_09_Ops_Automation | 🟡 부분 구현 | [task.md](Phase_09_Ops_Automation/task.md) |
| 10 | Phase_10_Test_Governance | 🟡 부분 구현 | [task.md](Phase_10_Test_Governance/task.md) |

---

## Roadmap 다음 우선순위 (Section 3) — Phase 매핑

| 우선순위 업무 | 해당 Phase |
|---------------|------------|
| 데이터 레이어/리포지토리/매니저/Runner 간 인터페이스 정합성 확보 | 1, 4, 5 |
| Config Sheet 로딩 경로를 현재 GoogleSheetsClient 인터페이스에 맞게 정리 | 2 |
| ETEDA Runner의 리포지토리 생성/의존성 주입 정합성 확보 | 5 |
| Ops 스케줄링(automation) 구현 범위 확정 및 최소 기능 구현 | 9 |
| Dashboard(Zero-Formula UI) 구현 범위 확정 및 최소 렌더링 경로 정의 | 6 |

---

## 관련 문서

- [Roadmap.md](../../Roadmap.md) — Phase별 상태, 판정 기준, 다음 우선순위
- [docs/arch/sub/](../../arch/sub/) — 아키텍처 정렬 문서 (14~20)
- [docs/tasks/finished/phases/](../finished/phases/) — 정리 완료된 이전 Task 문서
