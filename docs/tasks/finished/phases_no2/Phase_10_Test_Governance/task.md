# Phase 10 — Test & Governance (로드맵 기준 Task)

## 목표

- 테스트 폴더 구조/테스트 자산과 **거버넌스(Phase 종료 기준/검증 기준) 문서** 정합 유지
- Phase 10 Exit Criteria를 기준으로 다른 Phase의 ✅ 전환 판정 지원
- Phase 10 자체 Exit Criteria 충족 시 Roadmap 상태 ✅ 전환

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — Phase 10, Section 2·3
- [Phase Exit Criteria](../../finished/phases_no1/Phase_10_Test_Governance/Phase_Exit_Criteria.md) — **Single Source of Truth** for Phase 완료 판정
- 코드: `tests/`, `tests/contracts/`, `tests/fixtures/`
- 아키텍처: [docs/arch/10_Testability_Architecture.md](../../../arch/10_Testability_Architecture.md)

---

## Roadmap Section 2 — Phase 10 업무

| 업무 | 상태 | 완료 시 |
|------|------|--------|
| 테스트 폴더 구조/테스트 자산 | ✅ | Exit Criteria §2.1·§3 테스트 경로와 일치, 328 passed |
| 거버넌스(Phase 종료 기준/검증 기준) 문서 | ✅ | Phase_Exit_Criteria, Test_Suite_Structure, Fixtures_and_Contract_Policy |

---

## Wiring 요약 (현행)

| 컴포넌트 | 진입점 | 비고 |
|----------|--------|------|
| 테스트 구조 | `tests/`: api, config, contracts, engines, fixtures, google_sheets_integration, ops (automation, decision, maintenance, safety), runtime (broker, config, data, execution, execution_loop, integration, monitoring, risk, schema_auto, strategy) | Phase별 대응 경로: Exit Criteria §3 참조 |
| pytest 마커 | `conftest.pytest_configure`: `live_sheets`, `real_broker` | 기본 실행: `pytest tests/ -v -m "not live_sheets and not real_broker"`. real_broker: opt-in (`-m real_broker`) |
| Contract/픽스처 | `tests/contracts/test_contract_validation.py`, `tests/fixtures/contracts.py` | ExecutionIntent/ExecutionResponse, UI Contract, OrderDecision, ExecutionHint 필드 검증. Fixtures_and_Contract_Policy 정책 |
| Exit Criteria SSOT | `Phase_Exit_Criteria.md` (finished/phases_no1/Phase_10_Test_Governance/) | §2.1 필수 테스트, §2.2 운영 체크, §2.3 문서 SSOT. Phase별 ✅ 판정 기준 |
| 테스트 구조·실행 문서 | `Test_Suite_Structure_and_Execution.md`, `Fixtures_and_Contract_Policy.md` | §1 테스트 계층 매핑, §2 마커/opt-in. Contract 검증 정책 |

---

## 미결 사항

| 미결 항목 | 진행 단계 | 비고 |
|-----------|-----------|------|
| tests/ 구조와 Test_Suite_Structure §1 일치 | ✅ 반영 | api, config, contracts, engines, fixtures, google_sheets_integration, ops, runtime 등 존재. §1 경로 매핑 정합 |
| 기본 실행(not live_sheets, not real_broker) 통과 | ✅ 반영 | 328 passed, 3 skipped(api), 7 deselected. api/conftest QTS_API_TEST skip을 tests/api/로 제한 |
| Contract/픽스처 정책과 검증 테스트 유지 | ✅ 반영 | test_contract_validation, fixtures/contracts.py. Fixtures_and_Contract_Policy 정책 반영 |
| Phase Exit Criteria·Roadmap 상태 변경 절차 최신 유지 | ✅ 반영 | Phase_Exit_Criteria.md SSOT. Roadmap Phase별 비고 해소 시 ✅ 전환 절차 §5 |
| Roadmap “거버넌스 문서 명시 필요” 비고 해소 | ✅ 반영 | Phase_Exit_Criteria·Test_Suite_Structure·Fixtures_and_Contract_Policy로 명시 완료 |

---

## 작업 (체크리스트)

- [x] **테스트 구조**
  - [x] `tests/` 구조가 [Test_Suite_Structure_and_Execution.md](../../finished/phases_no1/Phase_10_Test_Governance/Test_Suite_Structure_and_Execution.md) §1과 일치
  - [x] 기본 실행: `pytest tests/ -v -m "not live_sheets and not real_broker"` 통과 — 328 passed
- [x] **Contract/픽스처**
  - [x] [Fixtures_and_Contract_Policy.md](../../finished/phases_no1/Phase_10_Test_Governance/Fixtures_and_Contract_Policy.md) 정책에 따른 Contract 검증 테스트 유지
- [x] **문서**
  - [x] Phase Exit Criteria·Roadmap 상태 변경 절차가 최신 유지
  - [x] Roadmap “거버넌스 문서 명시 필요” 비고 해소(본 Phase Exit Criteria 문서로 충족)

---

## 완료 조건 (Exit Criteria)

- [x] 필수 테스트 통과 (§2.1) — tests/contracts, tests/fixtures, 328 passed (전체 기본 실행)
- [x] 운영 체크 N/A (§2.2)
- [x] 문서 SSOT 반영 (§2.3) — 10_Testability, Phase Exit Criteria, 본 task 문서

---

## 관련 문서

- [Phase_Exit_Criteria.md](../../finished/phases_no1/Phase_10_Test_Governance/Phase_Exit_Criteria.md) — Phase별 ✅ 판정 기준 (SSOT)
- [Test_Suite_Structure_and_Execution.md](../../finished/phases_no1/Phase_10_Test_Governance/Test_Suite_Structure_and_Execution.md) — 테스트 계층·실행·마커
- [Fixtures_and_Contract_Policy.md](../../finished/phases_no1/Phase_10_Test_Governance/Fixtures_and_Contract_Policy.md) — Contract/픽스처 정책
