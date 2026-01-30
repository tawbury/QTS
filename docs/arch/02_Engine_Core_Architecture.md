아래는 **2번 문서: QTS_Engine_Core_Architecture.md**  
완성본(v1.0.0)이다.

---

# ==================================================

# QTS Engine Core Architecture

# ==================================================

Version: v1.0.0  
Status: Technical Specification (Final)  
Author: 타우  
Last Updated: 2025-12-12

문서 목적:  
QTS의 5대 엔진(Strategy, Risk, Portfolio, Trading, Performance)에 대한  
역할(Role), 입력/출력 I/O Contract, 동작 알고리즘, 상태 모델, 오류 모델을  
**코드 구현의 기준(표준 스펙)** 으로 정의한다.

본 문서는 ETEDA Pipeline에서 사용되는 모든 엔진의  
**표준 동작 규칙(Engine Core Rulebook)** 이며,  
QTS_Python_Calculation_Spec.md 및 QTS_Data_Contract_Spec.md 와 함께 사용된다.

---

# **1. Overview**

## **1.1 목적**

본 문서는 다음을 위해 작성된다.

1. 5대 엔진의 **표준 Interface & Behavior** 정의
    
2. 각 엔진의 Input/Output Contract 명세
    
3. 엔진 간 상호작용 규칙을 명확히 하여 의존성 혼란 방지
    
4. 테스트·디버깅·유지보수 시 기준이 되는 참조 문서 제공
    
5. 브로커/전략/데이터 변경에도 **엔진 구조는 유지되도록** 하는 기준 설정
    

---

## **1.2 범위**

포함:

- Strategy, Risk, Portfolio, Trading, Performance Engine의 역할·I/O·알고리즘 구조
    
- Engine State Model
    
- Engine Error Model
    
- Testability 규칙
    
- ETEDA와의 연결 관계 개념
    

제외:

- 개별 수식의 상세 정의(→ QTS_Python_Calculation_Spec)
    
- 실제 코드 구현(→ Code Repository)
    
- 특정 전략(Strategy Logic)의 상세 수학 모델
    

---

## **1.4 관련 문서**

- **Data Contract**: [04_Data_Contract_Spec.md](./04_Data_Contract_Spec.md)
- **Schema Automation**: [01_Schema_Auto_Architecture.md](./01_Schema_Auto_Architecture.md)
- **ETEDA Pipeline**: [03_Pipeline_ETEDA_Architecture.md](./03_Pipeline_ETEDA_Architecture.md)
- **Broker Integration**: [08_Broker_Integration_Architecture.md](./08_Broker_Integration_Architecture.md)
- **Fail-Safe & Safety**: [07_FailSafe_Architecture.md](./07_FailSafe_Architecture.md)
- **Testability**: [10_Testability_Architecture.md](./10_Testability_Architecture.md)

---

## **1.3 Engine-Oriented Architecture 철학**

QTS의 엔진 계층은 다음 철학 위에서 설계된다.

1. **엔진은 역할 단위로 분리된다.**
    
    - Strategy: 판단
        
    - Risk: 승인/거부
        
    - Portfolio: 비중/수량 조정
        
    - Trading: 주문 실행
        
    - Performance: 기록/평가
        
2. **엔진은 시트/브로커를 직접 참조하지 않는다.**
    
    - 오직 Data Contract & BrokerAdapter를 통해서만 상호작용
        
3. **엔진은 상태 없는(State-Less) 함수처럼 설계**하되,
    
    - 필요한 최소 상태만 명시적으로 관리한다.
        
4. **엔진 간 의사결정 우선순위는 고정**된다.
    
    - Strategy → Risk → Portfolio → Trading → Performance
        

---

## **1.4 ETEDA Pipeline 내 엔진의 위치**

엔진은 ETEDA의 “Evaluate / Decide / Act” 단계에 주로 관여한다.

- Extract/Transform: 데이터 수집·계산 (엔진 X)
    
- Evaluate: Strategy → Risk → Portfolio 엔진 실행
    
- Decide: Trading Engine 준비/결정
    
- Act: Trading Engine → Broker Adapter 실행
    
- Performance Engine: Act 이후 데이터 기반 성과 계산
    

---

# **2. Engine Layer 구성요소**

QTS 엔진 레이어는 다음 다섯 엔진으로 구성된다.

## **2.1 Strategy Engine**

- 진입/청산 신호 생성
    
- 복수 전략 관리
    
- 신호 강도/설명(reason) 반환
    

## **2.2 Risk Engine**

- 전략 신호에 대한 승인·거부 결정
    
- 노출·일손실·종목 제한 등 리스크 규칙 적용
    

## **2.3 Portfolio Engine**

- 계좌·포지션·목표 비중 기반 추천 수량 계산
    
- 전략 신호를 “얼마나” 실행할지 결정
    

## **2.4 Trading Engine**

- 주문 생성 및 브로커 API 호출
    
- Execution Report 반환
    
- T_Ledger 기록 트리거
    

## **2.5 Performance Engine**

- 거래별/일별/전략별 성과 계산

- PnL, MDD, CAGR 등 성과지표 생성

- 리포트/대시보드 입력값 생성


---

## **2.6 Capital Engine (참조)**

Capital allocation across strategy pools (Scalp/Swing/Portfolio).
3-Track Capital Strategy의 자본 흐름 및 풀 관리를 담당한다.

See: [sub/14_Capital_Flow_Architecture.md](./sub/14_Capital_Flow_Architecture.md)

---

# **3. Engine Interface Model**

## **3.1 Engine Input Contract**

엔진은 다음 세 가지 유형의 Contract를 입력으로 받는다.

1. **RawDataContract** (시트 기반 원천 데이터)
    
2. **CalcDataContract** (Transform 단계에서 계산된 값)
    
3. **EngineInputContract** (상위 단계가 넘겨준 정보)
    

예: Strategy Engine Input

```python
StrategyInput = {
  "symbol_data": ...,
  "position_data": ...,
  "strategy_params": ...,
  "market_context": ...
}
```

---

## **3.2 Engine Output Contract**

각 엔진은 다음과 같은 출력 Contract를 제공한다.

- StrategyOutput (StrategyDecision)
    
- RiskOutput (RiskDecision)
    
- PortfolioOutput (PortfolioDecision)
    
- TradingOutput (ExecutionRequest / ExecutionResult)
    
- PerformanceOutput (PerformanceSummary / Metrics)
    

예: StrategyDecision

```python
StrategyDecision = {
  "symbol": "AAPL",
  "signal": "BUY",    # BUY / SELL / HOLD / NONE
  "confidence": 0.78,
  "recommended_qty": 10,
  "reason": "RSI oversold + MA20 cross"
}
```

---

## **3.3 Contract Validation Rules**

공통 규칙:

- 모든 필드는 명시적 타입을 가진다.
    
- 필수 필드 누락 시 EngineError 발생
    
- Contract Version이 맞지 않으면 ContractMismatchError
    

Validation은 아래 레이어에서 수행될 수 있다.

- Contract 생성 직후
    
- 엔진 입구(입력)
    
- ETEDA Evaluate 단계 시작 시
    

---

## **3.4 Contract Versioning**

각 Contract에는 버전 필드를 둘 수 있다.

```python
StrategyContract.version = "1.0.0"
```

버전 증가 사유:

- 필드 추가/삭제
    
- 의미 변화
    

버전이 다를 경우:

- 변환 Adapter 사용
    
- 또는 Fail-Safe/경고 처리
    

---

## **3.5 Error Response Contract**

엔진 실행 실패 시, 다음 형태로 응답할 수 있다.

```python
EngineErrorResponse = {
  "engine": "Strategy",
  "error_type": "ValidationError",
  "message": "Invalid strategy parameter",
  "code": "SE001"
}
```

이 정보는 ETEDA / Safety Layer에서 활용된다.

---

# **4. Strategy Engine Architecture**

## **4.1 역할**

Strategy Engine은 다음 기능을 수행한다.

- 종목별 진입/청산 시그널 계산
    
- 복수 전략을 하나의 메타 전략으로 통합
    
- “왜 이 신호가 나왔는지”에 대한 최소한의 설명 제공
    

---

## **4.2 입력값**

StrategyInput 주요 필드:

- 가격/지표 데이터 (History 기반)
    
- 현재 포지션 정보 (Position Contract)
    
- 전략별 파라미터 (Strategy Sheet)
    
- 계좌 상태(선택적)
    
- 시장 환경 정보(선택적: 변동성, 장중/장외 등)
    

---

## **4.3 출력값**

StrategyDecision:

- signal: BUY / SELL / HOLD / NONE
    
- recommended_qty: 추천 거래 수량(포트폴리오 엔진에서 재조정 가능)
    
- confidence: 신호 강도(0~1 범위 권장)
    
- reason: 문자열 또는 코드값
    

---

## **4.4 신호 계산 알고리즘 구조**

Strategy Engine은 다음 구조를 따른다.

```python
def run_strategy(input: StrategyInput) -> StrategyDecision:
    features = build_features(input)
    raw_signal = calc_signal(features)
    adjusted_signal = apply_filters(raw_signal, input)
    qty = calc_recommended_qty(input, adjusted_signal)
    reason = build_reason(features, adjusted_signal)
    return StrategyDecision(...)
```

자세한 수식은 QTS_Python_Calculation_Spec에 정의한다.

---

## **4.5 Multi-Strategy 구조**

복수 전략이 동시에 존재할 수 있다.

전략 A / B / C 예시:

```python
signals = [
  run_strategy_A(input),
  run_strategy_B(input),
  run_strategy_C(input),
]
meta_decision = merge_signals(signals)
```

### merge_signals 규칙 예:

- BUY > HOLD > NONE > SELL
    
- 혹은 가중 평균 기반 합성
    
- 충돌 시 중립 또는 보수적 방향(HOLD) 우선
    

---

## **4.6 전략 충돌 해결 규칙 (Conflict Resolution)**

규칙 예시:

1. 상반된 신호(BUY vs SELL)가 동시에 발생 시  
    → HOLD 또는 NONE 우선
    
2. 다수결 우선 (전략 3개 중 2개 BUY)
    
3. Confidence 가중치 기반 의사결정 가능
    

이 규칙은 메타 전략 정책으로 별도 정의 가능하다.

---

## **4.7 Strategy Engine 오류 처리**

오류 상황:

- 전략 파라미터 누락
    
- 계산 불가 (NaN, Inf 등)
    
- 데이터 부족(lookback 기간 부족)
    

처리 방식:

- EngineErrorResponse 반환
    
- 해당 종목에 대한 신호: NONE
    
- Risk/Portfolio/Trading 단계에서 “신호 없음”으로 처리
    

---

# **5. Risk Engine Architecture**

## **5.1 역할**

Risk Engine은 “신호가 올바르더라도 실행해도 되는지”를 판단한다.

주요 기능:

- 계좌/포지션 노출 확인
    
- 종목/전략별 리스크 한도 적용
    
- 일손실·일익절 조건 감시
    
- 브로커/시장 상태 기반 승인 제한
    

---

## **5.2 입력값**

RiskInput:

- StrategyDecision
    
- Position Contract
    
- Account Equity 정보
    
- Config(Risk Parameters)
    
- Broker Capability (공매도 가능 여부 등)
    
- Performance 요약(최근 손익 상태)
    

---

## **5.3 출력값**

RiskDecision:

```python
RiskDecision = {
  "approved": True/False,
  "allowed_qty": int,
  "reason": "MAX_EXPOSURE_LIMIT"  # 코드 or 메시지
}
```

---

## **5.4 승인·거부 판단 알고리즘**

대표 로직:

1. 계좌 노출도 검사
    
2. 종목별 최대 비중 검사
    
3. 일손실 한도 검사
    
4. 전략별 Drawdown 검사
    
5. 브로커 가능 여부 검사(공매도, 레버리지 등)
    

거부 조건 중 하나라도 참이면:

```python
approved = False
allowed_qty = 0
reason = <해당 룰 코드>
```

---

## **5.5 리스크 한도 계산식 (Exposure, MaxQty 등)**

구체적인 계산식 예:

- exposure_pct
    
- max_order_qty
    
- daily_loss_limit
    
- max_symbol_exposure
    

→ 모든 수식은 QTS_Python_Calculation_Spec에서 정식 정의.

Risk Engine은 해당 스펙을 “그대로 호출하는 수준”으로 두고,  
수식 변경 시에는 스펙 문서와 테스트를 함께 수정한다.

---

## **5.6 Fail-Safe 연동**

아래 상황에서는 Risk Engine이 Fail-Safe를 트리거할 수 있다.

- 계좌 손실률이 치명 임계값 초과
    
- 포지션 구조가 논리적으로 불가능한 상태(음수 수량 등)
    
- 브로커/계좌 정보와 Position Contract 불일치
    

이 경우:

- trading_enabled = False
    
- Execution Lockdown 활성화
    

---

## **5.7 Risk Engine 오류 처리**

- 입력 Contract 누락 → ValidationError
    
- 수치 계산 오류 → CalculationError
    
- Config 파라미터 이상 → RiskConfigError
    

오류 발생 시:

- 해당 사이클 매매 중단
    
- Fail-Safe 여부는 오류 심각도에 따라 결정
    

---

# **6. Portfolio Engine Architecture**

## **6.1 역할**

Portfolio Engine은 계좌·포지션·목표 비중 관점에서  
"얼마나 살/팔지"를 계산하는 엔진이다.

주요 기능:

- 현재 포트폴리오 구성 분석
    
- 종목별/섹터별 비중 계산
    
- 목표 비중 대비 부족분/과잉분 계산
    
- StrategyDecision을 기반으로 주문량 추천

### **포트폴리오 스코프 지원**

Portfolio Engine은 다음 스코프에서 동작할 수 있다:

- **전체 계좌 스코프** (기본값)
    
- **명시적으로 정의된 서브-포트폴리오 스코프** (예: 장기 보유 포트폴리오)

Portfolio Engine은 스코프에 대해 **시간 무관**하며, 스코프 선택은 엔진 외부에서 결정된다.

---

## **6.2 입력값**

PortfolioInput:

- StrategyDecision
    
- RiskDecision
    
- Position Contract
    
- Account Equity
    
- Target Allocation (Config or Portfolio Policy)
    
- 가격 정보 (History 등)
    
- **scope_id** (포트폴리오 스코프 식별자, 전체 계좌 스코프 시 생략 가능)

---

## **6.3 출력값**

PortfolioDecision:

```python
PortfolioDecision = {
  "scope_id": str,                    # 포트폴리오 스코프 식별자
  "final_qty": int,
  "target_weight": float,
  "current_weight": float,
  "adjustment_reason": "REBALANCE"  # or "NEW_ENTRY", "EXIT"
}
```

---

## **6.4 포트폴리오 비중 계산 로직**

기본 개념:

- total_equity: 계좌 전체 평가금
    
- current_value(symbol): 현재 포지션 평가금
    
- target_weight(symbol): 목표 비중
    
- current_weight(symbol) = current_value / total_equity
    

---

## **6.5 주문량 산출 알고리즘**

예시 구조:

```python
target_value = total_equity * target_weight
current_value = price * current_qty
diff_value = target_value - current_value
final_qty = diff_value / price
```

RiskDecision.allowed_qty와의 최소값 사용:

```python
final_qty = min(final_qty, risk_allowed_qty)
```

정확한 공식은 QTS_Python_Calculation_Spec 문서에 명시.

---

## **6.6 계좌 상태 기반 동적 재조정**

- 휴식 모드(운영자가 관망 모드 설정)
    
- 레버리지 사용 여부
    
- 특정 종목/섹터에 대한 임시 비중 축소
    

이러한 정책을 반영하여 `target_weight`를 동적으로 조정할 수 있다.

---

## **6.7 Portfolio Engine 오류 처리**

- 타겟 비중의 합이 100% 초과/미만 → Config 오류
    
- total_equity <= 0 → 매매 불가
    
- 가격 정보 미존재 → 해당 종목 주문 불가
    

오류 발생 시:

- final_qty = 0
    
- 필요 시 Risk Engine과 함께 Fail-Safe 협업
    

---

## **6.8 명시적 비책임 (중요)**

Portfolio Engine은 다음을 **수행하지 않는다**:

- **타이밍 또는 리밸런스 스케줄 결정** - 스코프 외부에서 결정됨
    
- **포트폴리오 스코프 선택 또는 해석** - 스코프는 외부에서 제공됨
    
- **전략 판단 또는 시장 진입/청산 시점 결정** - Strategy Engine의 책임
    
- **실행 인지 또는 브로커 상태 고려** - Trading Engine의 책임

Portfolio Engine은 오직 **수량 계산**에만 집중하며, 제공된 스코프와 목표 비중에 대해 시간 무관적으로 동작한다.

---

# **7. Trading Engine Architecture**

## **7.1 역할**

Trading Engine은 QTS의 **실행자(Executor)** 로서,  
주문 생성 → 브로커 전달 → Execution Report → T_Ledger 기록 흐름을 관리한다.

---

## **7.2 입력값**

TradingInput:

- PortfolioDecision.final_qty
    
- StrategyDecision.signal
    
- RiskDecision.approved
    
- 가격 정보 (현재가, 지정가 등)
    
- 브로커 설정(BrokerAdapter, 주문 타입, 수수료 정책)
    

---

## **7.3 출력값**

TradingOutput:

- OrderRequest (브로커 전송 전 내부 표현)
    
- ExecutionResult (브로커 응답 정규 모델)
    

예:

```python
ExecutionResult = {
  "success": True,
  "order_id": "123456",
  "symbol": "AAPL",
  "filled_qty": 10,
  "avg_fill_price": 180.15,
  "timestamp": ...
}
```

---

## **7.4 주문 생성 알고리즘**

1. RiskDecision.approved == True ?
    
2. final_qty > 0 ?
    
3. signal = BUY / SELL 여부 확인
    
4. Unified Order Model 생성
    

---

## **7.5 브로커 API 연동 규칙**

- Trading Engine은 브로커별 세부 API를 몰라야 한다.
    
- BrokerAdapter 인터페이스만 호출한다.
    

```python
adapter = get_broker_adapter()
execution = adapter.send_order(unified_order)
```

브로커 추가/변경 시 Trading Engine은 수정하지 않는다.

---

## **7.6 재시도·예외 처리 규칙**

- 일시적 네트워크 오류 → 설정된 횟수까지 재시도
    
- 구조적 오류(종목코드 잘못, 계좌 문제 등) → 재시도 금지
    
- 재시도 실패 시 Fail-Safe 또는 Lockdown 고려
    

---

## **7.7 Execution Report 생성 규칙**

브로커 응답 → 내부 ExecutionResult로 정규화 후:

- T_Ledger 기록
    
- Position 업데이트 트리거
    
- Performance Engine 호출의 기반 데이터 제공
    

---

## **7.8 T_Ledger 업데이트 규칙**

ExecutionResult 기반:

- 체결 시각
    
- 매수/매도 플래그
    
- 수량, 가격, 금액
    
- 수수료(있는 경우)
    

T_Ledger는 Performance 및 회귀분석의 핵심 소스다.

---

# **8. Performance Engine Architecture**

## **8.1 역할**

Performance Engine은 QTS의 “기록자/분석자” 역할이다.

- 각 거래의 손익 계산
    
- 일별/월별/전략별 성과 지표 생성
    
- UI 및 리포트용 데이터 제공
    

---

## **8.2 입력값**

PerformanceInput:

- T_Ledger
    
- Position/Equity 정보
    
- Dividend 정보
    
- 종목 가격 정보(History)
    

---

## **8.3 출력값**

PerformanceOutput:

- 거래별 PnL
    
- 일별 손익
    
- 전략별 성과
    
- MDD, CAGR, WinRate, Sharpe 등 지표
    

---

## **8.4 손익 계산식 (PnL, MDD, CAGR 등)**

대표 개념:

- realized_pnl
    
- unrealized_pnl
    
- equity_curve
    
- drawdown
    
- max_drawdown
    
- cagr
    

구체 수식은 QTS_Python_Calculation_Spec에 정의한다.

---

## **8.5 전략별 성과 계산 로직**

T_Ledger에 전략 태그가 있는 경우:

- 전략별 거래 필터링
    
- 전략별 PnL, MDD, WinRate 계산
    
- “어떤 전략이 계좌에 기여/손실을 줬는지” 평가
    

---

## **8.6 리포트 생성 규칙**

- Daily Report 기록 (Performance 등)
    
- Summary Metrics → R_Dash 및 별도 리포트 구조
    
- 장기 성과 → 월/분기/연 단위 집계
    

Performance Engine은 “기록·분석”에 집중하며  
매매 의사결정에는 관여하지 않는다.

---

## **8.7 Performance Engine 오류 처리**

- T_Ledger 누락/불일치 → Data Consistency Error
    
- Equity 계산 불가 → 오류 플래그 설정, Fail-Safe 고려
    

오류 자체가 매매를 즉시 막지는 않지만,  
계좌 상태를 정확히 이해할 수 없는 경우  
Risk Engine과 연계해 보수적 동작 수행 가능.

---

# **9. Engine State Model**

## **9.1 Engine Lifecycle (Init → Run → Validate → Return)**

각 엔진은 공통 라이프사이클을 따른다.

1. Init: Config/Contract 로딩
    
2. Run: 핵심 알고리즘 실행
    
3. Validate: 결과 검증
    
4. Return: Output Contract 반환
    

---

## **9.2 Engine Fault State**

심각한 오류 발생 시 엔진은 Fault 상태로 전이될 수 있다.

- 반복 실패
    
- Contract 불일치
    
- 내부 예외 처리 실패
    

Fault 상태는 Safety Layer와 연동되어  
매매 중단 또는 Safe Mode 진입을 유도한다.

---

## **9.3 Engine Warning State**

치명적이지는 않으나 주의가 필요한 상태.

- 일부 신호 계산 실패
    
- 특정 종목 데이터 누락
    
- 성과 계산 불완전 등
    

Warning은 R_Dash/Ops Dashboard에 표시된다.

---

## **9.4 ETEDA와의 상태 연계**

ETEDA Evaluate 단계에서 엔진 상태를 확인한다.

- Fault 발생 → 해당 사이클 중단
    
- Warning → 매매는 진행하되 경고 표시
    

---

# **10. Engine Error Model**

## **10.1 EngineError**

엔진에서 발생하는 모든 예외의 베이스 타입.

## **10.2 ValidationError**

입력/출력 Contract Validation 실패.

## **10.3 ContractMismatchError**

Contract Version 또는 필드 구조 불일치.

## **10.4 CalculationError**

수식 계산 실패(0으로 나누기, NaN, Inf 등).

## **10.5 BrokerExecutionError**

브로커 주문 실행 실패 관련 오류.

## **10.6 오류 코드 체계**

예:

- SE001: Strategy Parameter Missing
    
- RE010: Exposure Limit Exceeded
    
- PE020: Target Weight Invalid
    
- TE030: Broker Timeout
    
- FE040: Performance Calc Error
    

모든 오류는 코드 + 메시지로 관리하며,  
로그 및 모니터링 시스템과 연동된다.

---

# **11. 테스트 전략 (Testability)**

## **11.1 Unit Test (각 엔진 단위)**

- Strategy, Risk, Portfolio, Trading, Performance 각각
    
- Mock Contract 이용
    
- 핵심 함수별 Given-When-Then 검증
    

## **11.2 Integration Test (엔진 상호작용)**

- Strategy → Risk → Portfolio → Trading → Performance
    
- 하나의 흐름으로 실행 후 전체 결과 검증
    

## **11.3 Scenario Test (시나리오 기반)**

- 상승장, 급락장, 박스권, 갭 하락 등
    
- 시나리오별 엔진 동작 테스트
    

## **11.4 Regression Test**

- 엔진 업데이트 후 과거 테스트 세트 재실행
    
- 기존 결과 대비 변화율 분석
    

## **11.5 Mock Contract Generator**

테스트 편의를 위해  
**표준 Mock Contract Generator**를 별도 유틸로 관리:

```python
def make_mock_strategy_input(...):
    ...

def make_mock_risk_input(...):
    ...
```

---

# **12. Appendix**

## **12.1 Engine I/O Contract 샘플**

각 엔진별 예제 Contract 구조는  
QTS_Data_Contract_Spec와 연동해 관리.

## **12.2 Engine 간 Interaction Diagram**

- Strategy → Risk → Portfolio → Trading → Performance  
    텍스트/다이어그램 형태로 정리.
    

## **12.3 알고리즘 Pseudocode**

- 각 엔진의 핵심 루프/로직을 Pseudocode로 문서화.
    

## **12.4 Error Code Table**

- EngineError 코드 목록 및 설명.
    

---
