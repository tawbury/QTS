# src/pipeline — ETEDA Pipeline

Runner·실행 루프·설정 경로 정리. **근거**: [03_Pipeline_ETEDA_Architecture.md](../../../docs/arch/03_Pipeline_ETEDA_Architecture.md), [15_Scalp_Execution_Micro_Architecture.md](../../../docs/arch/sub/15_Scalp_Execution_Micro_Architecture.md)

---

## 1. ETEDARunner 진입점·의존성 주입

| 항목 | 내용 |
|------|------|
| **경로** | `src/pipeline/eteda_runner.py` |
| **생성자** | `ETEDARunner(config, *, sheets_client=None, project_root=None, broker=None, safety_hook=None)` |
| **config** | 필수. UnifiedConfig. 아래 Config 키 사용(env fallback 가능). |
| **sheets_client** | 선택. None이면 config/env로 `GoogleSheetsClient(credentials_path, spreadsheet_id)` 생성. |
| **project_root** | 선택. None이면 `shared.paths.project_root()` 또는 cwd. |
| **broker** | 선택. BrokerEngine. 주입 시 Act 단계에서 submit_intent → ExecutionResponse. |
| **safety_hook** | 선택. PipelineSafetyHook. 주입 시 run_once 시작 전 should_run(), Act 실패 시 record_fail_safe(). |

**리포지토리 생성 (Runner 내부 단일 경로)**  
`sid = client.spreadsheet_id` 기준으로:  
`PositionRepository(client, sid)`, `EnhancedPortfolioRepository(client, sid, project_root)`, `T_LedgerRepository(client, sid)`, `HistoryRepository(client, sid)`, `EnhancedPerformanceRepository(client, sid, project_root)`.  
시트명은 리포지토리 클래스 고정(Position, Portfolio 등).

**엔진 주입**  
Phase 4 시그니처와 동일: PortfolioEngine(config, position_repo, portfolio_repo, t_ledger_repo), PerformanceEngine(config, history_repo, performance_repo), StrategyEngine(config).

---

## 2. Config 키 (Runner·루프)

| 키 | 용도 | 기본/비고 |
|----|------|-----------|
| **SPREADSHEET_ID** | Google 스프레드시트 ID | env `GOOGLE_SHEET_KEY` fallback. sheets_client 미주입 시 사용. |
| **CREDENTIALS_PATH** | Google 서비스 계정 키 경로 | env `GOOGLE_CREDENTIALS_FILE` fallback. |
| **RUN_MODE** | 실행 모드 | execution_mode.decide_execution_mode 참조. |
| **LIVE_ENABLED** | 실거래 허용 여부 | Phase E Runner 엔진 선택 시 사용. |
| **PIPELINE_PAUSED** | 루프 중단 플래그 | "1"/"true" 등 truthy 시 run_eteda_loop 즉시 탈출. |
| **INTERVAL_MS** | run_once 주기(ms) | 기본 1000. eteda_loop_policy.ETEDALoopPolicy.from_config. |
| **ERROR_BACKOFF_MS** | run_once 예외 후 대기(ms) | 기본 5000. |
| **ERROR_BACKOFF_MAX_RETRIES** | 연속 예외 허용 횟수 | 초과 시 루프 중단. 기본 3. |

---

## 3. 실행 루프

| 항목 | 내용 |
|------|------|
| **진입점** | `run_eteda_loop(runner, config, policy=None, should_stop=None, snapshot_source=None)` |
| **경로** | `src/pipeline/loop/eteda_loop.py` |
| **Runner 계약** | `run_once(snapshot: Dict[str, Any]) -> Dict[str, Any]` 만 있으면 됨 (ETEDARunnerLike). |
| **정책** | `ETEDALoopPolicy.from_config(config)` — INTERVAL_MS, ERROR_BACKOFF_MS, ERROR_BACKOFF_MAX_RETRIES. |
| **중단** | `should_stop` 없으면 Config PIPELINE_PAUSED로 생성. truthy 시 즉시 루프 탈출. |

---

## 4. Ops Decision Pipeline

| 항목 | 내용 |
|------|------|
| **진입점** | `DecisionPipelineRunner()` 무인자 → `run(context, strategy_name=None)` |
| **경로** | `src/decision_pipeline/` (Extract→Transform→Evaluate→Decide, Act 없음) |
| **비고** | 런타임 ETEDARunner와 별도 진입점. |

---

## 5. 테스트 경로

- `tests/runtime/execution_loop/` — run_eteda_loop, policy, phase4 loop 통합
- `tests/runtime/execution/` — intent flow, consecutive failure failsafe
- `tests/runtime/integration/` — phase5 strategy/risk loop, phaseE runner 엔진 선택

기본 실행: `pytest tests/runtime/execution_loop/ tests/runtime/execution/ tests/runtime/integration/ -v -m "not live_sheets and not real_broker"`
