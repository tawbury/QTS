# Phase 6 — Dashboard / Visualization (로드맵 기준 Task)

## 목표

- **Dashboard(Zero-Formula UI) 구현 범위 확정 및 최소 렌더링 경로 정의**
- R_Dash 리포지토리와 Zero-Formula UI 렌더러/계약 빌더 경로를 문서·코드에서 명확히 하고 테스트 추가
- Phase 10 Exit Criteria 충족 시 Roadmap 상태 ✅ 전환

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — Phase 6, Section 3 (다음 우선순위)
- [Phase Exit Criteria](../../../tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md) §4.2
- 코드: `src/runtime/data/repositories/r_dash_repository.py`
- 아키텍처: UI Contract/렌더러 관련 문서 (`docs/tasks/finished/phases/Phase_06_UI_Dashboard/` 참조)

---

## Roadmap Section 2 — Phase 6 업무

| 업무 | 상태 | 완료 시 |
|------|------|--------|
| R_Dash 리포지토리 | 🟡 | wiring·테스트 정합 |
| Zero-Formula UI 렌더링/계약 빌더 | 🟡 | 전용 렌더러·계약 빌더 경로 정의 및 최소 구현 |

---

## 작업 (체크리스트)

- [ ] **구현 범위 확정**
  - [ ] Zero-Formula UI 렌더러·계약 빌더의 “최소 구현 범위”를 문서로 확정
  - [ ] 전용 렌더러/계약 빌더 경로를 코드베이스에서 명확히 하거나 신규 정의
- [ ] **테스트**
  - [ ] UI Contract/렌더러 관련 테스트 추가 또는 기존 테스트와 인터페이스 일치
  - [ ] UI 실패 시 매매 중단 아님 정책 문서화 (§2.2)
- [ ] **문서**
  - [ ] Dashboard 진입점·렌더링 경로·UI Contract 스키마 문서화
  - [ ] Roadmap Phase 6 비고(“전용 렌더러/계약 빌더 미확정”) 해소

---

## 완료 조건 (Exit Criteria)

- [ ] 필수 테스트 통과 (§2.1)
- [ ] 운영 체크(UI 실패 시 정책) (§2.2)
- [ ] 문서 SSOT 반영 (§2.3)
