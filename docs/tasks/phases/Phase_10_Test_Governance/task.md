# Phase 10 — Test & Governance (로드맵 기준 Task)

## 목표

- 테스트 폴더 구조/테스트 자산과 **거버넌스(Phase 종료 기준/검증 기준) 문서** 정합 유지
- Phase 10 Exit Criteria를 기준으로 다른 Phase의 ✅ 전환 판정 지원
- Phase 10 자체 Exit Criteria 충족 시 Roadmap 상태 ✅ 전환

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — Phase 10, Section 2·3
- [Phase Exit Criteria](../../../tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md) — **Single Source of Truth** for Phase 완료 판정
- 코드: `tests/`, `tests/contracts/`, `tests/fixtures/`
- 아키텍처: `docs/arch/10_Testability_Architecture.md`

---

## Roadmap Section 2 — Phase 10 업무

| 업무 | 상태 | 완료 시 |
|------|------|--------|
| 테스트 폴더 구조/테스트 자산 | 🟡 | Exit Criteria §2.1·§3 테스트 경로와 일치 |
| 거버넌스(Phase 종료 기준/검증 기준) 문서 | 🟡 | Roadmap에 명시·유지 (본 문서로 명시 완료) |

---

## 작업 (체크리스트)

- [ ] **테스트 구조**
  - [ ] `tests/` 구조가 [Test_Suite_Structure_and_Execution.md](../../../tasks/finished/phases/Phase_10_Test_Governance/Test_Suite_Structure_and_Execution.md) §1과 일치
  - [ ] 기본 실행: `pytest tests/ -v -m "not live_sheets and not real_broker"` (또는 Phase별 하위) 통과
- [ ] **Contract/픽스처**
  - [ ] [Fixtures_and_Contract_Policy.md](../../../tasks/finished/phases/Phase_10_Test_Governance/Fixtures_and_Contract_Policy.md) 정책에 따른 Contract 검증 테스트 유지
- [ ] **문서**
  - [ ] Phase Exit Criteria·Roadmap 상태 변경 절차가 최신 유지
  - [ ] Roadmap “거버넌스 문서 명시 필요” 비고 해소(본 Phase Exit Criteria 문서로 충족)

---

## 완료 조건 (Exit Criteria)

- [ ] 필수 테스트 통과 (§2.1) — Phase 10 테스트 경로 존재·통과
- [ ] 운영 체크 N/A (§2.2)
- [ ] 문서 SSOT 반영 (§2.3) — 10_Testability, Phase Exit Criteria, 본 task 문서

---

## 관련 문서

- [Phase_Exit_Criteria.md](../../../tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md) — Phase별 ✅ 판정 기준
- [Test_Suite_Structure_and_Execution.md](../../../tasks/finished/phases/Phase_10_Test_Governance/Test_Suite_Structure_and_Execution.md)
- [Fixtures_and_Contract_Policy.md](../../../tasks/finished/phases/Phase_10_Test_Governance/Fixtures_and_Contract_Policy.md)
