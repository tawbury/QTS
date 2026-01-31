# Phase 9 — Ops & Automation (로드맵 기준 Task)

## 목표

- **Ops 스케줄링(automation) 구현 범위 확정 및 최소 기능 구현**
- Backup/Maintenance/Retention과 스케줄러/트리거 경로 정합
- Phase 10 Exit Criteria 충족 시 Roadmap 상태 ✅ 전환

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — Phase 9, Section 3 (다음 우선순위)
- [Phase Exit Criteria](../../../tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md) §4.2
- 코드: `src/ops/backup/`, `src/ops/maintenance/`, `src/ops/retention/`, `src/ops/automation/` (현재 비어 있음)
- 아키텍처: `docs/arch/09_Ops_Automation_Architecture.md`

---

## Roadmap Section 2 — Phase 9 업무

| 업무 | 상태 | 완료 시 |
|------|------|--------|
| Backup / Maintenance / Retention | 🟡 | 테스트·문서 정합 |
| Ops 자동화(스케줄러/트리거) | 🟡 | 최소 기능 범위 확정 후 구현 |

---

## 작업 (체크리스트)

- [ ] **스케줄링 범위 확정**
  - [ ] Ops 스케줄링(automation) “최소 구현 범위”를 문서로 확정
  - [ ] `src/ops/automation/` 에 최소 스케줄러/트리거 진입점 구현 또는 기존 경로 명시
- [ ] **테스트**
  - [ ] `tests/ops/automation/`, `tests/ops/maintenance/` 등이 현재 인터페이스와 일치하고 통과
- [ ] **문서**
  - [ ] 백업/스케줄/알림 진입점·wiring 문서화
  - [ ] Roadmap Phase 9 비고(“automation 비어 있음”) 해소

---

## 완료 조건 (Exit Criteria)

- [ ] 필수 테스트 통과 (§2.1)
- [ ] 운영 체크(백업/스케줄/알림) (§2.2)
- [ ] 문서 SSOT 반영 (§2.3)
