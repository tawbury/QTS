아래는 **4번 문서: QTS_Data_Contract_Spec.md**의  
**완성본(v1.0.0)** 이다.  
이 문서는 QTS 전체 시스템의 **데이터 표준(SSoT)** 역할을 수행하는 핵심 문서로,  
Schema → ETEDA → Engine Layer → UI까지 모든 단계가 의존한다.

---

# ============================================================

# QTS Data Contract Specification

# ============================================================

Version: v1.0.0  
Status: Data Specification (Final)  
Author: 타우  
Last Updated: 2025-12-12

문서 목적:  
QTS 시스템의 모든 데이터 구조(Raw, Calc, Engine I/O, UI Contract)를  
정확한 필드 정의, 타입, Validation 규칙과 함께 **SSoT(Single Source of Truth)** 로 고정한다.  
Python 계산 로직, ETEDA Pipeline, Engine Layer, UI Render Layer는  
모두 이 문서를 기준으로 구현되어야 한다.

---

# **1. Overview**

## **1.1 목적**

본 문서는 QTS 데이터 구조의 목적을 다음과 같이 정의한다.

1. 자동매매 시스템의 모든 데이터 구조를 단일 문서로 관리
    
2. Schema Engine → ETEDA → Engine → UI 흐름에서 데이터 불일치 제거
    
3. Contract 기반으로 엔진 및 파이프라인을 decouple
    
4. 데이터 필드 변경 시 Version 관리 기반으로 안전한 업그레이드 가능
    
5. 회귀 테스트(Regression Test)와 안정적 자동매매 운영 지원
    

---

## **1.2 범위**

포함:

- RawDataContract: 시트 기반 원천 데이터
    
- CalcDataContract: 변환 데이터
    
- EngineInput/EngineOutput Contracts
    
- OrderDecision Contract
    
- ExecutionResult + T_Ledger Contract
    
- UI Contract
    

제외:

- 개별 수식의 상세 정의 (→ QTS_Python_Calculation_Spec)
    
- 시트 구조 정의 (→ [QTS_Schema_Auto_Architecture.md](./01_Schema_Auto_Architecture.md))
    

---

## **1.6 관련 문서**

- **Schema Automation**: [01_Schema_Auto_Architecture.md](./01_Schema_Auto_Architecture.md)
- **Engine Core**: [02_Engine_Core_Architecture.md](./02_Engine_Core_Architecture.md)
- **ETEDA Pipeline**: [03_Pipeline_ETEDA_Architecture.md](./03_Pipeline_ETEDA_Architecture.md)
- **UI Architecture**: [06_UI_Architecture.md](./06_UI_Architecture.md)
- **Broker Integration**: [08_Broker_Integration_Architecture.md](./08_Broker_Integration_Architecture.md)
- **Testability**: [10_Testability_Architecture.md](./10_Testability_Architecture.md)
- **Data Layer**: [sub/18_Data_Layer_Architecture.md](./sub/18_Data_Layer_Architecture.md)
- **Feedback Loop**: [sub/20_Feedback_Loop_Architecture.md](./sub/20_Feedback_Loop_Architecture.md)

---

## **1.3 Contract-Driven Architecture 철학**

핵심 철학:

1. **엔진은 Contract만 보고 판단한다.**
    
2. **시트/브로커/API 정보는 Contract를 통해서만 전달된다.**
    
3. Contract가 바뀌지 않으면 엔진은 영구적으로 동일하게 동작한다.
    
4. Contract 변경은 시스템 변경을 의미하므로 Version 관리가 필수다.
    

---

## **1.4 Contract Versioning 철학**

Version 규칙:

- **Major 증가:** 필드 삭제, 의미 변경
    
- **Minor 증가:** 필드 추가, 선택 필드 변경
    
- **Patch 증가:** 오타·문구·코멘트 변경
    

Contract는 실행 시점에 VersionMismatchError를 발생시켜  
시스템이 잘못된 데이터 구조로 동작하지 않도록 보호한다.

---

## **1.5 Contract 간 관계도**

```
Raw Contract
   ↓ Transform
Calc Contract
   ↓ Evaluate
Engine I/O Contracts
   ↓ Decide
OrderDecision Contract
   ↓ Act
ExecutionResult / T_Ledger
   ↓ Render
UI Contract
```

---

# **2. RawData Contract Specification**

RawDataContract는 각 시트의 구조를 기반으로 생성된다.

## **2.1 Raw Contract 생성 규칙**

- Schema Engine이 필드 매핑 후 Contract를 생성
    
- 시트 컬럼명은 Contract 필드명으로 변환
    
- 데이터 타입 정규화(int, float, str, bool)
    
- 필수 필드 누락 시 RawContractError 발생
    
- Raw → Calc 단계에서 그대로 사용되므로 신뢰성이 매우 중요
    

---

## **2.2 시트별 Raw Contract 구조**

아래는 10+1 시트 기반 Contract이다.

---

### **2.2.1 Position Contract**

|필드|타입|설명|
|---|---|---|
|symbol|str|종목코드|
|qty|float|보유 수량|
|avg_price|float|평균 단가|
|market|str|시장 구분(KS/ KQ 등)|
|exposure_value|float|평가금액|
|exposure_pct|float|계좌 대비 비중|

필수 필드: symbol, qty, avg_price  
선택 필드: exposure_* (Calc 단계에서 갱신됨)

---

### **2.2.2 T_Ledger Contract**

|필드|타입|설명|
|---|---|---|
|timestamp|datetime|체결 시간|
|symbol|str|종목|
|side|str|BUY / SELL|
|qty|float|체결 수량|
|price|float|체결 가격|
|amount|float|금액|
|fee|float|수수료|
|strategy_tag|str|전략 구분|

---

### **2.2.3 History Contract**

일봉/분봉 기록 기반 RawData.

|필드|타입|
|---|---|
|date|str|
|open|float|
|high|float|
|low|float|
|close|float|
|volume|float|

---

### **2.2.4 Strategy Contract**

전략 파라미터 관리.

|필드|타입|
|---|---|
|param_name|str|
|value|float/str|
|description|str|

---

### **2.2.5 Config Contract**

|필드|타입|예시|
|---|---|---|
|trading_enabled|bool|True/False|
|mode|str|live/paper/backtest|
|interval_ms|int|500~3000|
|safe_mode|bool|True/False|

---

### **2.2.6 Risk Config Contract**

리스크 제한 정의.

|필드|타입|
|---|---|
|max_exposure_pct|float|
|max_symbol_exposure_pct|float|
|daily_loss_limit|float|
|max_trade_qty|float|

---

### **2.2.7 Dividend DB Contract**

|필드|타입|
|---|---|
|record_date|str|
|amount|float|
|symbol|str|

Local/Git DB와 동일 구조.

---

## **2.3 Null·타입 규칙**

- float 필드는 NaN 금지
    
- str 필드는 "" 금지 → None으로 정규화
    
- timestamp는 ISO 포맷으로 변환
    

---

## **2.4 Raw Contract Validation 규칙**

- symbol 필드가 비어 있으면 오류
    
- qty < 0 인 경우 오류
    
- 열(column) 누락 시 ContractBuildError
    

---

## **2.5 Raw Contract 오류 코드**

- RC001: Required field missing
    
- RC002: Invalid type
    
- RC003: Schema mismatch
    
- RC004: Raw contract build failed
    

---

# **3. CalcData Contract Specification**

Calc Contract는 Raw Contract 기반 **계산된 값 집합**이다.

## **3.1 Calc Contract 생성 규칙**

- Raw → Calc 단계는 순차적
    
- 모든 계산은 Python Calculation Spec 기반으로 수행
    
- 결과는 CalcDataContract 형태로 반환
    

---

## **3.2 주요 계산 필드 (Exposure, PnL, Weight 등)**

|필드|타입|설명|
|---|---|---|
|exposure_value|float|qty * price|
|exposure_pct|float|exposure_value / total_equity|
|unrealized_pnl|float|(price - avg_price) * qty|
|realized_pnl|float||
|target_weight|float||
|current_weight|float||
|equity|float|total_equity|

---

## **3.3 Python Calculation Spec과 연결**

Transform 단계는 계산 로직을 직접 구현하지 않는다.  
모든 공식은 아래 문서를 참조한다:

```
QTS_Python_Calculation_Spec.md
```

Calc Contract는 이 스펙 결과를 저장하는 구조다.

---

## **3.4 Symbol 단위 Calc Contract**

각 종목별 Calc 구조:

```python
CalcSymbol = {
    "symbol": "AAPL",
    "price": 189.12,
    "qty": 10,
    "exposure_value": 1891.2,
    "unrealized_pnl": 203.5,
    "target_weight": 0.12,
    ...
}
```

---

## **3.5 Account 단위 Calc Contract**

계좌 전체 계산:

```python
CalcAccount = {
    "total_equity": 10000000,
    "total_exposure": 8500000,
    "daily_pnl": 120000,
    "mdd": 0.05,
}
```

---

## **3.6 Calc Contract Validation**

- exposure_pct > 1 → 경고
    
- total_equity <= 0 → 오류
    
- unrealized_pnl NaN → 오류
    

---

## **3.7 계산 오류 처리 규칙**

- NaN 발생 → CalcError
    
- division by zero → CalcError
    
- 계산필드 누락 → CalcError
    

---

# **4. Engine Input/Output Contract Specification**

Engine Layer는 Contract 기반으로만 동작한다.

## **4.1 StrategyInput / StrategyDecision**

### StrategyInput

|필드|타입|
|---|---|
|symbol_data|History/가격 Contract|
|position_data|Position Contract|
|strategy_params|Strategy Contract|
|market_context|dict|

### StrategyDecision

|필드|타입|설명|
|---|---|---|
|signal|str|BUY/SELL/HOLD/NONE|
|confidence|float|신호 강도|
|recommended_qty|float||
|reason|str||

---

## **4.2 RiskInput / RiskDecision**

### RiskInput

- StrategyDecision
    
- Position Contract
    
- Calc Contract
    
- Risk Config
    
- Account Info
    

### RiskDecision

|필드|타입|
|---|---|
|approved|bool|
|allowed_qty|float|
|reason|str|

---

## **4.3 PortfolioInput / PortfolioDecision**

PortfolioDecision:

|필드|타입|
|---|---|
|final_qty|float|
|current_weight|float|
|target_weight|float|
|adjustment_reason|str|

---

## **4.4 TradingInput / TradingOutput**

### TradingInput

|필드|타입|
|---|---|
|action|BUY/SELL|
|qty|float|
|price|float|
|broker_config|dict|

### TradingOutput (Unified Execution Result)

|필드|타입|
|---|---|
|success|bool|
|order_id|str|
|symbol|str|
|filled_qty|float|
|avg_fill_price|float|
|timestamp|datetime|

---

## **4.5 PerformanceInput / PerformanceOutput**

PerformanceInput:

- T_Ledger
    
- CalcAccount
    
- Price Data
    

PerformanceOutput:

- PnL Series
    
- MDD
    
- CAGR
    
- Strategy Performance
    

---

## **4.6 Contract Interchange Rules**

- Raw → Calc → EngineInput
    
- EngineOutput → Decide → OrderDecision
    
- OrderDecision → TradingInput
    

---

## **4.7 Contract Validation Rules**

1. 필수 필드 존재 여부
    
2. 타입 정합성 확인
    
3. 논리적 정합성(ex: qty > 0 when BUY)
    
4. Contract Version 확인
    

---

# **5. OrderDecision Contract Specification**

OrderDecision은 Evaluate 결과를 기반으로  
최종 매수/매도/보류 여부를 결정하는 Contract이다.

## **5.1 필드**

|필드|타입|
|---|---|
|action|BUY/SELL/NONE|
|qty|float|
|price_type|MARKET/LIMIT|
|limit_price|float or None|
|reason|str|

---

## **5.2 주문 유형**

- MARKET
    
- LIMIT
    
- STOP
    
- STOP_LIMIT
    

---

## **5.3 포트폴리오/리스크 반영 규칙**

- final_qty는 RiskDecision.allowed_qty 이하
    
- Safe Mode에서는 action = NONE
    

---

## **5.4 주문 가능/불가 판단**

- qty <= 0 → 주문 불가
    
- approved=False → 주문 불가
    

---

## **5.5 가격 소스 규칙**

- MARKET 주문은 History 등 가격 데이터 사용
    
- LIMIT 주문은 Portfolio/Strategy에서 제공된 limit_price 사용
    

---

## **5.6 Validation**

- action 필수
    
- qty가 0 이하일 수 없음
    
- limit_price는 LIMIT 주문에서만 허용
    

---

# **6. ExecutionResult & T_Ledger Contract Specification**

## **6.1 Unified Execution Result Model**

브로커별 응답을 통합한 모델:

```python
ExecutionResult = {
    "success": True,
    "order_id": "...",
    "symbol": "AAPL",
    "filled_qty": 10,
    "avg_fill_price": 185.5,
    "amount": 1855,
    "timestamp": "...",
}
```

---

## **6.2 정규화 규칙**

브로커별 응답 형식 차이를 다음 규칙으로 통합:

- timestamp → ISO
    
- filled_qty → float
    
- null 값은 None으로 정규화
    

---

## **6.3 ExecutionResult 필드 정의**

|필드|타입|
|---|---|
|success|bool|
|order_id|str|
|symbol|str|
|filled_qty|float|
|avg_fill_price|float|
|amount|float|
|fee|float|
|timestamp|str|

---

## **6.4 ExecutionResult → T_Ledger 매핑 규칙**

- amount = filled_qty * avg_fill_price
    
- fee는 브로커 정책 기반
    
- side는 OrderDecision.action으로 결정
    

---

## **6.5 체결 정보 오류 처리**

- filled_qty == 0 → Partial Fill or Reject
    
- avg_fill_price == None → BrokerError
    

---

## **6.6 Validation**

- symbol=None → 오류
    
- filled_qty<0 → 오류
    
- amount<0 → 오류
    

---

# **7. UI Contract Specification**

UI Contract는 대시보드(R_Dash)를 업데이트하기 위한 구조.  
**필드·버전 정책·단일 빌더 원칙**은 **[UI_Contract_Schema.md](./UI_Contract_Schema.md)** 에 고정되어 있다.

## **7.1 목적**

- 파이프라인의 성과 및 상태를 시각화
    
- 운영자가 판단할 수 있는 지표 제공
    

---

## **7.2 R_Dash 구조**

|필드|설명|
|---|---|
|total_equity|계좌 평가금|
|daily_pnl|일 손익|
|exposure_pct|전체 노출|
|top_gainer|최대 상승 종목|
|top_loser|최대 하락 종목|
|strategy_summary|전략별 성과|
|pipeline_status|RUNNING/SAFE/FAIL/LOCKDOWN|

---

## **7.3 UI 필드 핵심 규칙**

- CalcAccount 기반
    
- PerformanceEngine 기반
    
- Contract Version 불일치 시 렌더링 중단
    

---

## **7.4 업데이트 규칙**

- ETEDA 종료 시 마다 UI Contract 갱신
    
- UI는 ETEDA 파이프라인을 방해하지 않아야 한다
    
- UI 렌더링 실패는 매매 중단 사유가 아님
    

---

## **7.5 Validation**

- daily_pnl NaN → 오류
    
- total_equity <= 0 → 경고
    
- pipeline_status None → 오류
    

---

# **8. Contract Versioning & Compatibility Rules**

## **8.1 Version 필드 규칙**

```
contract.version = "1.0.0"
```

---

## **8.2 Major/Minor 규칙**

- 필드 삭제 → Major 증가
    
- 필드 추가 → Minor 증가
    
- 의미 변경 → Major 증가
    

---

## **8.3 Contract 변경 시 호환성 처리**

- Adapter Layer 필요 시 적용
    
- ETEDA 시작 시 version mismatch 검사
    

---

## **8.4 Adapter Layer 사용**

예: Contract 1.0.0 → 1.1.0 변환 시 체계적 적응 레이어 추가 가능.

---

## **8.5 VersionMismatch 처리**

Mismatch 발생 시:

- Pipeline 즉시 중단
    
- Fail-Safe 적용 가능
    
- 운영자 알림 송출
    

---

# **9. Contract Error Model**

오류 모델은 Contract의 안정성을 보장하기 위해 필수적이다.

## **9.1 ContractError**

모든 Contract 관련 오류의 베이스 클래스.

## **9.2 RequiredFieldMissingError**

필수 필드 누락 시 발생.

## **9.3 TypeMismatchError**

필드 타입이 명세와 다를 때 사용.

## **9.4 VersionMismatchError**

Contract Version이 기대값과 다름.

## **9.5 ContractBuildError**

Contract 생성 과정 실패.

---

## **9.6 Error Code Table**

|코드|설명|
|---|---|
|CE001|Required field missing|
|CE002|Type mismatch|
|CE003|Version mismatch|
|CE004|Contract build failed|

---

# **10. TimescaleDB-Specific Contracts**

## **10.1 Time-Series Data Contracts**

TimescaleDB 기반 시계열 데이터를 위한 Contract 확장.

---

### **10.1.1 TickData Contract**

틱 데이터 저장 및 조회를 위한 Contract.

|필드|타입|설명|
|---|---|---|
|time|timestamptz|타임스탬프 (UTC)|
|symbol|str|종목코드|
|price|decimal(18,8)|체결가|
|volume|bigint|거래량|
|bid|decimal(18,8)|매수호가|
|ask|decimal(18,8)|매도호가|
|source|str|데이터 소스 (broker/feed)|

**Hypertable 설정:**
- Partition Key: `time`
- Chunk Interval: 1 day
- Retention Policy: 7 days

---

### **10.1.2 OHLCV Contract (1-Minute)**

분봉 데이터 Contract (Continuous Aggregate).

|필드|타입|설명|
|---|---|---|
|bucket|timestamptz|1분 버킷 시작 시각|
|symbol|str|종목코드|
|open|decimal(18,8)|시가|
|high|decimal(18,8)|고가|
|low|decimal(18,8)|저가|
|close|decimal(18,8)|종가|
|volume|bigint|거래량|

**Continuous Aggregate 설정:**
- Source: `tick_data`
- Refresh Policy: Real-time

---

### **10.1.3 ExecutionLog Contract**

실행 로그 시계열 데이터.

|필드|타입|설명|
|---|---|---|
|time|timestamptz|실행 시각|
|order_id|str|주문 ID|
|symbol|str|종목|
|stage|str|실행 단계 (PreCheck/Send/Fill)|
|latency_ms|float|레이턴시 (밀리초)|
|success|bool|성공 여부|
|error_code|str|오류 코드 (있는 경우)|

**Retention Policy:** 90 days

---

## **10.2 Feedback Data Contract**

Feedback Loop를 위한 데이터 Contract.

```python
@dataclass
class FeedbackData:
    """Execution → Strategy 피드백 데이터"""

    # Tick Data
    scalp_ticks: List[TickRecord]

    # Execution Metrics
    total_slippage_bps: float
    avg_fill_latency_ms: float
    partial_fill_ratio: float

    # Market Context
    volatility_at_execution: float
    spread_at_execution: float
    depth_at_execution: int

    # Learning Signals
    execution_quality_score: float  # 0.0 ~ 1.0
    market_impact_bps: float

    # Timestamps
    execution_start: datetime
    execution_end: datetime
    feedback_generated_at: datetime


@dataclass
class TickRecord:
    """개별 틱 레코드"""
    timestamp: datetime
    symbol: str
    price: Decimal
    volume: int
    side: str  # BID / ASK / TRADE
```

---

## **10.3 Database Adapter Contract Interface**

데이터 소스 중립적 Contract 생성을 위한 Adapter 인터페이스.

```python
class DataSourceAdapter(ABC):
    """데이터 소스 추상 인터페이스"""

    @abstractmethod
    def fetch_raw_data(self, sheet_name: str) -> RawDataContract:
        """Raw 데이터 조회"""
        pass

    @abstractmethod
    def store_execution_result(self, result: ExecutionResult) -> bool:
        """실행 결과 저장"""
        pass

    @abstractmethod
    def fetch_time_series(
        self,
        symbol: str,
        start: datetime,
        end: datetime
    ) -> List[TickData]:
        """시계열 데이터 조회 (TimescaleDB 전용)"""
        pass
```

**구현체:**
- `GoogleSheetsAdapter`: Google Sheets 연결
- `TimescaleDBAdapter`: PostgreSQL + TimescaleDB 연결
- `HybridAdapter`: Sheets + DB 하이브리드

---

## **10.4 Contract Migration Path**

Google Sheets → TimescaleDB 마이그레이션 시 Contract 호환성 유지.

**호환성 규칙:**
1. RawDataContract 인터페이스는 데이터 소스 무관
2. Adapter Layer가 소스별 변환 담당
3. ETEDA Pipeline은 Contract만 인지
4. Schema Version은 데이터 소스 변경 시에도 유지

**마이그레이션 체크리스트:**
- [ ] DB Adapter 구현
- [ ] RawDataContract 호환성 검증
- [ ] Dual-Write 모드 활성화
- [ ] 데이터 정합성 검증
- [ ] Read 트래픽 DB로 이동
- [ ] Google Sheets Read-Only 전환

---

# **11. Appendix**

## **11.1 Contract 전체 요약 표**

Raw → Calc → Engine I/O → Order → ExecutionResult → UI 전체 구조 요약.

## **11.2 Pseudocode 예시**

각 Contract 생성 예시 코드.

## **11.3 Contract 연결 다이어그램**

데이터 흐름 흐름도.

## **11.4 계산 필드 목록**

Python Calculation Spec 링크.

## **11.5 확장 가능한 Contract 구조**

미래 확장 대응을 위한 Contract 계층화 구조.

## **11.6 TimescaleDB Schema 예시**

상세한 DDL 및 설정은 [sub/18_Data_Layer_Architecture.md](./sub/18_Data_Layer_Architecture.md) 참조.

---

**QTS Data Contract Specification v1.0.0 — 완료됨**