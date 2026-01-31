# Phase 7 — Safety & Risk Core (로드맵 기준 Task)

## 목표

- Risk 구성요소·Ops Safety Guard·Lockdown/Fail-Safe 상태 머신의 **완전판 정의 및 검증**
- Phase 10 Exit Criteria 충족 시 Roadmap 상태 ✅ 전환

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — Phase 7
- [Phase Exit Criteria](../../../tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md) §4.3
- 코드: `src/runtime/risk/`, `src/ops/safety/guard.py`
- 아키텍처: `docs/arch/sub/16_Micro_Risk_Loop_Architecture.md`, `docs/arch/sub/18_System_State_Promotion_Architecture.md`

---

## Roadmap Section 2 — Phase 7 업무

| 업무 | 상태 | 완료 시 |
|------|------|--------|
| Risk 구성요소(계산기/게이트/정책) | 🟡 | 테스트·문서 정합 |
| Ops Safety Guard | 🟡 | 동일 |
| Lockdown/Fail-Safe 상태 머신(완전판) | 🟡 | 완전판 정의 후 검증 |

---

## 작업 (체크리스트)

- [ ] **상태 머신 완전판**
  - [ ] Lockdown/Fail-Safe 상태 머신 “완전판” 정의(문서·상태 전이·입출력)
  - [ ] 부분 구현과의 갭 정리 및 검증 테스트
- [ ] **테스트**
  - [ ] `tests/ops/safety/` 등 해당 테스트가 현재 인터페이스와 일치하고 통과
  - [ ] Fail-Safe/Lockdown 시나리오 문서화
- [ ] **문서**
  - [ ] Safety 진입점·wiring·상태 전이 문서화
  - [ ] Roadmap Phase 7 비고(“완전판 확인 필요”) 해소

---

## 완료 조건 (Exit Criteria)

- [ ] 필수 테스트 통과 (§2.1)
- [ ] 운영 체크(Fail-Safe/Lockdown) (§2.2)
- [ ] 문서 SSOT 반영 (§2.3)
