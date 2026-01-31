# Phase 5 — Execution Pipeline (ETEDA) (로드맵 기준 Task)

## 목표

- **데이터 레이어/리포지토리/매니저/Runner 간 인터페이스 정합성 확보** (Runner 중심)
- **ETEDA Runner의 리포지토리 생성/의존성 주입 정합성** 확보 (스프레드시트 ID 등)
- Phase 10 Exit Criteria 충족 시 Roadmap 상태 ✅ 전환

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — Phase 5, Section 3 (다음 우선순위)
- [Phase Exit Criteria](../../../tasks/finished/phases/Phase_10_Test_Governance/Phase_Exit_Criteria.md) §4.1
- 코드: `src/runtime/pipeline/eteda_runner.py`, `src/runtime/execution_loop/`, `src/ops/decision_pipeline/`
- 아키텍처: `docs/arch/sub/15_Scalp_Execution_Micro_Architecture.md`, `docs/arch/sub/17_Event_Priority_Architecture.md`, `docs/arch/sub/18_System_State_Promotion_Architecture.md`

---

## Roadmap Section 2 — Phase 5 업무

| 업무 | 상태 | 완료 시 |
|------|------|--------|
| ETEDA Runner(런타임) | 🟡 | 리포지토리 생성/DI 정합 |
| 실행 루프/제어 | 🟡 | 문서·코드 일치 |
| Ops Decision Pipeline | 🟡 | 동일 |

---

## 작업 (체크리스트)

- [ ] **Runner wiring 정합성**
  - [ ] ETEDA Runner가 사용하는 리포지토리 생성자 호출(스프레드시트 ID, 시트명 등)을 문서·코드로 정리
  - [ ] 의존성 주입 경로 단일화 또는 명시적 문서화
- [ ] **테스트**
  - [ ] `tests/runtime/execution_loop/`, `tests/runtime/execution/`, `tests/runtime/integration/` 등이 현재 Runner 인터페이스와 일치하고 통과
- [ ] **문서**
  - [ ] Runner 진입점·wiring·설정 경로 문서화
  - [ ] Roadmap Phase 5 비고(“Runner–리포지토리 생성자 불일치”) 해소

---

## 완료 조건 (Exit Criteria)

- [ ] 필수 테스트 통과 (§2.1)
- [ ] 파이프라인 실패/복구 운영 체크 문서화 (§2.2)
- [ ] 문서 SSOT 반영 (§2.3)
