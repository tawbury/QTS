# QTS Production API 통합 가이드

## 개요

Mock-test에서 실제 Kiwoom API 통합으로 전환하는 가이드입니다.
VTS (모의투자) 환경에서 테스트한 후 REAL (실전투자) 환경으로 전환합니다.

**작업 일시**: 2026-02-01
**테스트 상태**: Import 테스트 완료, API 호출 대기

---

## 1. 구현된 컴포넌트

### 1.1 신규 생성된 파일

| 파일 | 목적 |
|------|------|
| `src/runtime/config/env_loader.py` | .env 환경 변수 로더, Broker Config 로드 |
| `src/runtime/broker/kiwoom/kiwoom_client.py` | Kiwoom REST API Client (인증, 주문, 조회, 취소) |
| `src/runtime/execution/adapters/order_adapter_to_broker_engine_adapter.py` | OrderAdapter → BrokerEngine 변환 어댑터 |
| `docs/Production_API_Integration_Guide.md` | 본 문서 |

### 1.2 수정된 파일

| 파일 | 변경 사항 |
|------|----------|
| `main.py` | Production Runner에 Kiwoom API 통합, .env 로드 |

---

## 2. 환경 변수 구조 (.env)

### 2.1 필수 환경 변수

```bash
# 운영 모드 선택
KIWOOM_MODE = "KIWOOM_VTS"  # 또는 "KIWOOM_REAL"

# VTS (모의투자) 설정
KIWOOM_VTS_APP_KEY = "..."
KIWOOM_VTS_APP_SECRET = "..."
KIWOOM_VTS_ACCOUNT_NO = "..."
KIWOOM_VTS_ACNT_PRDT_CD = "01"
KIWOOM_VTS_BASE_URL = "https://mockapi.kiwoom.com"
KIWOOM_VTS_WEBSOCKET_URL = "wss://openapi.kiwoom.com:443/ws/stream"

# REAL (실전투자) 설정
KIWOOM_REAL_APP_KEY = "..."
KIWOOM_REAL_APP_SECRET = "..."
KIWOOM_REAL_ACCOUNT_NO = "..."
KIWOOM_REAL_ACNT_PRDT_CD = "01"
KIWOOM_REAL_BASE_URL = "https://api.kiwoom.com"
KIWOOM_REAL_WEBSOCKET_URL = "wss://openapi.kiwoom.com:443/ws/stream"

# 안전장치
ENABLE_REAL_ORDER = "N"  # Y = 실전 주문 허용, N = 거부

# Google Sheets
GOOGLE_SHEET_KEY = "..."
GOOGLE_CREDENTIALS_FILE = "..."
```

### 2.2 모드 선택 로직

```python
from runtime.config.env_loader import get_broker_config

# KIWOOM_MODE에 따라 자동 선택
config = get_broker_config("KIWOOM")
# KIWOOM_MODE = "KIWOOM_VTS" → VTS 설정 로드
# KIWOOM_MODE = "KIWOOM_REAL" → REAL 설정 로드
```

---

## 3. 아키텍처

### 3.1 데이터 흐름

```
┌──────────────────────────────────────────────────────────────────┐
│ main.py                                                           │
├──────────────────────────────────────────────────────────────────┤
│ 1. .env 로드 (load_dotenv_if_available)                          │
│ 2. Broker Config 로드 (get_broker_config("KIWOOM"))              │
│ 3. KiwoomClient 생성 (API 인증, 토큰 관리)                        │
│ 4. KiwoomOrderAdapter 생성 (OrderRequest → Kiwoom API)           │
│ 5. OrderAdapterToBrokerEngineAdapter 생성                         │
│    └─ ExecutionIntent → OrderRequest 변환                        │
│ 6. BrokerEngine 생성 (create_broker_for_execution)               │
│ 7. ETEDARunner에 주입                                            │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ ETEDA Pipeline                                                    │
├──────────────────────────────────────────────────────────────────┤
│ StrategyEngine → Signal (BUY/SELL/HOLD)                          │
│         ↓                                                         │
│ Decision Gate → ExecutionIntent                                  │
│         ↓                                                         │
│ BrokerEngine.submit_intent(intent)                               │
│         ↓                                                         │
│ OrderAdapterToBrokerEngineAdapter                                │
│    │ Intent → OrderRequest 변환                                  │
│    └─→ KiwoomOrderAdapter.place_order(request)                   │
│           └─→ KiwoomClient._request("POST", "/api/v1/order")     │
│                  └─→ Kiwoom REST API                             │
│                         ↓                                         │
│                   ExecutionResponse                               │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 인증 흐름

```
┌────────────────────────────────────────────────────────┐
│ KiwoomClient                                            │
├────────────────────────────────────────────────────────┤
│ 1. _get_access_token()                                  │
│    ├─ POST /oauth2/token                                │
│    │  - grant_type: client_credentials                  │
│    │  - appkey: KIWOOM_VTS_APP_KEY                      │
│    │  - appsecret: KIWOOM_VTS_APP_SECRET                │
│    └─ Response: access_token, expires_in               │
│                                                          │
│ 2. 토큰 캐싱 (expires_in - 60초)                        │
│    └─ _access_token, _token_expires_at                 │
│                                                          │
│ 3. API 요청 시 자동 재사용                               │
│    └─ Authorization: Bearer {access_token}             │
│                                                          │
│ 4. 서명 생성 (POST 요청)                                 │
│    └─ signature = HMAC-SHA256(path + body, app_secret) │
└────────────────────────────────────────────────────────┘
```

---

## 4. 실행 방법

### 4.1 VTS (모의투자) 모드

```bash
# .env에서 KIWOOM_MODE 확인
KIWOOM_MODE = "KIWOOM_VTS"

# Production 모드 실행 (--local-only 없이)
python main.py --scope scalp --verbose

# 예상 로그:
# [main] INFO .env file loaded from d:\development\prj_qts\.env
# [main] INFO Broker config loaded: KIWOOM_VTS
# [KiwoomClient] INFO KiwoomClient initialized (base_url=https://mockapi.kiwoom.com, account=81190067)
# [main] INFO BrokerEngine created (live_allowed=False)
# [ETEDARunner] INFO Pipeline Result: {...}
```

### 4.2 REAL (실전투자) 모드 (주의!)

```bash
# .env 수정
KIWOOM_MODE = "KIWOOM_REAL"
ENABLE_REAL_ORDER = "Y"  # 실전 주문 허용

# Production 모드 실행
python main.py --scope scalp --verbose

# 경고: 실제 주문이 발생합니다!
```

### 4.3 Local-Only 모드 (Mock)

```bash
# API 연결 없이 Mock 테스트
python main.py --local-only --verbose --max-iterations 5
```

---

## 5. API 에러 처리

### 5.1 인증 에러

**증상**:
```
[ERROR] Failed to get Kiwoom access token: HTTP 401
KiwoomAuthError: Token acquisition failed: ...
```

**해결책**:
1. `.env` 파일의 `APP_KEY`, `APP_SECRET` 확인
2. Kiwoom 개발자 센터에서 키 재발급
3. BASE_URL이 VTS/REAL에 맞는지 확인

### 5.2 API 호출 에러

**증상**:
```
[ERROR] Kiwoom API error: POST /api/v1/order -> 400 {"return_code": -1, "return_msg": "..."}
```

**디버깅**:
1. `return_code` 확인 (0 = 성공, -1 = 실패)
2. `return_msg` 또는 `msg1` 메시지 확인
3. Payload 구조 검증 (`build_kiwoom_order_payload` 로그)

### 5.3 Rate Limit 에러

**증상**:
```
[ERROR] Kiwoom API error: HTTP 429 Too Many Requests
```

**해결책**:
1. `KiwoomClient` 생성 시 `timeout` 증가
2. ETEDA Loop의 `INTERVAL_MS` 증가
3. API 호출 빈도 제한 확인

### 5.4 Network Timeout

**증상**:
```
[ERROR] Kiwoom API request failed: POST /api/v1/order -> ConnectionError
```

**해결책**:
1. 네트워크 연결 확인
2. `KiwoomClient(timeout=10)` → `timeout=30` 증가
3. 방화벽/프록시 설정 확인

---

## 6. 로그 분석

### 6.1 정상 실행 로그

```
2026-02-01 20:30:00 [main] INFO .env file loaded from d:\development\prj_qts\.env
2026-02-01 20:30:00 [env_loader] INFO Broker mode: KIWOOM_VTS
2026-02-01 20:30:00 [KiwoomClient] INFO KiwoomClient initialized (base_url=https://mockapi.kiwoom.com, account=81190067)
2026-02-01 20:30:00 [OrderAdapterToBrokerEngineAdapter] INFO OrderAdapterToBrokerEngineAdapter initialized (broker=kiwoom)
2026-02-01 20:30:00 [main] INFO BrokerEngine created (live_allowed=False)
2026-02-01 20:30:00 [ETEDARunner] INFO Pipeline Result: {'symbol': '005930', 'signal': {'action': 'HOLD', ...}}
```

### 6.2 주문 실행 로그 (BUY/SELL)

```
2026-02-01 20:30:05 [StrategyEngine] INFO Signal generated: BUY 005930 qty=10
2026-02-01 20:30:05 [ETEDARunner] INFO Decision approved: BUY 005930
2026-02-01 20:30:05 [KiwoomClient] INFO Placing Kiwoom order: MARKET 005930
2026-02-01 20:30:05 [KiwoomClient] INFO Kiwoom access token acquired
2026-02-01 20:30:06 [KiwoomAdapter] INFO Order placed: broker_order_id=KIWOOM-12345, status=ACCEPTED
2026-02-01 20:30:06 [ETEDARunner] INFO act_result: {'status': 'executed', 'broker': 'kiwoom', 'intent_id': '...'}
```

---

## 7. 테스트 체크리스트

- [x] .env 파일 로드
- [x] Broker Config 로드 (KIWOOM_VTS)
- [x] KiwoomClient import 성공
- [x] KiwoomOrderAdapter import 성공
- [x] OrderAdapterToBrokerEngineAdapter import 성공
- [ ] KiwoomClient 인증 성공 (access_token 획득)
- [ ] 주문 Payload 생성 (build_kiwoom_order_payload)
- [ ] 주문 전송 (place_order)
- [ ] 주문 응답 파싱 (parse_kiwoom_place_response)
- [ ] ExecutionResponse 반환
- [ ] GoogleSheetsClient 연결 (Position, Portfolio 조회)
- [ ] 실시간 시세 연결 (WebSocket, 선택사항)

---

## 8. 다음 단계

### 8.1 즉시 실행 가능

1. **VTS 모드 테스트**:
   ```bash
   python main.py --scope scalp --verbose
   ```

2. **API 인증 검증**:
   - Kiwoom access_token 획득 성공 확인
   - 로그에서 "access token acquired" 확인

3. **주문 테스트** (StrategyEngine 수정 필요):
   - `calculate_signal()`에서 BUY 시그널 반환하도록 수정
   - ExecutionIntent → Kiwoom API 호출 확인

### 8.2 향후 작업

1. **실시간 시세 연결**:
   - Kiwoom WebSocket 연동
   - `MockSnapshotSource` → `KiwoomWebSocketSource`

2. **Position Data 연동**:
   - `KiwoomClient.get_positions()` 구현
   - PortfolioEngine에서 실제 포지션 조회

3. **Safety Layer 연결**:
   - Kill Switch 실제 구현
   - Fail-Safe 연동

4. **Performance Optimization**:
   - API 호출 캐싱
   - Async I/O 적용

---

## 9. 트러블슈팅

### 9.1 "Falling back to NoopBroker" 경고

**원인**: Broker 생성 중 예외 발생

**확인 사항**:
```python
# main.py _create_production_runner() 내부
except Exception as e:
    _LOG.error(f"Failed to create production broker: {e}")
```

**해결**:
1. 로그에서 실제 예외 메시지 확인
2. .env 파일 존재 여부 확인
3. 필수 환경 변수 누락 확인

### 9.2 Import Error

**증상**:
```
ModuleNotFoundError: No module named 'runtime.broker.kiwoom.kiwoom_client'
```

**해결**:
```bash
# sys.path 확인
python -c "import sys; print(sys.path)"

# src 경로 추가 확인
_SRC = _ROOT / "src"
sys.path.insert(0, str(_SRC))
```

---

## 10. 참고 문서

- [Integration_Test_Guide.md](./Integration_Test_Guide.md): Mock 테스트 가이드
- [Code_Improvements_Summary.md](./Code_Improvements_Summary.md): 코드 개선 요약
- [Kiwoom API 문서](https://api.kiwoom.com/docs): 공식 API 문서
