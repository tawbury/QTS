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
| ETEDA Runner(런타임) | ✅ | 리포지토리 생성/DI 정합 (src/runtime/pipeline/README.md) |
| 실행 루프/제어 | ✅ | 문서·코드 일치 (run_eteda_loop, ETEDALoopPolicy, Config 키) |
| Ops Decision Pipeline | ✅ | 진입점·wiring 문서화 (pipeline README §4) |

---

## Wiring 요약 (현행)

| 컴포넌트 | 진입점 | 비고 |
|----------|--------|------|
| ETEDARunner | `(config, *, sheets_client=None, project_root=None, broker=None, safety_hook=None)` | sheets_client 없으면 config/env로 `GoogleSheetsClient(credentials_path, spreadsheet_id)` 생성. sid = client.spreadsheet_id |
| 리포지토리 생성 | Runner 내부: `PositionRepository(client, sid)`, `EnhancedPortfolioRepository(client, sid, project_root)`, `T_LedgerRepository(client, sid)`, `HistoryRepository(client, sid)`, `EnhancedPerformanceRepository(client, sid, project_root)` | 시트명은 리포지토리 클래스 고정(Position, R_Dash 등). 단일 경로: client + sid + project_root(Enhanced만) |
| 엔진 주입 | Runner 내부: PortfolioEngine(config, position_repo, portfolio_repo, t_ledger_repo), PerformanceEngine(config, history_repo, performance_repo), StrategyEngine(config) | Phase 4 시그니처와 동일 |
| 실행 루프 | `run_eteda_loop(runner: ETEDARunnerLike, config, policy=None, should_stop=None, snapshot_source=None)` | runner는 `run_once(snapshot)`만 필요. Config: INTERVAL_MS, PIPELINE_PAUSED, ERROR_BACKOFF_* |
| Ops Decision Pipeline | `DecisionPipelineRunner()` 무인자 → `run(context, strategy_name=None)` | Extract→Transform→Evaluate→Decide(Act 없음). 런타임 ETEDARunner와 별도 진입점 |

---

## 미결 사항

| 미결 항목 | 진행 단계 | 비고 |
|-----------|-----------|------|
| Runner–리포지토리 생성자 정합 | ✅ 완료 | 스프레드시트 ID·시트명 단일 경로(client, sid, repo 클래스). pipeline/README.md §1 |
| 의존성 주입 경로 문서화 | ✅ 완료 | config/sheets_client/project_root/broker/safety_hook. pipeline/README.md §1, §2 |
| tests/execution_loop·execution·integration | ✅ 완료 | 15 passed. ETEDARunnerLike·LiveBroker intent_id 계약 정합 |
| Runner 진입점·설정 경로 문서화 | ✅ 완료 | SPREADSHEET_ID, CREDENTIALS_PATH, RUN_MODE, LIVE_ENABLED, PIPELINE_PAUSED, INTERVAL_MS, ERROR_BACKOFF_* — pipeline/README.md §2 |
| Roadmap Phase 5 비고 해소 | ✅ 완료 | Runner–리포지토리 정합·Exit Criteria §2.1·§2.2·§2.3 충족 |

---

## 작업 (체크리스트)

- [x] **Runner wiring 정합성**
  - [x] ETEDA Runner 리포지토리 생성자 호출(스프레드시트 ID, 시트명) 문서·코드 정리 (pipeline/README.md §1)
  - [x] 의존성 주입 경로 명시적 문서화 (config, sheets_client, project_root, broker, safety_hook)
- [x] **테스트**
  - [x] `tests/runtime/execution_loop/`, `tests/runtime/execution/`, `tests/runtime/integration/` 현재 Runner 인터페이스와 일치·통과 (15 passed)
- [x] **문서**
  - [x] Runner 진입점·wiring·설정 경로 문서화 (src/runtime/pipeline/README.md)
  - [x] Roadmap Phase 5 비고(“Runner–리포지토리 생성자 불일치”) 해소

---

## 완료 조건 (Exit Criteria)

- [x] 필수 테스트 통과 (§2.1) — `pytest tests/runtime/execution_loop/ tests/runtime/execution/ tests/runtime/integration/ -v -m "not live_sheets and not real_broker"`
- [x] 파이프라인 실패/복구 운영 체크 문서화 (§2.2) — [ETEDA_파이프라인_운영_체크.md](./ETEDA_파이프라인_운영_체크.md)
- [x] 문서 SSOT 반영 (§2.3) — 03_Pipeline_ETEDA, pipeline/README.md, 운영 체크 문서
