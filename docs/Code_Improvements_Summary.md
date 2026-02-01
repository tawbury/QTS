# QTS 코드 개선 요약

## 개요

Mock-Test 및 통합 테스트 결과를 기반으로 발견된 문제점들을 수정하고 전체 시스템을 개선했습니다.

**작업 일시**: 2026-02-01
**테스트 결과**: 15/15 통과 (통합 테스트 8개 + 단위 테스트 7개)

---

## 1. 수정된 파일 목록

### 1.1 신규 생성된 파일

| 파일 경로 | 목적 |
|----------|------|
| `src/runtime/data/mock_sheets_client.py` | Google Sheets API 없이 동작하는 Mock 클라이언트 |
| `src/runtime/pipeline/mock_safety_hook.py` | Safety Layer Mock 구현 |
| `src/runtime/execution_loop/mock_snapshot_source.py` | 테스트용 가격 데이터 생성기 |
| `src/runtime/config/config_validator.py` | Config 필수 키 검증 로직 |
| `src/runtime/utils/runtime_checks.py` | 실행 환경 사전 검증 |
| `tests/integration/test_main_mock_run.py` | 전체 파이프라인 통합 테스트 |
| `tests/unit/test_config_validator.py` | Config Validator 단위 테스트 |
| `docs/Integration_Test_Guide.md` | 통합 테스트 가이드 |
| `docs/Code_Improvements_Summary.md` | 본 문서 |

### 1.2 수정된 파일

| 파일 경로 | 주요 변경 사항 |
|----------|----------------|
| `main.py` | Mock 모드 추가, Config 검증, Preflight Check, 시그널 핸들러 |
| `config/local/config_local.json` | 필수 키 8개 추가 (INTERVAL_MS 등) |
| `src/runtime/engines/strategy_engine.py` | position_data Optional 처리, reason 필드 추가 |
| `src/runtime/pipeline/eteda_runner.py` | position_data 예외 처리 개선 |

---

## 2. 주요 개선 사항

### 2.1 Config Validation 추가

**문제점**: 필수 Config 키가 누락되어도 런타임 에러로만 발견됨

**해결책**:
- `config_validator.py` 추가
- main.py에서 Config 로드 후 즉시 검증
- 명확한 에러 메시지 제공

```python
# 필수 키 검증
REQUIRED_KEYS = {
    "INTERVAL_MS", "ERROR_BACKOFF_MS", "ERROR_BACKOFF_MAX_RETRIES",
    "RUN_MODE", "LIVE_ENABLED", "trading_enabled",
    "PIPELINE_PAUSED", "KS_ENABLED", "BASE_EQUITY"
}

try:
    validate_config(config)
except ConfigValidationError as e:
    _LOG.error(f"Config validation failed: {e}")
    sys.exit(1)
```

### 2.2 Runtime Preflight Check

**추가 기능**:
- Python 버전 확인 (3.11+)
- 프로젝트 구조 확인 (src, config, tests 등)
- 필수 파일 확인 (config_local.json, credentials.json)

```python
if not preflight_check(project_root, verbose=args.verbose):
    _LOG.warning("Preflight check failed, but continuing anyway...")
```

### 2.3 StrategyEngine 개선

**변경 사항**:
- `position_data`를 Optional로 변경
- dict가 아닌 경우 자동으로 빈 dict 처리
- `reason` 필드 추가하여 시그널 근거 명시

```python
def calculate_signal(
    self,
    market_data: Dict[str, Any],
    position_data: Optional[Dict[str, Any]]  # Optional로 변경
) -> Dict[str, Any]:
    pos = position_data if isinstance(position_data, dict) else {}
    return {
        'symbol': symbol,
        'action': 'HOLD',
        'qty': 0,
        'reason': 'Default HOLD (no strategy loaded)'  # 근거 추가
    }
```

### 2.4 ETEDARunner Position Data 예외 처리

**변경 사항**:
- `get_positions()` 실패 시에도 파이프라인 계속 진행
- position_data=None으로 처리

```python
try:
    positions = await self._portfolio_engine.get_positions()
    position_data = next((p for p in positions if p.symbol == symbol), None)
except Exception as e:
    self._log.warning(f"Failed to fetch position data for {symbol}: {e}")
    position_data = None
```

### 2.5 main.py 리팩토링

**주요 변경**:
1. **CLI 옵션 추가**:
   - `--max-iterations N`: 반복 횟수 제한
   - `--dry-run`: --local-only 별칭

2. **시그널 핸들러**:
   - Ctrl+C 처리 (SIGINT, SIGTERM)
   - 종료 플래그 설정

3. **Mock/Production 모드 분리**:
   - `_create_mock_runner()`: Mock 클라이언트 주입
   - `_create_production_runner()`: 실제 클라이언트 사용

4. **종료 조건 개선**:
   - 시그널 수신
   - max_iterations 도달
   - PIPELINE_PAUSED Config

---

## 3. 테스트 결과

### 3.1 통합 테스트 (8/8 통과)

```bash
pytest tests/integration/test_main_mock_run.py -v

test_config_local_loads_successfully          PASSED [ 12%]
test_mock_sheets_client_works                 PASSED [ 25%]
test_mock_safety_hook_works                   PASSED [ 37%]
test_mock_snapshot_source_generates_data      PASSED [ 50%]
test_eteda_runner_run_once_with_mock_data     PASSED [ 62%]
test_execution_intent_passed_to_broker        PASSED [ 75%]
test_eteda_loop_runs_limited_iterations       PASSED [ 87%]
test_noop_broker_rejects_all_intents          PASSED [100%]

======================== 8 passed in 2.80s ========================
```

### 3.2 단위 테스트 (7/7 통과)

```bash
pytest tests/unit/test_config_validator.py -v

test_validate_config_with_all_keys            PASSED [ 14%]
test_validate_config_missing_keys             PASSED [ 28%]
test_validate_config_with_custom_keys         PASSED [ 42%]
test_validate_config_with_fallback_true       PASSED [ 57%]
test_validate_config_with_fallback_false      PASSED [ 71%]
test_get_flat_hierarchical_fallback           PASSED [ 85%]
test_validate_empty_config                    PASSED [100%]

======================== 7 passed in 0.05s ========================
```

### 3.3 main.py 실행 테스트

```bash
python main.py --local-only --max-iterations 2

2026-02-01 20:01:25 [main] INFO Loading local-only config...
2026-02-01 20:01:25 [main] INFO Config validation passed
2026-02-01 20:01:25 [main] INFO Creating mock runner (local-only mode)...
2026-02-01 20:01:25 [MockSheetsClient] INFO MockSheetsClient initialized
2026-02-01 20:01:25 [MockSafetyHook] INFO MockSafetyHook initialized (state=NORMAL)
2026-02-01 20:01:25 [main] INFO Starting ETEDA loop (local_only=True, max_iterations=2)
2026-02-01 20:01:25 [ETEDARunner] INFO Pipeline Result: {...}
2026-02-01 20:01:26 [ETEDARunner] INFO Pipeline Result: {...}
2026-02-01 20:01:26 [ETEDALoop] INFO ETEDA loop stopped (should_stop=True)
2026-02-01 20:01:26 [main] INFO ETEDA loop finished.
```

---

## 4. 데이터 흐름 검증

### 4.1 전체 파이프라인

```
┌─────────────────────────────────────────────────────────────┐
│ main.py                                                      │
├─────────────────────────────────────────────────────────────┤
│ 1. Preflight Check                                           │
│    ├─ Python 버전 확인                                       │
│    ├─ 프로젝트 구조 확인                                     │
│    └─ 필수 파일 확인                                         │
│                                                               │
│ 2. Config Load & Validation                                  │
│    ├─ load_local_only_config() or load_unified_config()     │
│    └─ validate_config()                                      │
│                                                               │
│ 3. Runner 생성                                               │
│    ├─ Mock 모드: MockSheetsClient, MockSafetyHook           │
│    └─ Production: GoogleSheetsClient, SafetyLayer            │
│                                                               │
│ 4. ETEDA Loop                                                │
│    └─ run_eteda_loop(runner, config, should_stop, snapshot)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ ETEDARunner.run_once(snapshot)                              │
├─────────────────────────────────────────────────────────────┤
│ 1. Safety Check                                              │
│    └─ safety_hook.should_run()                              │
│                                                               │
│ 2. Extract                                                   │
│    └─ snapshot → market_data (price, volume, symbol)        │
│                                                               │
│ 3. Transform                                                 │
│    ├─ PortfolioEngine.get_positions()                       │
│    └─ market_data + position_data → transformed_data        │
│                                                               │
│ 4. Evaluate                                                  │
│    └─ StrategyEngine.calculate_signal() → signal            │
│                                                               │
│ 5. Decide                                                    │
│    └─ Risk Gate → decision (approved/rejected)              │
│                                                               │
│ 6. Act                                                       │
│    ├─ Config Guard (trading_enabled, PIPELINE_PAUSED, etc)  │
│    ├─ ExecutionIntent 생성                                  │
│    └─ BrokerEngine.submit_intent() → ExecutionResponse      │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Config 계층적 조회

```python
# config_map 내부 구조:
{
    "SYSTEM.LOOP.INTERVAL_MS": "1000",
    "SYSTEM.EXECUTION.RUN_MODE": "PAPER"
}

# get_flat() 동작:
config.get_flat("INTERVAL_MS")  # → "1000" (suffix match)
config.get_flat("RUN_MODE")     # → "PAPER" (suffix match)
```

### 4.3 ExecutionIntent → Broker 전달

```python
# Decision (approved=True, action=BUY)
decision = {
    'symbol': '005930',
    'action': 'BUY',
    'qty': 10,
    'approved': True
}

# ExecutionIntent 생성
intent = ExecutionIntent(
    intent_id=uuid4(),
    symbol='005930',
    side='BUY',
    quantity=10,
    intent_type='MARKET'
)

# Broker 전달
response = broker.submit_intent(intent)

# NoopBroker: accepted=False, message="Noop broker rejects all intents"
# MockBroker: accepted=True (quantity > 0인 경우)
```

---

## 5. 향후 개선 사항

### 5.1 실제 Strategy 구현
- 현재: 항상 HOLD 반환
- 개선: RSI, MACD 등 지표 기반 매매 로직

### 5.2 Kiwoom Adapter 연결
- 현재: NoopBroker (실거래 차단)
- 개선: KiwoomAdapter 연동

### 5.3 SafetyLayer 연결
- 현재: MockSafetyHook
- 개선: ops.safety.SafetyLayer 연동

### 5.4 Performance Optimization
- Async I/O 최적화
- Repository 캐싱
- Batch 처리

---

## 6. 검증 체크리스트

- [x] Config 로드 및 검증
- [x] get_flat() 계층적 fallback
- [x] Mock Clients 동작 (Sheets, Safety, Snapshot)
- [x] ETEDA 파이프라인 전체 흐름
- [x] ExecutionIntent → Broker 전달
- [x] NoopBroker 실거래 차단
- [x] SafetyHook should_run() 연동
- [x] Preflight Check (Python, 구조, 파일)
- [x] 시그널 핸들러 (Ctrl+C)
- [x] 종료 조건 (max_iterations, PIPELINE_PAUSED)
- [x] position_data 예외 처리
- [x] 통합 테스트 8개 통과
- [x] 단위 테스트 7개 통과

---

## 7. 문서 참고

- [Integration_Test_Guide.md](./Integration_Test_Guide.md): 통합 테스트 가이드
- [Full_Run_Integration_Scan.md](./Full_Run_Integration_Scan.md): 전체 통합 스캔
- [README.md](../README.md): 프로젝트 개요
- [tests/README.md](../tests/README.md): 테스트 가이드
