# Phase 4 — Engine Layer (로드맵 기준 Task)

## 목표

- **데이터 레이어/리포지토리/매니저와 Engine 간 인터페이스 정합성** 유지
- 엔진 테스트 코드가 **현재 생성자 시그니처/공개 API**와 일치하도록 수정
- Phase 10 Exit Criteria 충족 시 Roadmap 상태 ✅ 전환

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — Phase 4, Section 3 (다음 우선순위)
- [Phase Exit Criteria](../../../tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md) §4.1
- 코드: `src/runtime/engines/portfolio_engine.py`, `performance_engine.py`, `strategy_engine.py`
- 아키텍처: `docs/arch/02_Engine_Core_Architecture.md`, `docs/arch/04_Data_Contract_Spec.md`

---

## Roadmap Section 2 — Phase 4 업무

| 업무 | 상태 | 완료 시 |
|------|------|--------|
| Portfolio Engine | 🟡 | 테스트·wiring 정합 |
| Performance Engine | 🟡 | 동일 |
| Strategy Engine | 🟡 | 동일 |

---

## 작업 (체크리스트)

- [ ] **엔진–호출부 정합성**
  - [ ] Engine 생성자/메서드 시그니처와 테스트·Runner 호출이 일치
  - [ ] I/O Contract(execute 입력/출력)가 ETEDA Evaluate/Decide/Act와 정합
- [ ] **테스트**
  - [ ] `tests/engines/`, `tests/runtime/strategy/`, `tests/runtime/risk/` 등이 현재 엔진 인터페이스 기준으로 통과
  - [ ] Mock/픽스처가 실제 공개 API에 맞게 수정됨
- [ ] **문서**
  - [ ] 엔진 진입점/wiring 문서화
  - [ ] Roadmap Phase 4 비고(“테스트–생성자 불일치”) 해소

---

## 완료 조건 (Exit Criteria)

- [ ] 필수 테스트 통과 (§2.1)
- [ ] 해당 Phase 운영 체크(엔진만 해당 시 제한적) (§2.2)
- [ ] 문서 SSOT 반영 (§2.3)
