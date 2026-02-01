# KIS API 통합 가이드

## 개요

한국투자증권(Korea Investment & Securities, KIS) API를 QTS 시스템에 통합한 가이드입니다.
Kiwoom과 명확하게 분리된 구조로 설계되었으며, `--broker` 옵션으로 선택할 수 있습니다.

**작업 일시**: 2026-02-01
**테스트 상태**: Import 테스트 완료, API 호출 대기

---

## 1. KIS와 Kiwoom의 구조적 분리

### 1.1 디렉토리 구조

```
src/runtime/broker/
├── kis/
│   ├── kis_client.py          # KIS REST API Client
│   ├── adapter.py              # KIS Broker Adapter (Auth)
│   ├── auth.py                 # KIS OAuth2 인증
│   └── payload_mapping.py      # KIS Payload 변환
│
├── kiwoom/
│   ├── kiwoom_client.py        # Kiwoom REST API Client
│   └── payload_mapping.py      # Kiwoom Payload 변환
│
└── adapters/
    ├── kis_adapter.py          # KISOrderAdapter (공통 Order 계약)
    └── kiwoom_adapter.py       # KiwoomOrderAdapter
```

### 1.2 분리 원칙

| 항목 | KIS | Kiwoom |
|------|-----|--------|
| **환경 변수 접두사** | `KIS_VTS_*`, `KIS_REAL_*` | `KIWOOM_VTS_*`, `KIWOOM_REAL_*` |
| **Client 클래스** | `KISClient` | `KiwoomClient` |
| **Adapter 클래스** | `KISOrderAdapter` | `KiwoomOrderAdapter` |
| **broker_id** | `"kis"` | `"kiwoom"` |
| **인증 방식** | OAuth2.0 + Hashkey | OAuth2.0 + HMAC-SHA256 |
| **tr_id** | `VTTC0802U`, `TTTC0802U` | (없음) |

---

## 2. KIS API 특징

### 2.1 인증 구조

KIS API는 2단계 인증을 사용합니다:

```
1. OAuth2.0 Token 발급
   ├─ POST /oauth2/tokenP
   ├─ Body: {grant_type, appkey, appsecret}
   └─ Response: {access_token, expires_in}

2. Hashkey 생성 (POST 요청 시 필수)
   ├─ POST /uapi/hashkey
   ├─ Headers: {appkey, appsecret}
   └─ Response: {HASH}

3. API 요청
   ├─ Headers: {authorization: "Bearer {token}", hashkey: "{hash}", tr_id: "..."}
   └─ 성공/실패
```

### 2.2 tr_id (거래 ID)

KIS API는 요청 종류를 `tr_id` 헤더로 구분합니다:

| 거래 종류 | VTS (모의투자) | REAL (실전투자) |
|-----------|----------------|-----------------|
| 매수 | `VTTC0802U` | `TTTC0802U` |
| 매도 | `VTTC0801U` | `TTTC0801U` |
| 주문 조회 | `VTTC8001R` | `TTTC8001R` |
| 주문 취소 | `VTTC0803U` | `TTTC0803U` |
| 잔고 조회 | `VTTC8434R` | `TTTC8434R` |

### 2.3 Payload 구조

```python
# KIS 매수 주문 Payload
{
    "CANO": "50157329",          # 계좌번호
    "ACNT_PRDT_CD": "01",        # 계좌상품코드
    "PDNO": "005930",            # 종목코드 (삼성전자)
    "ORD_DVSN": "01",            # 주문구분 (00: 지정가, 01: 시장가)
    "ORD_QTY": "10",             # 주문수량
    "ORD_UNPR": "0",             # 주문가격 (시장가는 0)
    "SLL_BUY_DVSN_CD": "02"      # 매수매도구분 (01: 매도, 02: 매수)
}
```

---

## 3. 구현된 컴포넌트

### 3.1 KISClient (`kis_client.py`)

```python
class KISClient:
    """KIS REST API Client"""

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        base_url: str,
        account_no: str,
        acnt_prdt_cd: str = "01",
        trading_mode: str = "VTS",  # VTS 또는 REAL
        timeout: int = 10,
    ):
        ...

    def _get_access_token(self) -> str:
        """OAuth2.0 토큰 발급 (캐싱)"""
        ...

    def _get_hashkey(self, body: Dict) -> str:
        """Hashkey 생성"""
        ...

    def place_order(self, payload: Dict) -> Dict:
        """주문 전송"""
        ...

    def get_order(self, params: Dict) -> Dict:
        """주문 조회"""
        ...

    def cancel_order(self, params: Dict) -> Dict:
        """주문 취소"""
        ...

    def get_balance(self) -> Dict:
        """잔고 조회"""
        ...
```

### 3.2 KISOrderAdapter (`kis_adapter.py`)

```python
class KISOrderAdapter(BaseBrokerAdapter):
    """
    KIS OrderAdapter

    ExecutionIntent → OrderRequest → KIS API 변환
    """

    @property
    def broker_id(self) -> str:
        return "kis"

    def place_order(self, req: OrderRequest) -> OrderResponse:
        # OrderRequest → KIS Payload
        payload = build_kis_order_payload(req, ...)

        # KIS API 호출
        resp = self._client.place_order(payload)

        # 응답 파싱
        status, order_id, message = parse_kis_place_response(resp)

        return OrderResponse(...)
```

---

## 4. 실행 방법

### 4.1 KIS VTS (모의투자) 모드

```bash
# .env 확인
KIS_MODE = "KIS_VTS"
KIS_VTS_APP_KEY = "..."
KIS_VTS_APP_SECRET = "..."
KIS_VTS_ACCOUNT_NO = "50157329"
KIS_VTS_BASE_URL = "https://openapivts.koreainvestment.com:29443"

# KIS Broker 선택하여 실행
python main.py --broker kis --scope scalp --verbose

# 예상 로그:
# [main] INFO .env file loaded
# [env_loader] INFO Broker mode: KIS_VTS
# [KISClient] INFO KISClient initialized (mode=VTS, base_url=https://openapivts.koreainvestment.com:29443)
# [main] INFO BrokerEngine created (live_allowed=False)
```

### 4.2 Kiwoom .env (모의/실전 분리)

키움도 KIS와 동일하게 [키움 REST API](https://openapi.kiwoom.com/main/home) 기준으로 `.env`에서 모의/실전을 완전 분리한다.

- **모드**: `KIWOOM_MODE = "KIWOOM_VTS"`(모의) 또는 `KIWOOM_MODE = "KIWOOM_REAL"`(실전)
- **모의**: `KIWOOM_VTS_APP_KEY`, `KIWOOM_VTS_APP_SECRET`, `KIWOOM_VTS_ACCOUNT_NO`, `KIWOOM_VTS_ACNT_PRDT_CD`, `KIWOOM_VTS_BASE_URL` (선택: `KIWOOM_VTS_WEBSOCKET_URL`)
- **실전**: `KIWOOM_REAL_APP_KEY`, `KIWOOM_REAL_APP_SECRET`, `KIWOOM_REAL_ACCOUNT_NO`, `KIWOOM_REAL_ACNT_PRDT_CD`, `KIWOOM_REAL_BASE_URL` (선택: `KIWOOM_REAL_WEBSOCKET_URL`)
- 설정 로드: `get_broker_config("KIWOOM")` → `BrokerConfig`; 클라이언트: `KiwoomClient`(base_url이 모의/실전에 따라 분리됨)

```bash
# .env 확인
KIWOOM_MODE = "KIWOOM_VTS"

# Kiwoom Broker 선택하여 실행
python main.py --broker kiwoom --scope scalp --verbose
```

### 4.3 Broker 비교 테스트

```bash
# KIS 테스트
python main.py --broker kis --local-only --max-iterations 3

# Kiwoom 테스트
python main.py --broker kiwoom --local-only --max-iterations 3
```

---

## 5. 데이터 흐름

### 5.1 KIS 주문 실행 흐름

```
StrategyEngine → Signal (BUY 005930 qty=10)
    ↓
Decision Gate → ExecutionIntent
    ↓
BrokerEngine.submit_intent(intent)
    ↓
OrderAdapterToBrokerEngineAdapter
    │ ExecutionIntent → OrderRequest 변환
    └─→ KISOrderAdapter.place_order(request)
          │ OrderRequest → KIS Payload 변환
          │   - symbol="005930" → PDNO="005930"
          │   - side=BUY → SLL_BUY_DVSN_CD="02"
          │   - qty=10 → ORD_QTY="10"
          │   - order_type=MARKET → ORD_DVSN="01"
          │
          └─→ KISClient._request(POST, "/uapi/domestic-stock/v1/trading/order-cash")
                │ 1. OAuth2.0 토큰 발급 (캐시 재사용)
                │ 2. Hashkey 생성
                │ 3. tr_id 설정 (VTTC0802U)
                │ 4. API 호출
                │
                └─→ KIS REST API
                       ↓
                  Response: {rt_cd: "0", output: {ord_no: "12345"}, ...}
                       ↓
          OrderResponse (status=ACCEPTED, broker_order_id="12345")
                       ↓
          ExecutionResponse (accepted=True, broker="kis")
```

### 5.2 환경 변수 로드 흐름

```
main.py
  │
  ├─→ load_dotenv_if_available(_ROOT)
  │      └─ .env 파일 로드
  │
  └─→ get_broker_config("KIS")
         │
         ├─ KIS_MODE 읽기 → "KIS_VTS"
         ├─ prefix = "KIS_VTS_"
         ├─ KIS_VTS_APP_KEY 로드
         ├─ KIS_VTS_APP_SECRET 로드
         ├─ KIS_VTS_ACCOUNT_NO 로드
         └─ KIS_VTS_BASE_URL 로드
         │
         └─→ BrokerConfig(
                broker_type="KIS",
                trading_mode="VTS",
                app_key="...",
                ...
             )
```

---

## 6. 트러블슈팅

### 6.1 "Missing required environment variables" 에러

**원인**: `.env` 파일에 필수 키 누락

**확인**:
```bash
# .env 파일 열기
cat .env | grep KIS_VTS

# 필수 키:
KIS_VTS_APP_KEY
KIS_VTS_APP_SECRET
KIS_VTS_ACCOUNT_NO
KIS_VTS_BASE_URL
```

### 6.2 "Hashkey response missing HASH" 에러

**원인**: KIS API가 Hashkey 생성 실패

**디버깅**:
```python
# kis_client.py에서 로그 확인
_log.error(f"Failed to get KIS hashkey: {e}")
```

**해결**:
1. `appkey`, `appsecret` 검증
2. BASE_URL 확인 (VTS vs REAL)
3. Hashkey API 호출 로그 확인

### 6.3 "Token acquisition failed" 에러

**원인**: OAuth2.0 토큰 발급 실패

**확인**:
```python
# 로그에서 HTTP 상태 코드 확인
# [ERROR] Failed to get KIS access token: HTTP 401
```

**해결**:
1. `APP_KEY`, `APP_SECRET` 재확인
2. KIS 개발자 센터에서 키 재발급
3. VTS/REAL BASE_URL 확인

### 6.4 "rt_cd != 0" 경고

**원인**: KIS API 응답 코드가 실패

**확인**:
```python
# 로그에서 rt_cd와 msg1 확인
# [WARNING] KIS API returned non-zero code: -1 - 주문가능수량 부족
```

**해결**:
1. `msg1` 메시지 확인
2. 주문 수량, 가격, 계좌 잔고 확인
3. Payload 구조 검증

---

## 7. KIS vs Kiwoom 비교

| 항목 | KIS | Kiwoom |
|------|-----|--------|
| **인증** | OAuth2.0 + Hashkey | OAuth2.0 + HMAC-SHA256 |
| **tr_id** | 필수 (헤더) | 없음 |
| **Hashkey** | POST마다 생성 | 없음 |
| **주문 Endpoint** | `/uapi/domestic-stock/v1/trading/order-cash` | `/api/v1/order` |
| **매수/매도 코드** | `02`/`01` | (Payload 의존) |
| **주문구분 코드** | `01` (시장가), `00` (지정가) | (Payload 의존) |
| **응답 코드** | `rt_cd` | `return_code` |
| **주문번호** | `ord_no` | `order_no` |

---

## 8. 다음 단계

### 8.1 즉시 가능한 테스트

1. **API 인증 검증**:
   ```bash
   python main.py --broker kis --scope scalp --verbose
   # "KIS access token acquired" 로그 확인
   ```

2. **Hashkey 생성 검증**:
   - 로그에서 "Hashkey generation" 확인

3. **주문 테스트** (StrategyEngine 수정 필요):
   - `calculate_signal()`에서 BUY 시그널 반환
   - ExecutionIntent → KIS API 호출 확인

### 8.2 향후 작업

1. **실시간 시세 연결**: KIS WebSocket 연동
2. **Position Data 연동**: `get_balance()` 결과 파싱
3. **Safety Layer 연결**: Kill Switch, Fail-Safe
4. **Performance 최적화**: 토큰/Hashkey 캐싱 개선

---

## 9. 체크리스트

- [x] KIS와 Kiwoom 분리
- [x] KISClient 구현 (OAuth2.0 + Hashkey)
- [x] KISOrderAdapter 구현
- [x] env_loader에 KIS 지원 추가
- [x] main.py에 --broker 옵션 추가
- [x] Import 테스트 통과
- [x] Broker Config 로드 검증
- [ ] **KIS API 인증 테스트** (다음 단계)
- [ ] **KIS 주문 테스트** (다음 단계)
- [ ] KIS 잔고 조회 연동
- [ ] KIS 실시간 시세 연동

---

## 10. 참고 문서

- [Production_API_Integration_Guide.md](./Production_API_Integration_Guide.md): Kiwoom 통합 가이드
- [Integration_Test_Guide.md](./Integration_Test_Guide.md): Mock 테스트 가이드
- [KIS API 문서](https://apiportal.koreainvestment.com/): 공식 API 문서
