# ============================================================
# QTS Capital Flow Architecture
# ============================================================

Version: v1.0.0
Status: Architecture Specification (Final)
Author: 타우
Last Updated: 2026-01-30

문서 목적:
본 문서는 QTS의 **자본 흐름(Capital Flow)** 아키텍처를 정의한다.
자본은 파이프라인으로 취급되며, Scalp → Swing → Portfolio 세 개의 자본 풀을
규칙 기반으로 관리한다. 자본 배분과 프로모션은 재량적 판단 없이
데이터 기반 규칙으로만 수행된다.

---

# **1. Overview**

## **1.1 목적**

Capital Flow Architecture는 다음 목표를 수행한다.

1. 3-Track 자본 전략의 풀 구조 정의
2. 규칙 기반 자본 배분 메커니즘 제공
3. 자본 프로모션(승급) 규칙 명세
4. ETEDA 파이프라인과의 통합
5. Safety Layer와의 자본 보호 연계

---

## **1.2 범위**

포함:

- 자본 풀(Scalp/Swing/Portfolio) 모델
- 풀 상태 계약(CapitalPoolContract)
- 자본 배분 규칙
- 풀 간 자본 이동(Promotion/Demotion)
- ETEDA 통합
- Safety 연계

제외:

- 개별 포지션 사이징 (Portfolio Engine 문서 참조)
- 개별 거래 실행 (Trading Engine 문서 참조)
- 전략 신호 생성 (Strategy Engine 문서 참조)

---

## **1.3 설계 원칙**

1. **자본은 파이프라인이다.**
   자본은 Scalp에서 생성되어 Swing으로, Swing에서 Portfolio로 흐른다.

2. **배분은 규칙 기반이다.**
   자본 배분은 감정, 직관, 재량적 판단 없이 데이터 기반 규칙으로만 수행한다.

3. **풀은 독립적이나 연결되어 있다.**
   각 풀은 독립적 계좌처럼 관리되지만 프로모션 규칙으로 연결된다.

4. **Capital Engine ≠ Portfolio Engine**
   Capital Engine은 풀 수준 배분, Portfolio Engine은 종목 수준 배분을 담당한다.

---

## **1.4 관련 문서**

- **Main Architecture**: [../00_Architecture.md](../00_Architecture.md)
- **Engine Core**: [../02_Engine_Core_Architecture.md](../02_Engine_Core_Architecture.md)
- **ETEDA Pipeline**: [../03_Pipeline_ETEDA_Architecture.md](../03_Pipeline_ETEDA_Architecture.md)
- **Fail-Safe & Safety**: [../07_FailSafe_Architecture.md](../07_FailSafe_Architecture.md)
- **System State**: [18_System_State_Promotion_Architecture.md](./18_System_State_Promotion_Architecture.md)
- **Config 3분할**: [../13_Config_3분할_Architecture.md](../13_Config_3분할_Architecture.md)

---

# **2. Capital Pool Model**

## **2.1 풀 계층 구조**

QTS는 세 개의 자본 풀을 계층적으로 관리한다.

```
┌─────────────────────────────────────────────────────────────────────┐
│                       TOTAL CAPITAL (총 자본)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │   SCALP POOL    │    │   SWING POOL    │    │ PORTFOLIO POOL  │  │
│  │                 │    │                 │    │                 │  │
│  │  Purpose:       │    │  Purpose:       │    │  Purpose:       │  │
│  │  Cashflow       │ ──▶│  Compounding    │ ──▶│  Wealth         │  │
│  │  Generation     │    │  Profits        │    │  Preservation   │  │
│  │                 │    │                 │    │                 │  │
│  │  Horizon:       │    │  Horizon:       │    │  Horizon:       │  │
│  │  Ultra-short    │    │  Medium-term    │    │  Long-term      │  │
│  │  (분~시간)      │    │  (일~주)        │    │  (월~년)        │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## **2.2 풀 상태 계약 (CapitalPoolContract)**

각 풀의 상태를 나타내는 데이터 계약:

```python
CapitalPoolContract = {
    "pool_id": "SCALP",
    "version": "1.0.0",
    "timestamp": "2026-01-30T09:30:00Z",

    # 자본 상태
    "total_capital": 10000000,      # 총 배정 자본
    "available_capital": 7500000,    # 사용 가능 자본
    "invested_capital": 2500000,     # 투자 중 자본
    "reserved_capital": 0,           # 예약 자본 (프로모션 대기)

    # 손익 상태
    "realized_pnl": 500000,          # 실현 손익
    "unrealized_pnl": 50000,         # 미실현 손익
    "accumulated_profit": 550000,     # 누적 수익 (프로모션 기준)

    # 배분 비율
    "allocation_pct": 0.40,          # 전체 대비 배분율 (40%)
    "target_allocation_pct": 0.40,   # 목표 배분율

    # 메타데이터
    "last_promotion_time": "2026-01-15T00:00:00Z",
    "promotion_eligible": True,
    "pool_state": "ACTIVE"           # ACTIVE / PAUSED / LOCKED
}
```

---

## **2.3 풀 역할 정의**

### **2.3.1 Scalp Pool**

| 항목 | 값 |
|------|-----|
| **목적** | 현금 흐름(Cashflow) 생성 |
| **투자 기간** | 초단기 (분~시간) |
| **회전율** | 매우 높음 (일 10~50회 거래) |
| **리스크 성향** | 고위험/고빈도 |
| **수익 목표** | 소액 누적 수익 |
| **배정 비율** | Operating State 따라 5%~80% |

### **2.3.2 Swing Pool**

| 항목 | 값 |
|------|-----|
| **목적** | 수익 복리 (Compounding) |
| **투자 기간** | 중기 (일~주) |
| **회전율** | 중간 (주 5~10회 거래) |
| **리스크 성향** | 중위험/중빈도 |
| **수익 목표** | 추세 추종 수익 |
| **배정 비율** | Operating State 따라 15%~40% |

### **2.3.3 Portfolio Pool**

| 항목 | 값 |
|------|-----|
| **목적** | 자산 보존 (Wealth Preservation) |
| **투자 기간** | 장기 (월~년) |
| **회전율** | 낮음 (월 1~5회 거래) |
| **리스크 성향** | 저위험/저빈도 |
| **수익 목표** | 인덱스 수준 또는 배당 |
| **배정 비율** | Operating State 따라 5%~80% |

---

## **2.4 풀 간 관계**

풀은 독립적으로 관리되지만 다음과 같이 연결된다:

```
Scalp Pool
    │
    │  ┌──────────────────────────────────────┐
    │  │ Promotion: 수익 임계값 초과 시       │
    │  │ Scalp 누적 수익 → Swing Pool 이전   │
    │  └──────────────────────────────────────┘
    │
    ▼
Swing Pool
    │
    │  ┌──────────────────────────────────────┐
    │  │ Promotion: 수익 임계값 초과 시       │
    │  │ Swing 누적 수익 → Portfolio Pool 이전│
    │  └──────────────────────────────────────┘
    │
    ▼
Portfolio Pool
```

역방향 이동(Demotion):

```
Portfolio Pool
    │
    │  ┌──────────────────────────────────────┐
    │  │ Demotion: MDD 임계값 초과 시         │
    │  │ Portfolio 일부 → Swing Pool 복귀    │
    │  └──────────────────────────────────────┘
    │
    ▼
Swing Pool
    │
    │  ┌──────────────────────────────────────┐
    │  │ Demotion: MDD 임계값 초과 시         │
    │  │ Swing 일부 → Scalp Pool 복귀        │
    │  └──────────────────────────────────────┘
    │
    ▼
Scalp Pool
```

---

# **3. Capital Allocation Mechanism**

## **3.1 초기 배분 규칙**

신규 계좌 또는 리셋 시 초기 배분:

```python
InitialAllocationRule = {
    "scalp_initial_pct": 1.00,      # 100% Scalp에서 시작
    "swing_initial_pct": 0.00,      # 0% Swing
    "portfolio_initial_pct": 0.00,  # 0% Portfolio

    "reason": "Scalp에서 현금 흐름 생성 후 Swing/Portfolio로 프로모션"
}
```

대안: Operating State 기반 초기 배분

```python
def get_initial_allocation(operating_state: str, total_capital: float):
    if operating_state == "AGGRESSIVE":
        return {
            "scalp": total_capital * 0.70,
            "swing": total_capital * 0.20,
            "portfolio": total_capital * 0.10
        }
    elif operating_state == "BALANCED":
        return {
            "scalp": total_capital * 0.40,
            "swing": total_capital * 0.35,
            "portfolio": total_capital * 0.25
        }
    else:  # DEFENSIVE
        return {
            "scalp": total_capital * 0.10,
            "swing": total_capital * 0.20,
            "portfolio": total_capital * 0.70
        }
```

---

## **3.2 동적 재배분 트리거**

배분 비율이 동적으로 조정되는 조건:

| 트리거 | 조건 | 동작 |
|--------|------|------|
| Operating State 변경 | AGGRESSIVE ↔ BALANCED ↔ DEFENSIVE | 목표 비율 변경 |
| 프로모션 | 수익 임계값 초과 | 풀 간 자본 이동 |
| 디모션 | MDD 임계값 초과 | 역방향 자본 이동 |
| 리밸런싱 | 드리프트 > 10% | 목표 비율로 복귀 |

---

## **3.3 배분 제약 조건**

각 풀의 최소/최대 배분 한도:

```python
AllocationConstraints = {
    "scalp": {
        "min_pct": 0.05,    # 최소 5%
        "max_pct": 0.80,    # 최대 80%
        "min_amount": 1000000  # 최소 100만원
    },
    "swing": {
        "min_pct": 0.10,
        "max_pct": 0.50,
        "min_amount": 2000000
    },
    "portfolio": {
        "min_pct": 0.05,
        "max_pct": 0.80,
        "min_amount": 3000000
    }
}
```

---

## **3.4 긴급 자본 잠금 (Emergency Capital Lock)**

위험 상황 시 자본 이동 차단:

```python
def emergency_capital_lock(pool_id: str, reason: str):
    """긴급 상황 시 풀 자본 잠금"""
    pool = get_pool(pool_id)
    pool.pool_state = "LOCKED"
    pool.lock_reason = reason
    pool.lock_timestamp = now()

    # 모든 프로모션/디모션 중단
    disable_all_transfers(pool_id)

    # Safety Layer 통보
    notify_safety_layer(
        code="FS081",
        message=f"Capital pool {pool_id} locked: {reason}"
    )
```

잠금 조건:

| 조건 | Fail-Safe 코드 |
|------|----------------|
| 풀 MDD > 20% | FS082 |
| 비정상 자본 감소 | FS083 |
| 풀 불일치 감지 | FS084 |
| Safety LOCKDOWN | FS085 |

---

# **4. Capital Promotion Rules**

## **4.1 프로모션 개요**

프로모션은 하위 풀에서 상위 풀로 수익을 이전하는 메커니즘이다.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PROMOTION FLOW                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Scalp 수익 축적                                                    │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────┐                                               │
│  │ 프로모션 조건   │                                               │
│  │ 충족 여부 확인  │                                               │
│  └────────┬────────┘                                               │
│           │ YES                                                     │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │ 이전 금액 계산  │  transfer = profit * transfer_ratio           │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐    ┌─────────────────┐                       │
│  │ Scalp Pool      │ ──▶│ Swing Pool      │                       │
│  │ -transfer       │    │ +transfer       │                       │
│  └─────────────────┘    └─────────────────┘                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## **4.2 Scalp → Swing 프로모션 규칙**

### **4.2.1 프로모션 조건**

모든 조건 충족 시 프로모션 실행:

```python
ScalpToSwingPromotionCriteria = {
    "min_accumulated_profit": 1000000,   # 최소 누적 수익 100만원
    "min_sharpe_ratio": 1.5,             # 최소 샤프 비율
    "min_win_rate_30d": 0.55,            # 최소 30일 승률 55%
    "min_trades_30d": 50,                # 최소 30일 거래 횟수
    "max_mdd_30d": 0.10,                 # 최대 30일 MDD 10%
    "promotion_frequency": "weekly"      # 주간 단위 검토
}
```

### **4.2.2 이전 금액 계산**

```python
def calculate_scalp_to_swing_transfer(pool_state, config):
    if not meets_promotion_criteria(pool_state, ScalpToSwingPromotionCriteria):
        return 0

    # 임계값 초과 수익 계산
    excess_profit = pool_state.accumulated_profit - config.min_accumulated_profit

    # 이전 금액 = 초과 수익 × 이전 비율
    transfer_amount = excess_profit * config.transfer_ratio  # 보통 50%

    # 최소/최대 이전 금액 제한
    transfer_amount = max(transfer_amount, config.min_transfer_amount)
    transfer_amount = min(transfer_amount, config.max_transfer_amount)

    return transfer_amount
```

### **4.2.3 프로모션 실행**

```python
def execute_scalp_to_swing_promotion():
    scalp_pool = get_pool("SCALP")
    swing_pool = get_pool("SWING")

    transfer_amount = calculate_scalp_to_swing_transfer(
        scalp_pool,
        PROMOTION_CONFIG
    )

    if transfer_amount > 0:
        # 원자적 이전
        with capital_transfer_lock():
            scalp_pool.available_capital -= transfer_amount
            scalp_pool.accumulated_profit -= transfer_amount
            scalp_pool.last_promotion_time = now()

            swing_pool.total_capital += transfer_amount
            swing_pool.available_capital += transfer_amount

        # 이벤트 기록
        log_promotion_event(
            from_pool="SCALP",
            to_pool="SWING",
            amount=transfer_amount,
            timestamp=now()
        )
```

---

## **4.3 Swing → Portfolio 프로모션 규칙**

### **4.3.1 프로모션 조건**

```python
SwingToPortfolioPromotionCriteria = {
    "min_accumulated_profit": 5000000,   # 최소 누적 수익 500만원
    "min_sharpe_ratio": 1.2,             # 최소 샤프 비율
    "max_mdd_recovery_days": 30,         # MDD 회복 기간 30일 이내
    "min_holding_period_avg": 5,         # 평균 보유 기간 5일 이상
    "max_mdd_90d": 0.15,                 # 최대 90일 MDD 15%
    "promotion_frequency": "quarterly"   # 분기 단위 검토
}
```

### **4.3.2 이전 금액 계산**

```python
def calculate_swing_to_portfolio_transfer(pool_state, config):
    if not meets_promotion_criteria(pool_state, SwingToPortfolioPromotionCriteria):
        return 0

    excess_profit = pool_state.accumulated_profit - config.min_accumulated_profit
    transfer_amount = excess_profit * config.transfer_ratio  # 보통 30%

    return transfer_amount
```

---

## **4.4 프로모션 주기 및 타이밍**

| 프로모션 | 주기 | 실행 시점 |
|----------|------|-----------|
| Scalp → Swing | 주간 | 매주 월요일 장 시작 전 |
| Swing → Portfolio | 분기 | 분기말 마지막 거래일 장 마감 후 |

```python
PromotionSchedule = {
    "scalp_to_swing": {
        "frequency": "weekly",
        "day_of_week": "monday",
        "time": "08:30"  # 장 시작 전
    },
    "swing_to_portfolio": {
        "frequency": "quarterly",
        "day": "last_trading_day",
        "time": "16:00"  # 장 마감 후
    }
}
```

---

## **4.5 디모션(Demotion) 규칙**

### **4.5.1 Portfolio → Swing 디모션**

| 조건 | 동작 |
|------|------|
| Portfolio MDD > 10% | Portfolio의 20%를 Swing으로 이전 |
| Operating State = AGGRESSIVE | Portfolio를 최소 비율까지 축소 |

### **4.5.2 Swing → Scalp 디모션**

| 조건 | 동작 |
|------|------|
| Swing MDD > 15% | Swing의 30%를 Scalp으로 이전 |
| Consecutive Swing Losses > 5 | Swing의 20%를 Scalp으로 이전 |

```python
DemotionRules = {
    "portfolio_to_swing": {
        "trigger_mdd": 0.10,
        "transfer_ratio": 0.20
    },
    "swing_to_scalp": {
        "trigger_mdd": 0.15,
        "transfer_ratio": 0.30,
        "trigger_consecutive_losses": 5
    }
}
```

---

# **5. Capital Engine Architecture**

## **5.1 Capital Engine 역할**

Capital Engine은 6번째 엔진으로, 풀 수준 자본 배분을 담당한다.

```python
class CapitalEngine:
    """
    역할:
    - 풀 자본 상태 관리
    - 배분 비율 계산
    - 프로모션/디모션 실행
    - ETEDA 통합

    역할이 아닌 것:
    - 개별 종목 포지션 사이징 (Portfolio Engine)
    - 주문 실행 (Trading Engine)
    - 리스크 승인 (Risk Engine)
    """
```

---

## **5.2 Engine Input Contract**

```python
CapitalEngineInput = {
    "total_equity": 30000000,            # 총 자산
    "operating_state": "BALANCED",       # 현재 운영 상태
    "pool_states": {
        "scalp": CapitalPoolContract,
        "swing": CapitalPoolContract,
        "portfolio": CapitalPoolContract
    },
    "performance_metrics": {
        "scalp_sharpe": 1.8,
        "scalp_win_rate": 0.58,
        "swing_mdd": 0.08,
        "portfolio_mdd": 0.05
    },
    "config": CapitalFlowConfig
}
```

---

## **5.3 Engine Output Contract**

```python
CapitalEngineOutput = {
    "allocation_decision": {
        "scalp_target_pct": 0.40,
        "swing_target_pct": 0.35,
        "portfolio_target_pct": 0.25
    },
    "pending_promotions": [
        {
            "from_pool": "SCALP",
            "to_pool": "SWING",
            "amount": 500000,
            "reason": "PROFIT_THRESHOLD_EXCEEDED"
        }
    ],
    "pending_demotions": [],
    "rebalancing_required": False,
    "capital_alerts": []
}
```

---

## **5.4 Engine Algorithm**

```python
class CapitalEngine:
    def evaluate(self, input: CapitalEngineInput) -> CapitalEngineOutput:
        # 1. 현재 상태 기반 목표 배분 계산
        target_allocation = self.calculate_target_allocation(
            input.operating_state,
            input.config
        )

        # 2. 프로모션 조건 확인
        pending_promotions = self.check_promotions(
            input.pool_states,
            input.performance_metrics
        )

        # 3. 디모션 조건 확인
        pending_demotions = self.check_demotions(
            input.pool_states,
            input.performance_metrics
        )

        # 4. 리밸런싱 필요 여부 확인
        rebalancing_required = self.check_rebalancing_needed(
            input.pool_states,
            target_allocation
        )

        # 5. 자본 경고 생성
        capital_alerts = self.generate_alerts(input.pool_states)

        return CapitalEngineOutput(
            allocation_decision=target_allocation,
            pending_promotions=pending_promotions,
            pending_demotions=pending_demotions,
            rebalancing_required=rebalancing_required,
            capital_alerts=capital_alerts
        )
```

---

## **5.5 Capital Engine vs Portfolio Engine**

| 구분 | Capital Engine | Portfolio Engine |
|------|----------------|------------------|
| **범위** | 풀 수준 | 종목 수준 |
| **결정** | Scalp/Swing/Portfolio 배분 | 종목별 포지션 크기 |
| **입력** | 총 자산, 성과 지표 | CalcData, 종목 데이터 |
| **출력** | 풀 배분 비율 | 종목별 목표 수량 |
| **실행 시점** | ETEDA 이전 (Transform) | ETEDA 내 (Evaluate) |

---

# **6. ETEDA Integration**

## **6.1 Extract 단계: 자본 상태 로드**

```python
def extract_phase():
    # 기존 Extract 로직
    raw_data = load_raw_data()

    # 자본 풀 상태 로드 (추가)
    capital_pools = load_capital_pool_states()

    return RawDataContract(
        data=raw_data,
        capital_pools=capital_pools
    )
```

---

## **6.2 Transform 단계: 가용 자본 계산**

```python
def transform_phase(raw_contract):
    # 기존 Transform 로직
    calc_data = calculate_derived_fields(raw_contract)

    # 풀별 가용 자본 계산 (추가)
    for pool in raw_contract.capital_pools:
        pool.available_capital = calculate_available_capital(
            pool.total_capital,
            pool.invested_capital,
            pool.reserved_capital
        )

    # Capital Engine 실행
    capital_decision = CapitalEngine.evaluate(
        CapitalEngineInput(
            total_equity=calc_data.total_equity,
            operating_state=raw_contract.operating_state,
            pool_states=raw_contract.capital_pools
        )
    )

    return CalcDataContract(
        data=calc_data,
        capital_decision=capital_decision
    )
```

---

## **6.3 Evaluate 단계: 자본 제약 적용**

```python
def evaluate_phase(calc_contract):
    capital = calc_contract.capital_decision

    # Scalp Engine - Scalp Pool 자본 제약
    scalp_available = get_pool_available("SCALP")
    scalp_decision = ScalpEngine.evaluate(
        calc_contract,
        max_capital=scalp_available
    )

    # Swing Engine - Swing Pool 자본 제약
    swing_available = get_pool_available("SWING")
    swing_decision = SwingEngine.evaluate(
        calc_contract,
        max_capital=swing_available
    )

    return EvaluationResult(
        scalp=scalp_decision,
        swing=swing_decision,
        capital_decision=capital
    )
```

---

## **6.4 Capital vs Portfolio 경계**

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ETEDA PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Transform Phase:                                                   │
│  ┌─────────────────────────────────────────┐                       │
│  │ Capital Engine                          │                       │
│  │ - 풀 배분 결정                          │                       │
│  │ - 프로모션/디모션 결정                  │                       │
│  │ - Output: CapitalDecision               │                       │
│  └─────────────────────────────────────────┘                       │
│                         │                                           │
│                         ▼                                           │
│  Evaluate Phase:                                                    │
│  ┌─────────────────────────────────────────┐                       │
│  │ Portfolio Engine                        │                       │
│  │ - 풀 내 종목 배분 결정                  │                       │
│  │ - 종목별 목표 수량 계산                 │                       │
│  │ - Input: CapitalDecision.pool_available │                       │
│  │ - Output: PortfolioDecision             │                       │
│  └─────────────────────────────────────────┘                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

# **7. Safety & Guardrails**

## **7.1 Capital Guardrails (GR050-GR059)**

| 코드 | 조건 | 동작 |
|------|------|------|
| GR050 | 풀 배분 합계 ≠ 100% | 경고, 자동 정규화 |
| GR051 | 풀 최소 비율 미달 | 경고, 리밸런싱 트리거 |
| GR052 | 풀 최대 비율 초과 | 경고, 프로모션 차단 |
| GR053 | 프로모션 금액 > 가용 자본 | 프로모션 축소 |
| GR054 | 일일 자본 이동 > 한도 | 이동 지연 |
| GR055 | 풀 간 드리프트 > 10% | 리밸런싱 권고 |

---

## **7.2 Capital Fail-Safe (FS080-FS089)**

| 코드 | 조건 | 동작 |
|------|------|------|
| FS080 | 총 자본 ≤ 0 | ETEDA 중단, LOCKDOWN |
| FS081 | 풀 자본 음수 | 풀 잠금, 조사 필요 |
| FS082 | 풀 MDD > 20% | 풀 잠금, 거래 중단 |
| FS083 | 비정상 자본 변동 | 모든 이동 중단 |
| FS084 | 풀 상태 불일치 | 동기화 후 재개 |
| FS085 | Safety LOCKDOWN | 모든 풀 잠금 |

---

## **7.3 풀 불균형 감지**

```python
def detect_pool_imbalance(pool_states, threshold=0.10):
    """풀 간 비중 불균형 감지"""
    total = sum(p.total_capital for p in pool_states.values())

    for pool_id, pool in pool_states.items():
        actual_pct = pool.total_capital / total
        target_pct = pool.target_allocation_pct
        drift = abs(actual_pct - target_pct)

        if drift > threshold:
            trigger_guardrail(
                code="GR055",
                message=f"Pool {pool_id} drift: {drift:.2%} > {threshold:.2%}"
            )
```

---

# **8. Testability**

## **8.1 풀 상태 테스트**

```python
class TestCapitalPoolState:
    def test_available_capital_calculation(self):
        pool = CapitalPool(
            total_capital=10000000,
            invested_capital=3000000,
            reserved_capital=500000
        )
        assert pool.available_capital == 6500000

    def test_pool_state_validation(self):
        # 유효하지 않은 상태
        pool = CapitalPool(invested_capital=15000000, total_capital=10000000)
        assert pool.is_valid() == False
```

---

## **8.2 프로모션 테스트**

```python
class TestPromotion:
    def test_scalp_to_swing_promotion_criteria(self):
        pool_state = CapitalPoolState(
            accumulated_profit=1500000,
            sharpe_ratio=1.8,
            win_rate_30d=0.58
        )
        assert should_promote_scalp_to_swing(pool_state) == True

    def test_promotion_amount_calculation(self):
        profit = 2000000
        threshold = 1000000
        ratio = 0.50
        expected = (2000000 - 1000000) * 0.50
        assert calculate_transfer_amount(profit, threshold, ratio) == 500000
```

---

## **8.3 통합 테스트**

```python
class TestCapitalETEDAIntegration:
    def test_capital_constraint_in_evaluate(self):
        scalp_available = 1000000
        order_size = 2000000  # 가용 자본 초과

        decision = evaluate_with_capital_constraint(order_size, scalp_available)
        assert decision.adjusted_qty <= scalp_available

    def test_promotion_execution(self):
        initial_scalp = 10000000
        initial_swing = 5000000
        transfer = 500000

        execute_promotion("SCALP", "SWING", transfer)

        assert get_pool("SCALP").total_capital == initial_scalp - transfer
        assert get_pool("SWING").total_capital == initial_swing + transfer
```

---

# **9. Appendix**

## **9.1 CapitalPoolContract Schema**

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "CapitalPoolContract",
    "type": "object",
    "required": ["pool_id", "version", "timestamp", "total_capital"],
    "properties": {
        "pool_id": {
            "type": "string",
            "enum": ["SCALP", "SWING", "PORTFOLIO"]
        },
        "version": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "total_capital": {"type": "number", "minimum": 0},
        "available_capital": {"type": "number", "minimum": 0},
        "invested_capital": {"type": "number", "minimum": 0},
        "reserved_capital": {"type": "number", "minimum": 0},
        "realized_pnl": {"type": "number"},
        "unrealized_pnl": {"type": "number"},
        "accumulated_profit": {"type": "number"},
        "allocation_pct": {"type": "number", "minimum": 0, "maximum": 1},
        "target_allocation_pct": {"type": "number", "minimum": 0, "maximum": 1},
        "last_promotion_time": {"type": "string", "format": "date-time"},
        "promotion_eligible": {"type": "boolean"},
        "pool_state": {
            "type": "string",
            "enum": ["ACTIVE", "PAUSED", "LOCKED"]
        }
    }
}
```

---

## **9.2 Promotion State Diagram**

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PROMOTION STATE MACHINE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐                                               │
│  │   ACCUMULATING  │◀─────────────────────────────────┐            │
│  │                 │                                   │            │
│  │  Scalp 수익     │                                   │            │
│  │  축적 중        │                                   │            │
│  └────────┬────────┘                                   │            │
│           │                                            │            │
│           │ Criteria Met                               │            │
│           ▼                                            │            │
│  ┌─────────────────┐                                   │            │
│  │ PROMOTION_READY │                                   │            │
│  │                 │                                   │            │
│  │ 프로모션 조건   │                                   │            │
│  │ 충족            │                                   │            │
│  └────────┬────────┘                                   │            │
│           │                                            │            │
│           │ Scheduled Time                             │            │
│           ▼                                            │            │
│  ┌─────────────────┐                                   │            │
│  │   TRANSFERRING  │                                   │            │
│  │                 │                                   │            │
│  │ 자본 이전 중    │                                   │            │
│  └────────┬────────┘                                   │            │
│           │                                            │            │
│           │ Transfer Complete                          │            │
│           ▼                                            │            │
│  ┌─────────────────┐                                   │            │
│  │   COMPLETED     │───────────────────────────────────┘            │
│  │                 │   Reset accumulated_profit                     │
│  │ 프로모션 완료   │                                                │
│  └─────────────────┘                                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## **9.3 Example Scenarios**

### **Scenario 1: 정상 프로모션**

```
초기 상태:
- Scalp Pool: 10,000,000원
- Swing Pool: 5,000,000원
- Scalp 누적 수익: 1,500,000원

프로모션 조건 확인:
- 누적 수익 (1,500,000) > 임계값 (1,000,000) ✓
- Sharpe (1.8) > 최소 (1.5) ✓
- 승률 (58%) > 최소 (55%) ✓

이전 금액 계산:
- 초과 수익 = 1,500,000 - 1,000,000 = 500,000
- 이전 금액 = 500,000 × 0.5 = 250,000

실행 후:
- Scalp Pool: 9,750,000원 (누적 수익 리셋)
- Swing Pool: 5,250,000원
```

### **Scenario 2: 디모션**

```
초기 상태:
- Swing Pool: 8,000,000원
- Swing MDD: 18%

디모션 조건 확인:
- MDD (18%) > 임계값 (15%) ✓

이전 금액 계산:
- 이전 금액 = 8,000,000 × 0.3 = 2,400,000

실행 후:
- Swing Pool: 5,600,000원
- Scalp Pool: +2,400,000원
```

---

**QTS Capital Flow Architecture v1.0.0 — 완료됨**
