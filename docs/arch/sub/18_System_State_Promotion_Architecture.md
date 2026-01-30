# ============================================================
# QTS System State and Strategy Promotion Architecture
# ============================================================

Version: v1.0.0
Status: Architecture Specification (Final)
Author: 타우
Last Updated: 2026-01-30

문서 목적:
본 문서는 QTS 시스템의 **운영 상태(Operating State)** 모델과
**전략 프로모션(Strategy Promotion)** 메커니즘을 정의한다.
시스템 상태 전이는 데이터 기반 규칙에 따라 자동으로 수행되며,
포트폴리오 리밸런싱은 전략이 아닌 **시스템 상태**로 취급된다.

---

# **1. Overview**

## **1.1 목적**

System State Architecture는 다음 목표를 수행한다.

1. 시장 상황에 따른 동적 시스템 행동 적응
2. 3-Track 자본 전략(Scalp → Swing → Portfolio)의 상태 기반 조율
3. 규칙 기반, 비재량적 상태 전이 보장
4. 포트폴리오 리밸런싱을 시스템 수준 행위로 정의
5. Safety Layer와의 상태 연동

---

## **1.2 범위**

포함:

- Operating State(AGGRESSIVE / BALANCED / DEFENSIVE) 정의
- 상태 전이 조건 및 규칙
- 전략 프로모션(Capital Promotion) 규칙
- 포트폴리오 리밸런싱 상태 정의
- ETEDA 및 Engine Layer와의 통합
- Safety Layer 연계

제외:

- 개별 전략 알고리즘 (Strategy Engine 문서 참조)
- 개별 거래 실행 로직 (Trading Engine 문서 참조)
- 자본 풀 상세 관리 (Capital Flow Architecture 참조)

---

## **1.3 설계 원칙**

1. **상태는 전략이 아니다.**
   Operating State는 "어떤 전략을 실행할지"가 아니라
   "시스템이 어떤 모드로 동작할지"를 결정한다.

2. **상태 전이는 규칙 기반이다.**
   감정, 직관, 재량적 판단 없이 데이터 기반 규칙으로만 전이한다.

3. **리밸런싱은 전략이 아닌 상태다.**
   포트폴리오 리밸런싱은 DEFENSIVE 상태에서 시스템 수준으로 트리거된다.

4. **상태는 Safety State와 직교한다.**
   NORMAL/WARNING/FAIL/LOCKDOWN은 Safety State,
   AGGRESSIVE/BALANCED/DEFENSIVE는 Operating State로 분리된다.

---

## **1.4 관련 문서**

- **Main Architecture**: [../00_Architecture.md](../00_Architecture.md)
- **Engine Core**: [../02_Engine_Core_Architecture.md](../02_Engine_Core_Architecture.md)
- **ETEDA Pipeline**: [../03_Pipeline_ETEDA_Architecture.md](../03_Pipeline_ETEDA_Architecture.md)
- **Fail-Safe & Safety**: [../07_FailSafe_Architecture.md](../07_FailSafe_Architecture.md)
- **Capital Flow**: [14_Capital_Flow_Architecture.md](./14_Capital_Flow_Architecture.md)
- **Config 3분할**: [../13_Config_3분할_Architecture.md](../13_Config_3분할_Architecture.md)

---

# **2. Operating State Model**

## **2.1 상태 정의**

QTS는 세 가지 운영 상태를 가진다.

| 상태 | 설명 | 특성 |
|------|------|------|
| **AGGRESSIVE** | 공격적 운영 모드 | Scalp 중심, 고회전, 적극적 진입 |
| **BALANCED** | 균형 운영 모드 | Scalp + Swing 혼합, 표준 리스크 |
| **DEFENSIVE** | 방어적 운영 모드 | Portfolio 중심, 저회전, 보수적 진입 |

---

## **2.2 상태별 자본 배분 비율**

```
AGGRESSIVE:
┌─────────────────────────────────────────────────────┐
│  Scalp: 60-80%  │  Swing: 15-30%  │  Portfolio: 5-10%  │
└─────────────────────────────────────────────────────┘

BALANCED:
┌─────────────────────────────────────────────────────┐
│  Scalp: 30-50%  │  Swing: 30-40%  │  Portfolio: 20-30% │
└─────────────────────────────────────────────────────┘

DEFENSIVE:
┌─────────────────────────────────────────────────────┐
│  Scalp: 5-15%   │  Swing: 15-25%  │  Portfolio: 60-80% │
└─────────────────────────────────────────────────────┘
```

---

## **2.3 상태별 속성**

### **2.3.1 AGGRESSIVE 상태**

```python
AGGRESSIVE_PROPERTIES = {
    "scalp_allocation_pct": (0.60, 0.80),
    "swing_allocation_pct": (0.15, 0.30),
    "portfolio_allocation_pct": (0.05, 0.10),

    "risk_tolerance_multiplier": 1.2,
    "entry_signal_threshold": 0.6,      # 낮은 임계값 = 적극적 진입
    "max_position_count": 20,
    "max_daily_trades": 50,

    "rebalancing_enabled": False,
    "new_entry_enabled": True,
    "scalp_engine_active": True,
    "swing_engine_active": True
}
```

### **2.3.2 BALANCED 상태**

```python
BALANCED_PROPERTIES = {
    "scalp_allocation_pct": (0.30, 0.50),
    "swing_allocation_pct": (0.30, 0.40),
    "portfolio_allocation_pct": (0.20, 0.30),

    "risk_tolerance_multiplier": 1.0,
    "entry_signal_threshold": 0.7,      # 표준 임계값
    "max_position_count": 15,
    "max_daily_trades": 30,

    "rebalancing_enabled": True,        # 스케줄 기반
    "new_entry_enabled": True,
    "scalp_engine_active": True,
    "swing_engine_active": True
}
```

### **2.3.3 DEFENSIVE 상태**

```python
DEFENSIVE_PROPERTIES = {
    "scalp_allocation_pct": (0.05, 0.15),
    "swing_allocation_pct": (0.15, 0.25),
    "portfolio_allocation_pct": (0.60, 0.80),

    "risk_tolerance_multiplier": 0.5,
    "entry_signal_threshold": 0.9,      # 높은 임계값 = 보수적 진입
    "max_position_count": 10,
    "max_daily_trades": 10,

    "rebalancing_enabled": True,        # 우선순위 높음
    "new_entry_enabled": False,         # 신규 진입 차단 (청산만)
    "scalp_engine_active": False,       # Scalp 비활성화
    "swing_engine_active": True         # Swing 유지 (청산용)
}
```

---

## **2.4 상태 지속성(Persistence)**

상태는 다음 위치에 저장된다:

- **현재 상태**: Config_Local의 `SYSTEM_OPERATING_STATE` 키
- **상태 이력**: `State_History_Log.json` (Git 버전 관리)
- **전이 시점**: 모든 전이는 타임스탬프와 함께 기록

```python
SystemStateContract = {
    "current_state": "BALANCED",
    "previous_state": "AGGRESSIVE",
    "transition_timestamp": "2026-01-30T09:30:00Z",
    "transition_reason": "DRAWDOWN_THRESHOLD_EXCEEDED",
    "manual_override": False,
    "override_expiry": None
}
```

---

# **3. State Transition Rules**

## **3.1 전이 조건 개요**

```
        ┌──────────────────────────────────────────────────┐
        │                                                  │
        ▼                                                  │
┌─────────────┐    Volatility↑    ┌─────────────┐         │
│  AGGRESSIVE │ ───────────────▶  │  BALANCED   │         │
│             │    Drawdown>5%    │             │         │
└─────────────┘                   └─────────────┘         │
        ▲                               │                 │
        │                               │ Drawdown>10%    │
        │ Performance↑                  │ VIX>30          │
        │ Low Volatility                ▼                 │
        │                         ┌─────────────┐         │
        │                         │  DEFENSIVE  │─────────┘
        │                         │             │  Recovery
        │                         └─────────────┘
        │                               │
        └───────────────────────────────┘
              Strong Recovery
```

---

## **3.2 AGGRESSIVE → BALANCED 전이 조건**

다음 중 하나라도 충족 시 전이:

| 조건 | 임계값 | 설명 |
|------|--------|------|
| Drawdown | > 5% | 고점 대비 하락률 |
| Volatility | VIX > 25 | 변동성 상승 |
| Consecutive Scalp Losses | > 5회 | 연속 Scalp 손실 |
| Daily Loss | > 2% | 일일 손실률 |

```python
def should_transition_aggressive_to_balanced(metrics):
    return (
        metrics.drawdown_pct > 0.05 or
        metrics.vix > 25 or
        metrics.consecutive_scalp_losses > 5 or
        metrics.daily_loss_pct > 0.02
    )
```

---

## **3.3 BALANCED → DEFENSIVE 전이 조건**

다음 중 하나라도 충족 시 전이:

| 조건 | 임계값 | 설명 |
|------|--------|------|
| Drawdown | > 10% | 심각한 하락 |
| Volatility | VIX > 30 | 극심한 변동성 |
| Market Circuit Breaker | True | 시장 서킷브레이커 발동 |
| Safety State | WARNING 이상 | Safety Layer 경고 |
| Manual Override | True | 운영자 강제 전환 |

```python
def should_transition_balanced_to_defensive(metrics, safety_state):
    return (
        metrics.drawdown_pct > 0.10 or
        metrics.vix > 30 or
        metrics.market_circuit_breaker or
        safety_state in ["WARNING", "FAIL"] or
        metrics.manual_defensive_override
    )
```

---

## **3.4 DEFENSIVE → BALANCED 전이 조건**

모든 조건 충족 시 전이:

| 조건 | 임계값 | 설명 |
|------|--------|------|
| Drawdown Recovery | < 5% | 하락률 회복 |
| Volatility Normalization | VIX < 20 | 변동성 정상화 |
| Consecutive Profitable Days | > 3일 | 연속 수익일 |
| Safety State | NORMAL | Safety 정상 상태 |
| Minimum Time in State | > 5일 | 최소 상태 유지 기간 |

```python
def should_transition_defensive_to_balanced(metrics, safety_state, state_duration):
    return (
        metrics.drawdown_pct < 0.05 and
        metrics.vix < 20 and
        metrics.consecutive_profitable_days >= 3 and
        safety_state == "NORMAL" and
        state_duration.days >= 5
    )
```

---

## **3.5 BALANCED → AGGRESSIVE 전이 조건**

모든 조건 충족 시 전이:

| 조건 | 임계값 | 설명 |
|------|--------|------|
| Performance | CAGR > Target | 목표 수익률 초과 |
| Volatility | VIX < 15 | 낮은 변동성 |
| Capital Growth | > 10% | 자본 성장률 |
| Win Rate | > 60% | 최근 30일 승률 |
| Minimum Time in BALANCED | > 10일 | 최소 상태 유지 기간 |

```python
def should_transition_balanced_to_aggressive(metrics, state_duration):
    return (
        metrics.cagr > metrics.target_cagr and
        metrics.vix < 15 and
        metrics.capital_growth_pct > 0.10 and
        metrics.win_rate_30d > 0.60 and
        state_duration.days >= 10
    )
```

---

## **3.6 전이 히스테리시스(Hysteresis)**

빠른 상태 진동을 방지하기 위한 규칙:

1. **최소 상태 유지 기간**
   - AGGRESSIVE: 최소 7일
   - BALANCED: 최소 5일
   - DEFENSIVE: 최소 3일

2. **쿨다운 기간**
   - 전이 후 24시간 동안 재전이 불가
   - 예외: Safety 강제 전이

3. **전이 확인 기간**
   - 전이 조건이 연속 2 사이클(2시간) 유지 시 전이 실행
   - 일시적 조건 충족은 무시

```python
def can_transition(current_state, target_state, state_duration, last_transition_time):
    min_duration = MIN_STATE_DURATION[current_state]
    cooldown_elapsed = (now() - last_transition_time) > timedelta(hours=24)

    return state_duration >= min_duration and cooldown_elapsed
```

---

## **3.7 수동 오버라이드(Manual Override)**

운영자는 상태를 강제로 전환할 수 있다.

규칙:

1. **오버라이드 기록 필수**
   - 오버라이드 시점, 이유, 운영자 ID 기록

2. **자동 만료**
   - 오버라이드는 최대 7일 후 자동 만료
   - 만료 시 규칙 기반 상태로 복귀

3. **Safety 우선**
   - Safety Layer의 LOCKDOWN은 오버라이드보다 우선

```python
ManualOverrideContract = {
    "override_state": "DEFENSIVE",
    "override_reason": "Upcoming earnings announcement",
    "operator_id": "tau",
    "override_time": "2026-01-30T09:00:00Z",
    "expiry_time": "2026-02-06T09:00:00Z",
    "auto_revert_state": "BALANCED"
}
```

---

# **4. Strategy Promotion Model**

## **4.1 프로모션 개념**

Strategy Promotion은 자본이 하위 트랙에서 상위 트랙으로 이동하는 메커니즘이다.

```
자본 흐름:

┌──────────────┐    Profit    ┌──────────────┐    Profit    ┌──────────────┐
│  SCALP POOL  │ ──────────▶  │  SWING POOL  │ ──────────▶  │ PORTFOLIO    │
│  (Cashflow)  │   Promotion  │ (Compounding)│   Promotion  │  (Wealth)    │
└──────────────┘              └──────────────┘              └──────────────┘
```

---

## **4.2 프로모션 기준**

### **4.2.1 Scalp → Swing 프로모션**

| 기준 | 조건 | 설명 |
|------|------|------|
| 누적 수익 | Scalp Profit > Threshold | 설정된 이익 임계값 초과 |
| 리스크 조정 수익 | Sharpe > 1.5 | 리스크 대비 수익 품질 |
| 승률 일관성 | Win Rate > 55% (30일) | 지속적 수익 능력 |
| 프로모션 주기 | 주 단위 또는 월 단위 | 설정 가능 |

```python
ScalpToSwingPromotionRule = {
    "min_profit_threshold": 1000000,    # 100만원
    "min_sharpe_ratio": 1.5,
    "min_win_rate_30d": 0.55,
    "promotion_frequency": "weekly",    # weekly / monthly
    "transfer_ratio": 0.50              # 초과 수익의 50% 이전
}
```

### **4.2.2 Swing → Portfolio 프로모션**

| 기준 | 조건 | 설명 |
|------|------|------|
| 누적 수익 | Swing Profit > Threshold | 설정된 이익 임계값 초과 |
| 리스크 조정 수익 | Sharpe > 1.2 | 장기 리스크 대비 수익 |
| MDD 회복 속도 | MDD Recovery < 30일 | 하락 회복 능력 |
| 프로모션 주기 | 분기 단위 | 장기 관점 |

```python
SwingToPortfolioPromotionRule = {
    "min_profit_threshold": 5000000,    # 500만원
    "min_sharpe_ratio": 1.2,
    "max_mdd_recovery_days": 30,
    "promotion_frequency": "quarterly",
    "transfer_ratio": 0.30              # 초과 수익의 30% 이전
}
```

---

## **4.3 프로모션 흐름**

```python
def execute_promotion(pool_state, performance_metrics):
    # Scalp → Swing 프로모션 체크
    if should_promote_scalp_to_swing(pool_state, performance_metrics):
        transfer_amount = calculate_transfer_amount(
            pool_state.scalp_profit,
            ScalpToSwingPromotionRule.transfer_ratio
        )
        execute_capital_transfer(
            from_pool="SCALP",
            to_pool="SWING",
            amount=transfer_amount
        )
        log_promotion_event("SCALP_TO_SWING", transfer_amount)

    # Swing → Portfolio 프로모션 체크
    if should_promote_swing_to_portfolio(pool_state, performance_metrics):
        transfer_amount = calculate_transfer_amount(
            pool_state.swing_profit,
            SwingToPortfolioPromotionRule.transfer_ratio
        )
        execute_capital_transfer(
            from_pool="SWING",
            to_pool="PORTFOLIO",
            amount=transfer_amount
        )
        log_promotion_event("SWING_TO_PORTFOLIO", transfer_amount)
```

---

## **4.4 디모션(Demotion) 규칙**

성과 부진 시 자본이 상위 트랙에서 하위 트랙으로 복귀할 수 있다.

| 조건 | 동작 | 설명 |
|------|------|------|
| Swing MDD > 15% | Swing → Scalp | 자본 보호 |
| Portfolio MDD > 10% | Portfolio → Swing | 점진적 회복 |
| Operating State = DEFENSIVE | All → Portfolio | 상태 기반 이동 |

```python
DemotionRules = {
    "swing_to_scalp": {
        "trigger": "mdd > 0.15",
        "transfer_ratio": 0.30
    },
    "portfolio_to_swing": {
        "trigger": "mdd > 0.10",
        "transfer_ratio": 0.20
    }
}
```

---

# **5. Portfolio Rebalancing as System State**

## **5.1 리밸런싱이 전략이 아닌 이유**

1. **시스템 수준 행위**
   리밸런싱은 개별 종목 매수/매도 신호가 아니라
   전체 자산 배분을 조정하는 시스템 동작이다.

2. **상태 트리거**
   리밸런싱은 Strategy Engine이 아닌 System State에 의해 트리거된다.

3. **모든 풀에 영향**
   리밸런싱은 Scalp/Swing/Portfolio 모든 풀에 균일하게 적용된다.

---

## **5.2 리밸런싱 트리거**

| 트리거 | 조건 | 설명 |
|--------|------|------|
| 상태 전이 | → DEFENSIVE | DEFENSIVE 진입 시 자동 트리거 |
| 스케줄 | 월간/분기 | 주기적 리밸런싱 |
| 드리프트 | > 10% | 목표 비중 대비 이탈 |
| 수동 트리거 | Manual | 운영자 명령 |

```python
RebalancingTriggers = {
    "state_transition_to_defensive": True,
    "scheduled_interval": "monthly",
    "drift_threshold_pct": 0.10,
    "manual_trigger_enabled": True
}
```

---

## **5.3 리밸런싱 실행**

### **5.3.1 목표 비중 계산**

```python
def calculate_target_weights(current_state):
    state_properties = STATE_PROPERTIES[current_state]

    return {
        "scalp": state_properties.scalp_allocation_pct.midpoint,
        "swing": state_properties.swing_allocation_pct.midpoint,
        "portfolio": state_properties.portfolio_allocation_pct.midpoint
    }
```

### **5.3.2 점진적 리밸런싱**

급격한 리밸런싱을 방지하기 위해 점진적으로 실행:

```python
RebalancingConfig = {
    "max_daily_rebalance_pct": 0.05,    # 일일 최대 5% 조정
    "min_trade_amount": 100000,          # 최소 거래 금액
    "rebalance_priority": ["PORTFOLIO", "SWING", "SCALP"],
    "execute_at": "market_close"         # 장 마감 시 실행
}
```

### **5.3.3 리밸런싱 우선순위**

신규 진입보다 리밸런싱이 우선:

```
1. 리밸런싱 주문 (최우선)
2. 청산 주문
3. 신규 진입 주문 (DEFENSIVE 상태에서는 차단)
```

---

# **6. ETEDA Integration**

## **6.1 상태 인식 Extract**

Extract 단계에서 현재 Operating State를 로드한다.

```python
def extract_phase():
    # 기존 Extract 로직
    raw_data = load_raw_data()

    # Operating State 로드 (추가)
    operating_state = load_operating_state()

    return RawDataContract(
        data=raw_data,
        operating_state=operating_state
    )
```

---

## **6.2 상태 인식 Evaluate**

Evaluate 단계에서 Operating State에 따라 엔진 동작을 조정한다.

```python
def evaluate_phase(raw_contract, calc_contract):
    state = raw_contract.operating_state

    # 상태별 엔진 활성화 결정
    if state == "DEFENSIVE":
        # Scalp Engine 비활성화
        scalp_decision = StrategyDecision(signal="NONE", reason="STATE_DEFENSIVE")
    else:
        scalp_decision = ScalpEngine.evaluate(calc_contract)

    # 신호 임계값 조정
    signal_threshold = STATE_PROPERTIES[state].entry_signal_threshold

    # 임계값 미달 신호 필터링
    if scalp_decision.confidence < signal_threshold:
        scalp_decision.signal = "NONE"
        scalp_decision.reason = "BELOW_STATE_THRESHOLD"

    return EvaluationResult(
        scalp=scalp_decision,
        swing=swing_decision,
        operating_state=state
    )
```

---

## **6.3 상태 기반 Decide 오버라이드**

Decide 단계에서 상태에 따라 최종 결정을 오버라이드할 수 있다.

```python
def decide_phase(evaluation_result):
    state = evaluation_result.operating_state

    # DEFENSIVE 상태에서 신규 진입 차단
    if state == "DEFENSIVE":
        if evaluation_result.signal in ["BUY"]:
            return OrderDecision(
                action="NONE",
                reason="NEW_ENTRY_BLOCKED_IN_DEFENSIVE_STATE"
            )

    # 리밸런싱 주문 우선
    if has_pending_rebalancing():
        return OrderDecision(
            action="REBALANCE",
            rebalancing_orders=get_rebalancing_orders()
        )

    # 일반 결정 진행
    return standard_decide_logic(evaluation_result)
```

---

# **7. Engine Coordination**

## **7.1 Strategy Engine 상태 인식**

Strategy Engine은 Operating State를 입력으로 받아 동작을 조정한다.

```python
class StrategyEngine:
    def evaluate(self, input: StrategyInput, state: OperatingState):
        # 상태별 전략 파라미터 조정
        adjusted_params = self.adjust_params_for_state(input.params, state)

        # 상태별 신호 생성
        if state == "AGGRESSIVE":
            return self.aggressive_signal_generation(input, adjusted_params)
        elif state == "BALANCED":
            return self.balanced_signal_generation(input, adjusted_params)
        else:  # DEFENSIVE
            return self.defensive_signal_generation(input, adjusted_params)
```

---

## **7.2 Portfolio Engine 상태 인식**

Portfolio Engine은 Operating State에 따라 배분 계산을 조정한다.

```python
class PortfolioEngine:
    def calculate_allocation(self, input: PortfolioInput, state: OperatingState):
        # 상태별 목표 비중 로드
        target_weights = STATE_PROPERTIES[state].allocation_weights

        # 상태별 최대 포지션 수 제한
        max_positions = STATE_PROPERTIES[state].max_position_count

        return self.standard_allocation(
            input,
            target_weights=target_weights,
            max_positions=max_positions
        )
```

---

## **7.3 Risk Engine 상태 인식**

Risk Engine은 Operating State에 따라 리스크 한도를 조정한다.

```python
class RiskEngine:
    def evaluate(self, input: RiskInput, state: OperatingState):
        # 상태별 리스크 승수 적용
        risk_multiplier = STATE_PROPERTIES[state].risk_tolerance_multiplier

        adjusted_limits = {
            "max_exposure": self.base_max_exposure * risk_multiplier,
            "max_daily_loss": self.base_daily_loss * risk_multiplier,
            "max_position_size": self.base_position_size * risk_multiplier
        }

        return self.standard_risk_check(input, adjusted_limits)
```

---

## **7.4 Capital Engine 상태 인식**

Capital Engine은 Operating State에 따라 풀 배분을 조정한다.

```python
class CapitalEngine:
    def allocate(self, total_capital: float, state: OperatingState):
        allocation_ranges = STATE_PROPERTIES[state]

        return CapitalAllocation(
            scalp=total_capital * allocation_ranges.scalp_allocation_pct.midpoint,
            swing=total_capital * allocation_ranges.swing_allocation_pct.midpoint,
            portfolio=total_capital * allocation_ranges.portfolio_allocation_pct.midpoint
        )
```

---

# **8. Safety Integration**

## **8.1 Safety State와 Operating State 관계**

두 상태는 직교(Orthogonal)하며 독립적으로 관리된다.

```
Safety State:     NORMAL ─── WARNING ─── FAIL ─── LOCKDOWN
                     │          │          │         │
Operating State:     └──────────┴──────────┴─────────┘
                  (AGGRESSIVE / BALANCED / DEFENSIVE)
```

---

## **8.2 Safety → Operating State 영향**

| Safety State | Operating State 영향 |
|--------------|---------------------|
| NORMAL | 변화 없음 |
| WARNING | BALANCED → DEFENSIVE 전이 가능성 증가 |
| FAIL | 즉시 DEFENSIVE 전이 |
| LOCKDOWN | 모든 거래 차단 (Operating State 무관) |

---

## **8.3 상태 기반 Guardrails**

Operating State별 추가 Guardrail 규칙:

| 상태 | 추가 Guardrail |
|------|----------------|
| AGGRESSIVE | GR080: 일일 거래 횟수 제한 |
| BALANCED | GR081: 풀 간 비중 불균형 경고 |
| DEFENSIVE | GR082: 신규 진입 차단 확인 |

---

## **8.4 강제 상태 전이**

Safety Layer는 Operating State를 강제로 전이시킬 수 있다.

```python
def safety_forced_transition(safety_state: SafetyState):
    if safety_state == "FAIL":
        force_transition_to("DEFENSIVE", reason="SAFETY_FAIL_TRIGGERED")

    if safety_state == "LOCKDOWN":
        # Operating State 유지하되 모든 거래 차단
        pause_all_trading(reason="SAFETY_LOCKDOWN")
```

---

## **8.5 Lockdown과 Operating State**

LOCKDOWN 상태에서:

1. **Operating State 보존**
   - LOCKDOWN 동안 Operating State는 그대로 유지

2. **해제 후 복원**
   - LOCKDOWN 해제 시 저장된 Operating State로 복귀

3. **수동 상태 조정**
   - LOCKDOWN 해제 후 운영자가 상태 재검토 가능

```python
def release_lockdown():
    preserved_state = get_preserved_operating_state()

    if preserved_state == "AGGRESSIVE":
        # LOCKDOWN 후 AGGRESSIVE 복귀는 위험 → BALANCED로 복귀
        transition_to("BALANCED", reason="LOCKDOWN_RELEASE_CONSERVATIVE")
    else:
        transition_to(preserved_state, reason="LOCKDOWN_RELEASE")
```

---

# **9. Monitoring & Dashboard**

## **9.1 현재 상태 표시**

R_Dash에 표시되는 상태 정보:

```
┌─────────────────────────────────────────────────────┐
│  OPERATING STATE: [BALANCED]                        │
│  Safety State: NORMAL                               │
│  State Duration: 5일 12시간                         │
│  Next Potential Transition: AGGRESSIVE (조건 미충족) │
└─────────────────────────────────────────────────────┘
```

---

## **9.2 전이 이력**

최근 상태 전이 이력 표시:

```
┌─────────────────────────────────────────────────────┐
│  STATE TRANSITION HISTORY (Last 30 days)            │
├─────────────────────────────────────────────────────┤
│  2026-01-25 AGGRESSIVE → BALANCED (Drawdown 5.2%)   │
│  2026-01-15 BALANCED → AGGRESSIVE (Performance↑)    │
│  2026-01-05 DEFENSIVE → BALANCED (Recovery)         │
└─────────────────────────────────────────────────────┘
```

---

## **9.3 상태 메트릭**

상태 관련 핵심 메트릭:

| 메트릭 | 설명 |
|--------|------|
| Time in Current State | 현재 상태 유지 시간 |
| State Transition Count (30d) | 30일간 전이 횟수 |
| Average State Duration | 평균 상태 유지 시간 |
| Forced Transition Count | Safety 강제 전이 횟수 |

---

## **9.4 프로모션 진행 상황**

자본 프로모션 진행률 표시:

```
┌─────────────────────────────────────────────────────┐
│  PROMOTION PROGRESS                                 │
├─────────────────────────────────────────────────────┤
│  Scalp → Swing: 75% to threshold                    │
│  ████████████████████░░░░░░░░  750,000 / 1,000,000  │
│                                                      │
│  Swing → Portfolio: 30% to threshold                │
│  ██████░░░░░░░░░░░░░░░░░░░░░░  1,500,000 / 5,000,000│
└─────────────────────────────────────────────────────┘
```

---

# **10. Testability**

## **10.1 상태 전이 테스트**

각 전이 조건에 대한 단위 테스트:

```python
class TestStateTransitions:
    def test_aggressive_to_balanced_on_drawdown(self):
        metrics = Metrics(drawdown_pct=0.06)
        assert should_transition_aggressive_to_balanced(metrics) == True

    def test_balanced_to_defensive_on_vix(self):
        metrics = Metrics(vix=35)
        assert should_transition_balanced_to_defensive(metrics) == True

    def test_hysteresis_prevents_rapid_transition(self):
        # 최소 유지 기간 미달 시 전이 불가
        state_duration = timedelta(days=2)
        assert can_transition("AGGRESSIVE", "BALANCED", state_duration) == False
```

---

## **10.2 프로모션 테스트**

프로모션 로직 테스트:

```python
class TestPromotion:
    def test_scalp_to_swing_promotion(self):
        pool_state = PoolState(scalp_profit=1500000)
        assert should_promote_scalp_to_swing(pool_state) == True

    def test_promotion_transfer_amount(self):
        profit = 2000000
        ratio = 0.50
        assert calculate_transfer_amount(profit, ratio) == 1000000
```

---

## **10.3 통합 테스트**

상태-ETEDA 통합 테스트:

```python
class TestStateETEDAIntegration:
    def test_defensive_blocks_new_entry(self):
        state = "DEFENSIVE"
        signal = "BUY"
        decision = decide_phase(signal, state)
        assert decision.action == "NONE"

    def test_rebalancing_priority_over_entry(self):
        state = "BALANCED"
        pending_rebalance = True
        decision = decide_phase("BUY", state, pending_rebalance)
        assert decision.action == "REBALANCE"
```

---

# **11. Appendix**

## **11.1 State Transition Diagram**

```
                    ┌─────────────────────────────────────────────────┐
                    │                  AGGRESSIVE                      │
                    │  Scalp: 60-80% | Swing: 15-30% | Portfolio: 5-10%│
                    └─────────────────────┬───────────────────────────┘
                                          │
                      ┌───────────────────┴───────────────────┐
                      │ Drawdown > 5%                         │
                      │ VIX > 25                              │
                      │ Consecutive Scalp Losses > 5          │
                      │ Daily Loss > 2%                       │
                      ▼                                       │
                    ┌─────────────────────────────────────────┴───────┐
    ┌──────────────▶│                   BALANCED                       │
    │               │  Scalp: 30-50% | Swing: 30-40% | Portfolio: 20-30%│
    │               └─────────────────────┬───────────────────────────┘
    │                                     │
    │                 ┌───────────────────┴───────────────────┐
    │                 │ Drawdown > 10%                        │
    │                 │ VIX > 30                              │
    │                 │ Market Circuit Breaker                │
    │                 │ Safety WARNING/FAIL                   │
    │                 ▼                                       │
    │               ┌─────────────────────────────────────────┴───────┐
    │               │                  DEFENSIVE                       │
    │               │  Scalp: 5-15% | Swing: 15-25% | Portfolio: 60-80%│
    │               └─────────────────────┬───────────────────────────┘
    │                                     │
    │                 ┌───────────────────┴───────────────────┐
    │                 │ Drawdown < 5%                         │
    │                 │ VIX < 20                              │
    │                 │ Consecutive Profitable Days >= 3      │
    │                 │ Safety NORMAL                         │
    └─────────────────┴───────────────────────────────────────┘
```

---

## **11.2 Promotion Flow Diagram**

```
SCALP PROFITS ACCUMULATE
         │
         ▼
    ┌─────────────────┐
    │ Check Promotion │
    │ Criteria        │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────────────────────────────────────┐
    │ Profit > 1M? Sharpe > 1.5? WinRate > 55%?       │
    └────────┬────────────────────────────┬───────────┘
             │ YES                         │ NO
             ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │ Transfer 50% of │           │ Continue Scalp  │
    │ profit to Swing │           │ accumulation    │
    └────────┬────────┘           └─────────────────┘
             │
             ▼
    SWING PROFITS ACCUMULATE
             │
             ▼
    ┌─────────────────┐
    │ Check Portfolio │
    │ Promotion       │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────────────────────────────────────┐
    │ Profit > 5M? Sharpe > 1.2? MDD Recovery < 30d?  │
    └────────┬────────────────────────────┬───────────┘
             │ YES                         │ NO
             ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │ Transfer 30% of │           │ Continue Swing  │
    │ profit to Port. │           │ accumulation    │
    └─────────────────┘           └─────────────────┘
```

---

## **11.3 Configuration Examples**

### Config_Local 상태 설정 예시

```json
{
    "SYSTEM_OPERATING_STATE": "BALANCED",
    "STATE_TRANSITION_ENABLED": true,
    "MANUAL_OVERRIDE_ENABLED": true,
    "MAX_OVERRIDE_DURATION_DAYS": 7,

    "AGGRESSIVE_CONFIG": {
        "scalp_allocation_min": 0.60,
        "scalp_allocation_max": 0.80,
        "risk_multiplier": 1.2,
        "entry_threshold": 0.6
    },

    "BALANCED_CONFIG": {
        "scalp_allocation_min": 0.30,
        "scalp_allocation_max": 0.50,
        "risk_multiplier": 1.0,
        "entry_threshold": 0.7
    },

    "DEFENSIVE_CONFIG": {
        "scalp_allocation_min": 0.05,
        "scalp_allocation_max": 0.15,
        "risk_multiplier": 0.5,
        "entry_threshold": 0.9
    },

    "TRANSITION_THRESHOLDS": {
        "drawdown_to_balanced": 0.05,
        "drawdown_to_defensive": 0.10,
        "vix_to_balanced": 25,
        "vix_to_defensive": 30,
        "consecutive_losses_to_balanced": 5
    },

    "PROMOTION_CONFIG": {
        "scalp_to_swing_threshold": 1000000,
        "scalp_to_swing_sharpe": 1.5,
        "swing_to_portfolio_threshold": 5000000,
        "swing_to_portfolio_sharpe": 1.2
    }
}
```

---

**QTS System State and Strategy Promotion Architecture v1.0.0 — 완료됨**
