아래는 **8번 문서: QTS_Broker_Integration_Architecture.md**  
**완성본(v1.0.0)** 이다.

본 문서는 QTS 자동매매 시스템이 **한국투자증권 API(KIS)** 를 기본 브로커로 사용하고,  
향후 **멀티 브로커(키움증권, IBKR 등)** 로 확장될 수 있도록  
Broker Adapter Layer・Execution Flow・Fail-Safe 연동・정규화 규칙까지  
전체 구조적 기준을 정의한 최종 문서다.

---

# ============================================================

# QTS Broker Integration Architecture

# ============================================================

Version: v1.0.0  
Status: Architecture Specification (Final)  
Author: 타우  
Last Updated: 2025-12-12

문서 목적:  
본 문서는 QTS 자동매매 시스템에서 브로커 API(한국투자증권 API 중심)를  
일관되고 안정적으로 통합하기 위한 전체 아키텍처를 정의한다.

Broker Adapter Layer 설계, 주문 실행 흐름, 오류 처리·정규화,  
Fail-Safe와의 연동, Risk Engine과의 협업 구조,  
멀티 브로커 확장성에 대한 기준을 포함한다.

---

# **1. Overview**

## **1.1 목적**

QTS Broker Integration Layer는 다음 목표를 수행한다.

1. 브로커 API를 표준화하여 Engine/ETEDA가 통일된 인터페이스만 사용하도록 한다.
    
2. 주문 실행의 안정성과 정확성을 보장한다.
    
3. API 오류·체결 실패 등 예외 상황을 Fail-Safe와 연계한다.
    
4. 다양한 브로커에 쉽게 확장 가능한 구조를 제공한다.
    
5. 데이터 정합성(체결 결과·잔고·포지션)을 유지한다.
    

---

## **1.2 범위**

포함:

- 한국투자증권 API 통합
    
- 브로커 Request/Response 정규화
    
- ExecutionResult 구조 정의
    
- Fail-Safe 연동
    
- Risk Engine과의 유기적 관계
    
- Multi-Broker 확장성
    

제외:

- 브로커 UI/사용자 단 인터페이스
    
- 거래 전략(Strategy Logic)
    

---

## **1.3 브로커 통합(Broker Integration)의 역할**

Broker Integration Layer는 Trading Engine이 다음을 할 수 있도록 구조화한다.

- 주문 요청 전달
    
- 체결 정보 수집
    
- 계좌 잔고/포지션 동기화
    
- 에러 코드 해석
    
- 응답을 ExecutionResult Contract로 변환
    

---

## **1.4 브로커 API 불안정성이 QTS에 미치는 영향**

브로커 API의 불안정성은 자동매매 시스템에 치명적이다.

- 주문이 미체결된 채 방치될 수 있음
    
- 포지션/잔고 값이 업데이트되지 않으면 Risk 판단이 왜곡
    
- API 속도 지연은 ETEDA 사이클 장애로 이어짐
    
- 브로커 오류는 Fail-Safe를 촉발
    

따라서 안정적인 Broker Integration은 QTS 전체 아키텍처의 핵심이다.

---

## **1.5 Broker Adapter Layer 철학**

1. **단일 인터페이스 제공**
    
2. **브로커별 차이점은 Adapter 내부에서 완전 흡수**
    
3. **Trading Engine은 Broker 차이를 알 필요 없음**
    
4. **정규화된 ExecutionResult만 시스템 내부로 유입**
    
5. **Fail-Safe·Guardrail과 즉각적으로 연계**
    

---

# **2. Multi-Broker Architecture**

## **2.1 Primary Broker: 한국투자증권(KIS)**

QTS의 기본 브로커로 설계한다.  
이미 공식 Python SDK가 존재하며 REST 기반 API 제공.

---

## **2.2 Secondary Broker 확장 구조**

향후 지원 가능 목록:

- 키움증권 OpenAPI+
    
- 인터랙티브 브로커(IBKR)
    
- 삼성/미래에셋 Open API(출시 시)
    

멀티 브로커는 ETEDA Pipeline의 구조를 변경하지 않고 Adapter Layer만 추가하는 방식으로 확장한다.

---

## **2.3 Multi-Broker 공통 인터페이스**

```python
class BrokerInterface:
    def connect(self): ...
    def place_order(self, order): ...
    def cancel_order(self, order_id): ...
    def fetch_position(self): ...
    def fetch_balance(self): ...
    def heartbeat(self): ...
```

---

## **2.4 브로커별 제한 사항 차이**

예시:

- 주문 단위 제한
    
- 특정 시간대 API 비활성화
    
- 해외/국내 시장 차이
    
- 응답 구조 차이
    

모두 Normalization Layer에서 통합한다.

---

## **2.5 브로커 호환성 테스트 전략**

- 주문 시나리오 테스트(Buy/Sell/Partial Fill)
    
- Rate Limit Stress Test
    
- Heartbeat 안정성 테스트
    

---

# **3. Broker Adapter Layer**

## **3.1 Adapter Layer 필요성**

브로커 API는 구조·필드·응답 포맷이 모두 다르며,  
이를 Trading Engine에 그대로 노출하면 유지보수가 불가능하다.

Adapter Layer는 이러한 차이를 흡수하고  
QTS 내부에 **표준화된 인터페이스**를 제공한다.

---

## **3.2 공통 I/O Contract**

입력 → OrderDecision Contract  
출력 → ExecutionResult Contract

Contract 기반으로 모든 브로커 응답을 정규화한다.

---

## **3.3 Request Normalization**

Broker API는 다음과 같은 차이가 있다.

- 주문 유형 코드
    
- 가격 표기 방식
    
- 시장 코드
    
- 통화 단위
    

따라서 Normalization 규칙을 미리 정의한다:

```
BUY → "02" (KIS Code)  
SELL → "01"
```

---

## **3.4 PlaceOrder / CancelOrder / FetchBalance**

각 Adapter는 같은 함수명을 사용하되 내부에서 브로커별 처리.

예:

```python
adapter.place_order(order)
```

→ KIS 또는 KiwoomAdapter 내부에서 서로 다른 처리 수행.

---

## **3.5 Adapter → Trading Engine 데이터 흐름**

```
OrderDecision
   ↓  
BrokerAdapter.place_order()  
   ↓  
BrokerResponse  
   ↓  
Normalize → ExecutionResult  
   ↓  
T_Ledger 저장  
```

---

## **3.6 Adapter 에러 처리 규칙**

- 브로커 오류 코드는 표준 FS코드로 변환
    
- 재시도(Retry) 최대 횟수 설정
    
- 네트워크 장애는 즉시 Fail-Safe 경고
    

---

# **4. Execution Flow Architecture**

## **4.1 ETEDA Act 단계 연동**

Act 단계는 Trading Engine이 브로커로 직접 주문하는 유일한 단계다.

---

## **4.2 OrderDecision → BrokerOrder 변환 규칙**

필수 변환 요소:

- qty
    
- price
    
- order_type
    
- symbol
    
- 시장 코드
    
- 통화
    

---

## **4.3 ExecutionResult 표준 구조**

필드 예:

```
{
  "order_id": "",
  "symbol": "",
  "side": "",
  "qty": "",
  "filled_qty": "",
  "avg_price": "",
  "status": "",
  "timestamp": ""
}
```

---

## **4.4 예외 처리**

- 거래 불가 종목(거래정지 등)
    
- 잔량 부족
    
- 가격 제한폭 도달
    
- 브로커 서버 점검
    

모두 Fail-Safe 또는 Guardrail로 매핑.

---

## **4.5 재시도(Retry) 정책**

- 3회 재시도
    
- 일정 시간 대기 후 진행
    
- 반복 실패 시 FS040 적용(Execution Failure)
    

---

## **4.6 주문 지연/타임아웃**

지정 시간 초과 → Fail-Safe 경고  
ExecutionResult.status = “timeout”

---

# **5. Broker Data Normalization**

## **5.1 Response 표준화**

다양한 브로커 응답을 다음 필드로 통일한다.

```
qty, price, filled, status, order_id
```

---

## **5.2 필수 필드 매핑**

브로커 필드 → QTS 표준 필드로 변환.

예:

```
"ord_qty" → qty  
"ord_prc" → price  
"rltv_prc" → avg_price  
```

---

## **5.3 브로커 오류 코드 매핑**

모든 오류 코드는 다음과 같이 매핑:

|브로커 오류 코드|QTS 코드|
|---|---|
|1001|FS040|
|3005|FS041|
|timeout|FS042|

---

## **5.4 주문 유형 정규화**

- Limit / Market / Stop 모두 공통 enum에 매핑
    
- 미체결 분리 Fill 구조 통일
    

---

## **5.5 통화/시장 코드 표준화**

예:

```
KOSPI → KR  
NASDAQ → US  
```

---

# **6. ExecutionResult → Data Layer 연동**

## **6.1 ExecutionResult Contract 정의**

ExecutionResult는 브로커 응답의 정답지 역할을 한다.

---

## **6.2 T_Ledger 기록 규칙**

ExecutionResult는 다음과 같이 Ledger에 기록된다.

- filled_qty
    
- avg_price
    
- currency
    
- timestamp
    

---

## **6.3 Partial Fill 처리**

Partial → Fully Filled 변환 기준:

```
filled_qty == requested_qty  
```

부분 체결은 Ledger에 여러 레코드로 분할 기록 가능.

---

## **6.4 Slippage 계산**

```
slippage = |expected_price - avg_price|
```

---

## **6.5 주문 종료 판단**

ExecutionResult.status:

- filled → 종료
    
- cancelled → 종료
    
- pending → 미종료
    

---

## **6.6 Multi-Fill Aggregation**

여러 건의 부분 체결도 하나의 ExecutionResult Contract로 집계 가능.

---

# **7. Broker 상태 모니터링**

## **7.1 Heartbeat**

주기적으로 Broker API 호출 테스트.

---

## **7.2 Rate Limit 관리**

- n초당 최대 호출 제한
    
- 호출 초과 시 대기 및 경고
    

---

## **7.3 API 장애/지연 감지**

timeout 또는 5xx 응답 반복 시 Fail-Safe 발동.

---

## **7.4 잔고/포지션 동기화**

주기적으로:

```
fetch_balance → fetch_position → update Position Sheet
```

---

## **7.5 Ping/Pong 상태 테스트**

브로커 연결 상태를 빠르게 확인하기 위한 Lightweight API 호출.

---

# **8. Fail-Safe & Safety Layer 연동**

## **8.1 Broker 오류 → Fail-Safe 변환**

- Execution 실패 → FS040
    
- 주문 지연 → FS042
    
- 체결 데이터 누락 → FS041
    

---

## **8.2 Escalation Flow**

```
Broker Error  
 → Guardrail  
 → Fail-Safe  
 → Lockdown (반복 발생 시)
```

---

## **8.3 반복 실패 시 Lockdown**

3회 연속 실패 또는  
5분 내 반복 오류 → Lockdown 진입.

---

## **8.4 Safety 코드 매핑**

- 브로커 오류는 FS040~FS049 범위
    
- Guardrail은 GR030 (신호 충돌 등)
    

---

## **8.5 주문 재시도 한계**

Retry 횟수 초과 시 Fail-Safe 발동.

---

# **9. Risk Engine과의 관계**

## **9.1 주문 가능성 판단**

RiskOutput.approved=False → 주문 전면 차단.

---

## **9.2 Risk 거부 시 Broker 호출 금지**

Trading Engine은 BrokerAdapter를 호출하지 않음.

---

## **9.3 위험 상태에서 특정 주문 유형 비활성화**

예:

```
Stop/Limit 주문 비활성화  
Market Only Mode
```

---

## **9.4 브로커 실패가 Risk 지표에 미치는 영향**

브로커 실패 반복 → Exposure 조정 불가 → Risk 지표 왜곡  
→ Fail-Safe 필요

---

# **10. 멀티 브로커 확장 전략**

## **10.1 공통 인터페이스 기반 브로커 추가 절차**

1. Adapter 클래스 생성
    
2. 공통 인터페이스 준수
    
3. Response Normalization 구현
    
4. Test Suite 통과
    

---

## **10.2 브로커별 Market Data 수집 구조**

브로커 API 기반 실시간 가격 수집은 별도 Market Data Layer로 분리.

---

## **10.3 계좌/포트폴리오 동기화**

각 브로커마다 Position/Balance API 구조가 다르므로  
Normalization Layer에서 공통 포맷으로 변환.

---

## **10.4 주문 라우팅 정책**

- 기본: Primary Broker
    
- 예외: 특정 종목은 Secondary Broker
    
- 비상 상황: Failover Broker
    

---

## **10.5 브로커 우선순위(Fallback Broker)**

Primary 장애 → Secondary로 자동 라우팅 가능(선택 사항)

---

# **11. 보안(Security) & 인증(Authentication)**

## **11.1 API Key 보관/암호화**

- 환경 변수 사용
    
- .env 파일 암호화
    
- Git 저장 금지
    

---

## **11.2 OAuth/토큰 관리**

KIS API는 토큰 기반 인증 → 정기 갱신 필요.

---

## **11.3 API 호출 로그 보안**

민감 정보는 마스킹 처리.

---

## **11.4 민감 데이터 암호화 규칙**

AES256 또는 Secret Manager 사용 가능.

---

## **11.5 Key 관리 원칙**

- Local/Server 분리
    
- 권한 최소화
    
- 로테이션 정책
    

---

# **12. 테스트 전략**

## **12.1 Mock Broker Interface**

Mock을 통해 거래 없이 ETEDA 테스트 가능.

---

## **12.2 주문 시나리오 테스트**

- 정상 체결
    
- 부분 체결
    
- 미체결 종료
    
- 가격 오류
    

---

## **12.3 에러 코드 테스트**

브로커 오류를 강제하여 FS040~FS049 테스트 수행.

---

## **12.4 Network Delay/Timeout 시뮬레이션**

지연 상황 재현 → Fail-Safe 정상 작동 확인.

---

## **12.5 Replay 기반 회귀 테스트**

T_Ledger 기반으로 거래 재현 테스트 가능.

---

# **13. Appendix**

## **13.1 한국투자증권 API 스펙 요약**

주문·체결·잔고 API 구조 요약.

---

## **13.2 ExecutionResult 예시**

예시 JSON 포함.

---

## **13.3 Multi-Broker 클래스 다이어그램**

Adapter 구조 시각화.

---

## **13.4 브로커별 제한 사항 정리**

시간 제한·주문 단위·지원 시장 등 비교.

---

## **13.5 Broker Error Code 표**

브로커 코드 → QTS 코드 매핑.

---

**QTS Broker Integration Architecture v1.0.0 — 완료됨**

---

다음은 **9번 문서 스켈레톤: QTS Ops/Automation Architecture**  
바로 이어서 생성해줄까?