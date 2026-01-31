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
| Portfolio Engine | ✅ | 테스트·wiring 정합 (tests/engines, src/runtime/engines/README.md) |
| Performance Engine | ✅ | 동일 |
| Strategy Engine | ✅ | 동일 |

---

## Wiring 요약 (현행)

| 컴포넌트 | 생성자/진입점 | 비고 |
|----------|----------------|------|
| BaseEngine | `(config: UnifiedConfig)` | 공통: state, metrics, initialize/start/stop/execute |
| PortfolioEngine | `(config, position_repo, portfolio_repo, t_ledger_repo)` | ETEDARunner에서 리포지토리 주입. execute → 포지션/요약 |
| PerformanceEngine | `(config, history_repo, performance_repo)` | ETEDARunner에서 리포지토리 주입. execute → 성과/KPI |
| StrategyEngine | `(config: UnifiedConfig)` | ETEDARunner에서 config만 주입. execute(data) → operation=calculate_signal 등 |
| ETEDA 연동 | `ETEDARunner.__init__` → 엔진 생성 후 Evaluate/Decide 단계에서 호출 | Evaluate: portfolio/performance/strategy execute; Decide: 의사결정 입력 조합 |

---

## 미결 사항

| 미결 항목 | 진행 단계 | 비고 |
|-----------|-----------|------|
| Engine–호출부 시그니처 정합 | ✅ 완료 | ETEDARunner·tests/engines 생성자 일치 (config + repo 주입) |
| I/O Contract (execute 입출력) | ✅ 완료 | execute → {success, data|error, execution_time}. src/runtime/engines/README.md §3 |
| tests/engines·runtime/strategy·risk 통과 | ✅ 완료 | 79 passed. test_portfolio_engine, test_performance_engine, test_base_engine, test_trading_engine, strategy, risk |
| 엔진 진입점/wiring 문서화 | ✅ 완료 | src/runtime/engines/README.md (생성자·ETEDA 연동·execute I/O) |
| Roadmap Phase 4 비고 해소 | ✅ 완료 | 테스트–생성자 정합·Exit Criteria §2.1·§2.3 충족 |

---

## 작업 (체크리스트)

- [x] **엔진–호출부 정합성**
  - [x] Engine 생성자/메서드 시그니처와 테스트·Runner 호출 일치 (PortfolioEngine/PerformanceEngine/StrategyEngine/TradingEngine)
  - [x] I/O Contract(execute 입력/출력)가 ETEDA Evaluate/Decide/Act와 정합 (README §3)
- [x] **테스트**
  - [x] `tests/engines/`, `tests/runtime/strategy/`, `tests/runtime/risk/` 현재 엔진 인터페이스 기준 통과 (79 passed)
  - [x] Mock/픽스처가 실제 공개 API에 맞음 (position_repo, portfolio_repo, history_repo, performance_repo, broker)
- [x] **문서**
  - [x] 엔진 진입점/wiring 문서화 (src/runtime/engines/README.md)
  - [x] Roadmap Phase 4 비고(“테스트–생성자 불일치”) 해소

---

## 완료 조건 (Exit Criteria)

- [x] 필수 테스트 통과 (§2.1) — `pytest tests/engines/ tests/runtime/strategy/ tests/runtime/risk/ -v -m "not live_sheets and not real_broker"`
- [x] 해당 Phase 운영 체크(엔진만 해당 시 제한적) (§2.2) — 엔진은 상태/메트릭·health_check 제공. 실거래는 Broker Phase
- [x] 문서 SSOT 반영 (§2.3) — 02_Engine_Core_Architecture, engines/README.md wiring·execute I/O
