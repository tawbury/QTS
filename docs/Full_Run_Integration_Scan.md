# 전체 구동 검수 보고서 (Full Run Integration Scan)

**검수 일자**: 2026-02-01  
**목적**: main.py 진입점 기준 전체 구동 테스트 가능 여부 및 모듈 간 연결 상태 검수.

---

## 1. 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| **main.py 진입점** | ✅ 추가됨 | 프로젝트 루트 `main.py`. `--local-only` 시 Config_Local + NoopBroker |
| **ETEDA Runner ↔ 루프** | ✅ 연결됨 | `run_eteda_loop(runner, config)` ↔ `ETEDARunner.run_once(snapshot)` |
| **Config 로딩** | ✅ 연결됨 | main.py에서 `load_local_only_config`/`load_unified_config` 호출. get_flat 계층 키 fallback 반영 |
| **Broker 주입** | ⚠️ 부분 | Runner는 `BrokerEngine` 주입 받음. 어댑터→브릿지→`create_broker_for_execution` 연동은 문서/테스트에만 존재 |
| **Safety Hook** | ⚠️ 부분 | `SafetyLayer` 구현·Runner 주입 계약 있음. 진입점에서 생성·주입 없음 |
| **Intent ↔ Order 브릿지** | ✅ 연결됨 | `OrderAdapterToBrokerEngineAdapter`가 Act 경로에서 사용됨(LiveBroker 주입 시) |

**결론**: **진입점(main.py) 추가 및 Config 키 정합(get_flat 계층 키 fallback) 반영 후, 로컬 전용 구동은 가능. 현재 상태만으로는 “main.py 한 번 실행으로 전체 구동”이 되지 않습니다.**  
전체 구동(시트+브로커)을 위해서는 Config_Local/시트 설정 + (선택) 브로커/시트 연동 wiring 필요.

**반영 사항 (2026-02-01)**  
- `main.py` 진입점 추가 (프로젝트 루트). `--local-only` 시 Config_Local만 로드, NoopBroker 사용.  
- `UnifiedConfig.get_flat(key)`: 계층 키 fallback 추가 (`*.key` 패턴으로 조회).  
- 검수 문서: 본 문서.

---

## 2. 진입점·실행 흐름

### 2.1 설계상 진입점 (문서 기준)

- **Runner**: `src/runtime/pipeline/eteda_runner.py` — `ETEDARunner(config, sheets_client?, project_root?, broker?, safety_hook?)`
- **루프**: `src/runtime/execution_loop/eteda_loop.py` — `run_eteda_loop(runner, config, policy?, should_stop?, snapshot_source?)`
- **의도된 흐름**:  
  Config 로드 → Broker 생성(선택) → Safety 생성(선택) → Runner 생성 → `asyncio.run(run_eteda_loop(...))`

### 2.2 현재 실제 진입점

- **테스트만**: `tests/runtime/integration/test_eteda_e2e.py`  
  - `UnifiedConfig` 수동 생성, Mock 클라이언트, `MockBroker`, `safety_hook=None`  
  - `run_eteda_loop`는 호출하지 않고 `runner.run_once(snapshot)`만 반복
- **루트/진입 스크립트**: 없음 (`main.py`, `run.py`, `__main__` 등 미존재)

---

## 3. 모듈별 연결 상태

### 3.1 Config

| 구성요소 | 경로 | 연결 여부 |
|----------|------|-----------|
| `load_unified_config(project_root, scope)` | `runtime/config/config_loader.py` | ✅ 구현됨. **진입점에서 미호출** |
| `load_local_config(project_root)` | `runtime/config/local_config.py` | ✅ 구현됨 |
| `load_sheet_config(project_root, scope, client?)` | `runtime/config/sheet_config.py` | ✅ 구현됨 (async 내부에 sync 래퍼) |
| `UnifiedConfig.get_flat(key)` | `runtime/config/config_models.py` | ⚠️ **키 불일치** (아래 §4) |

### 3.2 Broker

| 구성요소 | 경로 | 연결 여부 |
|----------|------|-----------|
| `create_broker_for_execution(live_allowed, adapter)` | `runtime/execution/brokers/__init__.py` | ✅ 구현됨. 프로덕션 경로에서만 사용하도록 문서화 |
| `OrderAdapterToBrokerEngineAdapter` | `runtime/execution/intent_to_order_bridge.py` | ✅ 구현됨. OrderAdapter → BrokerEngine 래핑 |
| `get_broker(broker_id, **kwargs)` | `runtime/broker/adapters/registry.py` | ✅ 구현됨. KIS/Kiwoom 등록 |
| `get_broker_for_config(BrokerConfig)` | `runtime/broker/adapters/__init__.py` | ✅ 구현됨. **UnifiedConfig → BrokerConfig 변환은 없음** |
| ETEDARunner `_act` → `broker.submit_intent(intent)` | `runtime/pipeline/eteda_runner.py` | ✅ 연결됨. broker 주입 시 ExecutionIntent → ExecutionResponse |

### 3.3 Safety

| 구성요소 | 경로 | 연결 여부 |
|----------|------|-----------|
| `SafetyLayer` (PipelineSafetyHook 구현) | `ops/safety/layer.py` | ✅ 구현됨 |
| ETEDARunner `run_once` 시작 시 `safety_hook.should_run()` | `eteda_runner.py` | ✅ 연결됨 |
| Act 단계 failsafe 시 `record_fail_safe` | `eteda_runner.py` | ✅ 연결됨 |
| 진입점에서 SafetyLayer 생성·주입 | 없음 | ❌ 없음 |

### 3.4 Execution Loop

| 구성요소 | 경로 | 연결 여부 |
|----------|------|-----------|
| `run_eteda_loop(runner, config, ...)` | `runtime/execution_loop/eteda_loop.py` | ✅ 구현됨 |
| `ETEDALoopPolicy.from_config(config)` | `runtime/execution_loop/eteda_loop_policy.py` | ✅ 구현됨. `INTERVAL_MS`, `ERROR_BACKOFF_*`, `PIPELINE_PAUSED` 등 |
| `default_should_stop_from_config(config)` | 동일 | ✅ 구현됨 |

---

## 4. 이슈: Config 키 불일치

- **현재**: `load_unified_config` → `_merge_configs` → `config_map` 키 형식은 **`"category.subcategory.key"`** (예: `SYSTEM.EXECUTION.RUN_MODE`).
- **Runner/Policy 사용**: `config.get_flat("RUN_MODE")`, `get_flat("LIVE_ENABLED")`, `get_flat("INTERVAL_MS")` 등 **단일 키(flat)** 로 조회.
- **결과**: 시트/로컬에서 로드한 Config만 쓰면 `get_flat("RUN_MODE")`가 항상 미존재로 처리될 수 있음 (테스트는 수동으로 `config_map={"RUN_MODE": "PAPER"}` 등 flat 키 사용).

**권장**:  
- `config_loader`에서 UnifiedConfig 생성 시, 문서화된 엔진/루프 키(`RUN_MODE`, `LIVE_ENABLED`, `INTERVAL_MS`, `PIPELINE_PAUSED`, `KILLSWITCH_STATUS` 등)에 대해 **flat 별칭**을 config_map에 추가하거나,  
- `UnifiedConfig.get_flat(key)`에서 `key` 뿐 아니라 `*.key` 패턴(예: `*.RUN_MODE`)으로도 조회하도록 확장.

---

## 5. 최소 실행 조건 (main.py)

- **Config_Local**: `config/local/config_local.json` 존재. (없으면 `--local-only` 실패.)
- **Python 경로**: 프로젝트 루트에서 `python main.py` 실행 (main.py가 src를 path에 추가).
- **Unified(시트) 모드**: `--local-only` 없이 실행 시 Google Sheet 연동 필요 (SPREADSHEET_ID, CREDENTIALS_PATH 또는 env).

## 6. 권장 조치 (체크리스트)

1. **진입점 추가**
   - [ ] 프로젝트 루트 또는 `src`에 `main.py`(또는 `run.py`) 추가.
   - [ ] 동작: `sys.path`에 `src` 포함 → Config 로드 → Runner/루프 생성 → `asyncio.run(run_eteda_loop(...))`.

2. **Config 정합**
   - [ ] `get_flat`과 로드된 config_map 키 정합: flat 별칭 추가 또는 `get_flat`에서 계층 키 fallback.

3. **Broker wiring (선택)**
   - [ ] 진입점에서 `broker_id`/실행 모드 읽기 (UnifiedConfig 또는 env).
   - [ ] `BrokerConfig` 생성 → `get_broker_for_config` → `OrderAdapterToBrokerEngineAdapter` → `create_broker_for_execution` → Runner에 주입.

4. **Safety wiring (선택)**
   - [ ] 진입점에서 `SafetyLayer` 생성(kill_switch/safe_mode는 config 또는 env에서) → Runner에 `safety_hook` 주입.

5. **문서/테스트**
   - [ ] README 또는 docs에 “전체 구동 방법: `python main.py` (또는 `python -m src.main`)” 및 필요 env/파일 명시.
   - [ ] (선택) `main.py` 경로를 사용하는 E2E 또는 smoke 테스트 추가.

---

## 7. 참고: 주요 파일 위치

| 용도 | 경로 |
|------|------|
| Runner | `src/runtime/pipeline/eteda_runner.py` |
| 루프 | `src/runtime/execution_loop/eteda_loop.py` |
| 루프 정책 | `src/runtime/execution_loop/eteda_loop_policy.py` |
| Config 로더 | `src/runtime/config/config_loader.py` |
| Config 모델 | `src/runtime/config/config_models.py` |
| Broker 팩토리 | `src/runtime/execution/brokers/__init__.py` |
| Intent↔Order 브릿지 | `src/runtime/execution/intent_to_order_bridge.py` |
| 어댑터 레지스트리 | `src/runtime/broker/adapters/registry.py` |
| Safety Layer | `src/ops/safety/layer.py` |
| E2E 테스트 | `tests/runtime/integration/test_eteda_e2e.py` |
