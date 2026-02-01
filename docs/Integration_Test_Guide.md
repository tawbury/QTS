# QTS 통합 테스트 가이드

## 개요

QTS 시스템의 전체 파이프라인 통합 테스트를 위한 가이드입니다.
Mock 클라이언트를 사용하여 실제 API 연결 없이 로컬 환경에서 테스트할 수 있습니다.

---

## 1. Mock-Test 실행

### 1.1 main.py 직접 실행

```bash
# 기본 실행 (10회 반복)
python main.py --local-only

# Verbose 로그 + 5회 반복
python main.py --local-only --verbose --max-iterations 5

# 무제한 실행 (Ctrl+C로 종료)
python main.py --local-only --max-iterations 0
```

### 1.2 pytest 통합 테스트 실행

```bash
# 전체 통합 테스트
pytest tests/integration/test_main_mock_run.py -v

# 특정 테스트만 실행
pytest tests/integration/test_main_mock_run.py::TestMainMockRun::test_execution_intent_passed_to_broker -v

# Coverage 포함
pytest tests/integration/test_main_mock_run.py --cov=src/runtime --cov-report=html
```

---

## 2. 테스트 시나리오

### 2.1 Config 로드 및 검증
- `config_local.json`에서 필수 키 로드
- `get_flat()` 계층적 fallback 동작 확인
- 필수 키 누락 시 명확한 에러 메시지

### 2.2 Mock Clients 동작 확인
- **MockSheetsClient**: Google API 없이 빈 데이터 반환
- **MockSafetyHook**: Kill Switch 시뮬레이션, Fail-Safe 기록
- **MockSnapshotSource**: 가격 변동 시뮬레이션 (삼성전자, SK하이닉스)

### 2.3 ETEDA 파이프라인 전체 흐름
```
Snapshot (MockSnapshotSource)
    ↓
Extract (시장 데이터 추출)
    ↓
Transform (정규화)
    ↓
Evaluate (StrategyEngine → Signal)
    ↓
Decide (Risk Gate)
    ↓
Act (BrokerEngine.submit_intent)
    ↓
ExecutionResponse
```

### 2.4 ExecutionIntent → Broker 전달
- **BUY/SELL 시그널**: ExecutionIntent 생성 → Broker 전달
- **HOLD 시그널**: Act 단계 skip
- **NoopBroker**: 모든 주문 거부 (실거래 차단)
- **MockBroker**: 테스트용 승인

---

## 3. 주요 검증 항목

### 3.1 Config 계층적 조회
```python
# config_map: "SYSTEM.LOOP.INTERVAL_MS" = "1000"
config.get_flat("INTERVAL_MS")  # → "1000"
config.get_flat("NONEXISTENT")  # → None
```

### 3.2 Safety Hook 연동
```python
mock_safety.should_run()  # → True (정상 실행)
mock_safety.record_fail_safe("FS040", "message", "Act")
mock_safety.pipeline_state()  # → "WARNING" (상태 전이)
```

### 3.3 Broker Intent 전달
```python
intent = ExecutionIntent(
    symbol="005930",
    side="BUY",
    quantity=10,
    intent_type="MARKET"
)
response = broker.submit_intent(intent)
assert response.accepted == True  # MockBroker
assert response.accepted == False  # NoopBroker
```

---

## 4. 테스트 커버리지

### 현재 통과한 테스트 (8/8)

| 테스트 | 목적 | 상태 |
|--------|------|------|
| `test_config_local_loads_successfully` | Config 로드 | ✅ |
| `test_mock_sheets_client_works` | MockSheetsClient | ✅ |
| `test_mock_safety_hook_works` | MockSafetyHook | ✅ |
| `test_mock_snapshot_source_generates_data` | MockSnapshotSource | ✅ |
| `test_eteda_runner_run_once_with_mock_data` | run_once 실행 | ✅ |
| `test_execution_intent_passed_to_broker` | Intent 전달 | ✅ |
| `test_eteda_loop_runs_limited_iterations` | Loop 제한 실행 | ✅ |
| `test_noop_broker_rejects_all_intents` | NoopBroker 거부 | ✅ |

---

## 5. 트러블슈팅

### 5.1 "Missing required config keys" 에러
```bash
# config_local.json에 다음 키가 있는지 확인:
INTERVAL_MS, ERROR_BACKOFF_MS, ERROR_BACKOFF_MAX_RETRIES,
RUN_MODE, LIVE_ENABLED, PIPELINE_PAUSED, KS_ENABLED,
BASE_EQUITY, trading_enabled
```

### 5.2 "run_once status=skipped" 반복
- **원인**: MockSnapshotSource가 주입되지 않아 `_default_snapshot()`이 사용됨
- **해결**: `--local-only` 모드에서는 자동으로 MockSnapshotSource 주입됨

### 5.3 무한 루프 종료 안됨
- **해결**: `--max-iterations N` 옵션 사용 또는 Ctrl+C

---

## 6. 다음 단계

### 6.1 실제 Strategy 구현
현재 `StrategyEngine`은 항상 HOLD를 반환합니다.
실제 전략 로직을 구현하려면:

```python
# src/runtime/engines/strategy_engine.py
def calculate_signal(self, market_data, position_data):
    # RSI, MACD 등 지표 계산
    # 매수/매도 조건 확인
    if rsi < 30:
        return {'action': 'BUY', 'qty': 10, ...}
    elif rsi > 70:
        return {'action': 'SELL', 'qty': position_qty, ...}
    return {'action': 'HOLD', 'qty': 0, ...}
```

### 6.2 실제 Kiwoom Adapter 연결
```python
# main.py _create_production_runner()
from runtime.execution.adapters.kiwoom_adapter import KiwoomAdapter

adapter = KiwoomAdapter(...)
broker = create_broker_for_execution(live_allowed=True, adapter=adapter)
```

### 6.3 실제 SafetyLayer 연결
```python
# main.py _create_production_runner()
from ops.safety.safety_layer import SafetyLayer

safety_hook = SafetyLayer(config)
runner = ETEDARunner(..., safety_hook=safety_hook)
```

---

## 7. 실행 로그 예시

```
2026-02-01 19:51:55,095 [main] INFO Loading local-only config...
2026-02-01 19:51:55,097 [main] INFO Creating mock runner (local-only mode)...
2026-02-01 19:51:55,691 [runtime.data.mock_sheets_client] INFO MockSheetsClient initialized
2026-02-01 19:51:55,691 [runtime.pipeline.mock_safety_hook] INFO MockSafetyHook initialized (state=NORMAL)
2026-02-01 19:51:55,692 [PortfolioEngine] INFO PortfolioEngine created with injected repositories
2026-02-01 19:51:55,692 [PerformanceEngine] INFO PerformanceEngine created with injected repositories
2026-02-01 19:51:55,692 [StrategyEngine] INFO StrategyEngine created
2026-02-01 19:51:55,692 [runtime.execution_loop.mock_snapshot_source] INFO MockSnapshotSource initialized (symbols=['005930', '000660'], max_iterations=3)
2026-02-01 19:51:55,692 [main] INFO Starting ETEDA loop (scope=scalp, local_only=True, max_iterations=3)
2026-02-01 19:51:55,693 [ETEDARunner] INFO Pipeline Result: {'timestamp': '2026-02-01 19:51:55', 'symbol': '005930', 'signal': {'symbol': '005930', 'action': 'HOLD', 'weight': 0.0, 'price': 70038.97, ...}, 'decision': {...}, 'act_result': {'status': 'skipped', 'action': 'HOLD'}, 'pipeline_state': 'NORMAL'}
2026-02-01 19:51:56,704 [ETEDARunner] INFO Pipeline Result: {'timestamp': '2026-02-01 19:51:56', 'symbol': '000660', ...}
2026-02-01 19:51:57,710 [ETEDARunner] INFO Pipeline Result: {'timestamp': '2026-02-01 19:51:57', 'symbol': '005930', ...}
2026-02-01 19:51:57,710 [ETEDALoop] INFO ETEDA loop stopped (should_stop=True)
2026-02-01 19:51:57,711 [main] INFO ETEDA loop finished.
```

---

## 8. 참고 문서

- [Full_Run_Integration_Scan.md](./Full_Run_Integration_Scan.md): 전체 통합 스캔 체크리스트
- [README.md](../README.md): 프로젝트 개요
- [tests/README.md](../tests/README.md): 테스트 가이드
