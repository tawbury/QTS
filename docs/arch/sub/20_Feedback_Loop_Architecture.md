# ============================================================
# QTS Feedback Loop Architecture
# ============================================================

Version: v1.0.0
Status: Architecture Specification (Final)
Author: AI Architect
Last Updated: 2026-01-31

문서 목적:
본 문서는 QTS의 **Feedback Loop 아키텍처**를 정의한다.
scalp_ticks 실행 데이터를 Evaluate 엔진 학습에 활용하여
실행 품질 개선, 슬리피지 예측, 시장 충격 최소화를 달성하는
Continuous Improvement Loop를 상세히 기술한다.

---

# **1. Overview**

## **1.1 목적**

QTS Feedback Loop는 다음 목표를 달성한다:

1. **Execution Quality Improvement**: 실행 품질 데이터 기반 전략 최적화
2. **Slippage Prediction**: 종목별/시간대별 슬리피지 패턴 학습
3. **Market Impact Estimation**: 주문 크기에 따른 시장 충격 추정
4. **Adaptive Strategy**: 피드백 기반 전략 파라미터 동적 조정
5. **Continuous Learning**: 실행 → 분석 → 학습 → 개선 사이클

---

## **1.2 범위**

포함:

- Feedback Data 수집 및 저장
- Feedback Aggregator 설계
- Strategy Engine Feedback Integration
- Learning Pipeline 구조
- Performance Metrics 및 KPI

제외:

- ML 모델 학습 알고리즘 상세 (→ ML/Data Science 팀)
- 브로커별 실행 차이 분석 (→ Broker Integration)
- UI 대시보드 (→ UI Architecture)

---

## **1.3 관련 문서**

- **Engine Core**: [../02_Engine_Core_Architecture.md](../02_Engine_Core_Architecture.md)
- **Scalp Execution**: [15_Scalp_Execution_Micro_Architecture.md](./15_Scalp_Execution_Micro_Architecture.md)
- **Data Layer**: [18_Data_Layer_Architecture.md](./18_Data_Layer_Architecture.md)
- **ETEDA Pipeline**: [../03_Pipeline_ETEDA_Architecture.md](../03_Pipeline_ETEDA_Architecture.md)

---

## **1.4 설계 원칙**

1. **Feedback는 비동기**: 실행 경로에 영향 없음
2. **저장 우선, 분석은 나중**: 모든 실행 데이터는 즉시 저장
3. **Incremental Learning**: 점진적 학습, 전체 재학습 불필요
4. **Explainable**: 피드백 결과는 설명 가능해야 함
5. **Fail-Safe**: 피드백 실패가 매매 중단으로 이어지지 않음

---

# **2. Feedback Loop Architecture**

## **2.1 Feedback Flow Overview**

```
┌──────────────────────────────────────────────────────────────────┐
│                    FEEDBACK LOOP FLOW                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   EXECUTION PHASE                        │    │
│  │                                                           │    │
│  │  Scalp Execution Micro-Pipeline                          │    │
│  │  (PreCheck → Split → Send → Monitor → Adjust → Escape)  │    │
│  │                           │                              │    │
│  │                           ▼                              │    │
│  │                    ExecutionResult                       │    │
│  │                    + scalp_ticks[]                       │    │
│  │                    + fill_events[]                       │    │
│  │                    + latency_logs[]                      │    │
│  └───────────────────────┬─────────────────────────────────┘    │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              DATA COLLECTION PHASE                       │    │
│  │                                                           │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐│    │
│  │  │ Tick Store    │  │ Fill Store    │  │ Execution Log││    │
│  │  │ (TimescaleDB) │  │ (T_Ledger)    │  │ (execution_  ││    │
│  │  │               │  │               │  │  logs)       ││    │
│  │  └───────┬───────┘  └───────┬───────┘  └──────┬───────┘│    │
│  │          │                  │                  │        │    │
│  │          └──────────────────┴──────────────────┘        │    │
│  │                             │                           │    │
│  └─────────────────────────────┼───────────────────────────┘    │
│                                │                                │
│                                ▼                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              AGGREGATION PHASE                           │    │
│  │                                                           │    │
│  │            Feedback Aggregator (Batch Job)               │    │
│  │                                                           │    │
│  │  Input:                                                  │    │
│  │  - scalp_ticks (price, volume, timestamp)               │    │
│  │  - execution_fills (qty, price, slippage)               │    │
│  │  - market_context (volatility, spread, depth)           │    │
│  │                                                           │    │
│  │  Processing:                                             │    │
│  │  - Slippage Calculation                                  │    │
│  │  - Market Impact Estimation                              │    │
│  │  - Execution Quality Scoring                             │    │
│  │  - Pattern Recognition                                   │    │
│  │                                                           │    │
│  │  Output:                                                 │    │
│  │  - FeedbackData (Symbol × TimeSlot × Metrics)           │    │
│  │                                                           │    │
│  └─────────────────────────┬───────────────────────────────┘    │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              LEARNING PHASE (Optional ML)                │    │
│  │                                                           │    │
│  │  - Slippage Prediction Model Update                      │    │
│  │  - Market Impact Regression                              │    │
│  │  - Optimal Timing Prediction                             │    │
│  │                                                           │    │
│  └─────────────────────────┬───────────────────────────────┘    │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │          STRATEGY ENHANCEMENT (Next Cycle)               │    │
│  │                                                           │    │
│  │                Strategy Engine Input:                    │    │
│  │                + historical_slippage_by_symbol           │    │
│  │                + execution_quality_score                 │    │
│  │                + market_impact_estimation                │    │
│  │                + optimal_entry_timing                    │    │
│  │                                                           │    │
│  │                Improved Decision:                        │    │
│  │                - Slippage-adjusted entry price           │    │
│  │                - Volume-aware position sizing            │    │
│  │                - Market impact-aware timing              │    │
│  │                                                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## **2.2 Data Collection Points**

| Collection Point | Data Source | Frequency | Storage |
|-----------------|-------------|-----------|---------|
| Tick Data | Market Feed | Real-time | tick_data (TimescaleDB) |
| Fill Events | Broker Callback | On Fill | t_ledger |
| Execution Logs | Scalp Pipeline | Per Stage | execution_logs |
| Market Context | Market Feed | 1s | Derived from tick_data |

---

# **3. Feedback Data Contract**

## **3.1 FeedbackData Structure**

```python
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

@dataclass
class FeedbackData:
    """Execution → Strategy 피드백 데이터"""

    # Metadata
    symbol: str
    execution_start: datetime
    execution_end: datetime
    feedback_generated_at: datetime

    # Tick Data
    scalp_ticks: List[TickRecord]

    # Execution Metrics
    total_slippage_bps: float             # 총 슬리피지 (basis points)
    avg_fill_latency_ms: float            # 평균 체결 지연 (ms)
    partial_fill_ratio: float             # 부분 체결 비율 (0.0 ~ 1.0)
    total_filled_qty: Decimal             # 총 체결 수량
    avg_fill_price: Decimal               # 평균 체결가

    # Market Context at Execution
    volatility_at_execution: float        # ATR 기반 변동성
    spread_at_execution: Decimal          # Bid-Ask Spread (bps)
    depth_at_execution: int               # 호가창 깊이 (상위 5단계 합)

    # Learning Signals
    execution_quality_score: float        # 실행 품질 점수 (0.0 ~ 1.0)
    market_impact_bps: float              # 시장 충격 (basis points)

    # Strategy Context
    strategy_tag: str                     # 전략 ID
    order_type: str                       # MARKET / LIMIT
    original_qty: Decimal                 # 원래 주문 수량


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

## **3.2 Slippage Calculation**

```python
def calculate_slippage_bps(
    decision_price: Decimal,
    avg_fill_price: Decimal
) -> float:
    """슬리피지 계산 (basis points)"""
    slippage = (avg_fill_price - decision_price) / decision_price
    return float(slippage * 10000)  # bps


# Example
decision_price = Decimal("75000")
avg_fill_price = Decimal("75050")
slippage_bps = calculate_slippage_bps(decision_price, avg_fill_price)
# Result: 6.67 bps
```

**Slippage 구성요소:**
- Spread Cost: Bid-Ask 스프레드
- Market Impact: 주문 크기에 따른 가격 이동
- Timing Cost: 주문 시점과 체결 시점 가격 변화

---

## **3.3 Execution Quality Score**

```python
def calculate_execution_quality_score(feedback: FeedbackData) -> float:
    """실행 품질 점수 (0.0 = worst, 1.0 = best)"""

    # 1. Slippage Score (낮을수록 좋음)
    slippage_penalty = min(abs(feedback.total_slippage_bps) / 50, 1.0)  # 50bps 이상 = 0점
    slippage_score = 1.0 - slippage_penalty

    # 2. Fill Ratio Score (높을수록 좋음)
    fill_score = 1.0 - feedback.partial_fill_ratio

    # 3. Latency Score (낮을수록 좋음)
    latency_penalty = min(feedback.avg_fill_latency_ms / 1000, 1.0)  # 1000ms 이상 = 0점
    latency_score = 1.0 - latency_penalty

    # Weighted Average
    quality_score = (
        slippage_score * 0.5 +
        fill_score * 0.3 +
        latency_score * 0.2
    )

    return quality_score
```

---

## **3.4 Market Impact Estimation**

```python
def estimate_market_impact_bps(
    order_qty: Decimal,
    avg_daily_volume: int,
    spread_bps: float
) -> float:
    """시장 충격 추정 (Kyle's Lambda 모델 단순화)"""

    participation_rate = float(order_qty) / avg_daily_volume

    # Simplified: Impact = Spread × sqrt(Participation Rate)
    impact_multiplier = (participation_rate ** 0.5)
    market_impact_bps = spread_bps * impact_multiplier * 10  # 경험적 계수

    return market_impact_bps


# Example
order_qty = Decimal("1000")
avg_daily_volume = 1000000
spread_bps = 5.0
impact = estimate_market_impact_bps(order_qty, avg_daily_volume, spread_bps)
# Result: ~1.58 bps
```

---

# **4. Feedback Aggregator**

## **4.1 Aggregation Architecture**

```python
class FeedbackAggregator:
    """실행 데이터 → 피드백 데이터 변환"""

    def __init__(self, db_adapter):
        self.db = db_adapter

    async def aggregate_feedback(
        self,
        execution_result: ExecutionResult
    ) -> FeedbackData:
        """ExecutionResult로부터 FeedbackData 생성"""

        symbol = execution_result.symbol
        start_time = execution_result.execution_start
        end_time = execution_result.execution_end

        # 1. Tick Data 조회
        ticks = await self.db.fetch_tick_data(symbol, start_time, end_time)

        # 2. Fill Events 조회
        fills = await self.db.fetch_fills(execution_result.order_id)

        # 3. Execution Logs 조회
        logs = await self.db.fetch_execution_logs(execution_result.order_id)

        # 4. Slippage 계산
        slippage_bps = calculate_slippage_bps(
            execution_result.decision_price,
            execution_result.avg_fill_price
        )

        # 5. Market Context 계산
        volatility = calculate_volatility(ticks)
        spread = calculate_spread(ticks)
        depth = calculate_depth(ticks)

        # 6. Execution Quality Score
        quality_score = calculate_execution_quality_score(FeedbackData(...))

        # 7. Market Impact Estimation
        market_impact = estimate_market_impact_bps(
            execution_result.total_filled_qty,
            await self.get_avg_daily_volume(symbol),
            spread
        )

        return FeedbackData(
            symbol=symbol,
            execution_start=start_time,
            execution_end=end_time,
            feedback_generated_at=datetime.now(),
            scalp_ticks=ticks,
            total_slippage_bps=slippage_bps,
            avg_fill_latency_ms=calculate_avg_latency(logs),
            partial_fill_ratio=calculate_partial_fill_ratio(fills),
            total_filled_qty=execution_result.total_filled_qty,
            avg_fill_price=execution_result.avg_fill_price,
            volatility_at_execution=volatility,
            spread_at_execution=spread,
            depth_at_execution=depth,
            execution_quality_score=quality_score,
            market_impact_bps=market_impact,
            strategy_tag=execution_result.strategy_tag,
            order_type=execution_result.order_type,
            original_qty=execution_result.original_qty
        )
```

---

## **4.2 Batch Processing Schedule**

```python
# Feedback Aggregation은 비동기 Batch Job
# - Execution 직후 즉시 수행 (Real-time)
# - 또는 1분마다 일괄 수행 (Batch)

async def feedback_batch_job():
    """1분마다 실행되는 피드백 집계"""
    while True:
        # 최근 1분간 완료된 모든 ExecutionResult 조회
        recent_executions = await db.fetch_recent_executions(since=datetime.now() - timedelta(minutes=1))

        for exec_result in recent_executions:
            try:
                feedback = await aggregator.aggregate_feedback(exec_result)
                await db.store_feedback(feedback)
                log_info(f"Feedback aggregated: {exec_result.order_id}")
            except Exception as e:
                log_error(f"Feedback aggregation failed: {e}")

        await asyncio.sleep(60)  # 1분 대기
```

---

## **4.3 Feedback Storage**

```sql
-- feedback_data 테이블 (TimescaleDB Hypertable)
CREATE TABLE feedback_data (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    strategy_tag VARCHAR(50),

    -- Execution Metrics
    total_slippage_bps DECIMAL(10, 3),
    avg_fill_latency_ms DECIMAL(10, 3),
    partial_fill_ratio DECIMAL(5, 4),
    total_filled_qty DECIMAL(18, 8),
    avg_fill_price DECIMAL(18, 8),

    -- Market Context
    volatility_at_execution DECIMAL(10, 6),
    spread_at_execution DECIMAL(10, 3),
    depth_at_execution INT,

    -- Learning Signals
    execution_quality_score DECIMAL(5, 4),
    market_impact_bps DECIMAL(10, 3),

    -- Metadata
    order_type VARCHAR(20),
    original_qty DECIMAL(18, 8)
);

SELECT create_hypertable('feedback_data', 'time', chunk_time_interval => INTERVAL '7 days');

-- Indexes
CREATE INDEX idx_feedback_symbol_time ON feedback_data (symbol, time DESC);
CREATE INDEX idx_feedback_strategy_time ON feedback_data (strategy_tag, time DESC);

-- Retention Policy (180일 보존)
SELECT add_retention_policy('feedback_data', INTERVAL '180 days');
```

---

# **5. Strategy Engine Integration**

## **5.1 Feedback-Enhanced Strategy Input**

```python
@dataclass
class StrategyInputEnhanced:
    """기존 StrategyInput + Feedback Data"""

    # Original Fields
    symbol_data: SymbolData
    position_data: PositionData
    strategy_params: StrategyParams
    market_context: MarketContext

    # Feedback Fields (NEW)
    historical_slippage_bps: float           # 종목별 평균 슬리피지
    execution_quality_score: float           # 최근 실행 품질 점수
    market_impact_estimation: float          # 예상 시장 충격
    optimal_entry_timing: Optional[datetime] # ML 기반 최적 진입 시점
```

---

## **5.2 Slippage-Adjusted Entry Price**

```python
def calculate_adjusted_entry_price(
    signal_price: Decimal,
    historical_slippage_bps: float,
    side: str  # BUY / SELL
) -> Decimal:
    """슬리피지 보정 진입가 계산"""

    slippage_factor = Decimal(str(historical_slippage_bps / 10000))

    if side == "BUY":
        # 매수 시 슬리피지만큼 높은 가격 예상
        adjusted_price = signal_price * (1 + slippage_factor)
    else:
        # 매도 시 슬리피지만큼 낮은 가격 예상
        adjusted_price = signal_price * (1 - slippage_factor)

    return adjusted_price


# Example
signal_price = Decimal("75000")
historical_slippage_bps = 10.0  # 평균 10bps 슬리피지
adjusted = calculate_adjusted_entry_price(signal_price, historical_slippage_bps, "BUY")
# Result: 75075 (0.1% 높게 설정)
```

---

## **5.3 Volume-Aware Position Sizing**

```python
def adjust_qty_for_market_impact(
    target_qty: Decimal,
    estimated_impact_bps: float,
    max_acceptable_impact_bps: float = 20.0
) -> Decimal:
    """시장 충격 기반 수량 조정"""

    if estimated_impact_bps <= max_acceptable_impact_bps:
        return target_qty

    # Impact가 너무 크면 수량 축소
    reduction_ratio = max_acceptable_impact_bps / estimated_impact_bps
    adjusted_qty = target_qty * Decimal(str(reduction_ratio))

    log_warning(f"Qty reduced due to market impact: {target_qty} → {adjusted_qty}")

    return adjusted_qty


# Example
target_qty = Decimal("1000")
estimated_impact = 50.0  # 50bps
max_impact = 20.0
adjusted = adjust_qty_for_market_impact(target_qty, estimated_impact, max_impact)
# Result: 400 (40% 축소)
```

---

## **5.4 Strategy Engine with Feedback**

```python
class FeedbackAwareStrategyEngine:
    def __init__(self, db_adapter):
        self.db = db_adapter

    async def run_strategy(
        self,
        input: StrategyInput
    ) -> StrategyDecision:
        # 1. 기본 신호 생성
        raw_signal = self.calculate_raw_signal(input)

        # 2. 피드백 데이터 조회
        feedback = await self.get_historical_feedback(input.symbol)

        # 3. 슬리피지 보정
        adjusted_price = calculate_adjusted_entry_price(
            raw_signal.entry_price,
            feedback.avg_slippage_bps,
            raw_signal.side
        )

        # 4. 시장 충격 기반 수량 조정
        adjusted_qty = adjust_qty_for_market_impact(
            raw_signal.qty,
            feedback.avg_market_impact_bps,
            max_acceptable_impact_bps=20.0
        )

        return StrategyDecision(
            signal=raw_signal.signal,
            entry_price=adjusted_price,
            recommended_qty=adjusted_qty,
            confidence=raw_signal.confidence * feedback.avg_quality_score,
            reason=f"Feedback-adjusted: slippage={feedback.avg_slippage_bps:.2f}bps, impact={feedback.avg_market_impact_bps:.2f}bps"
        )

    async def get_historical_feedback(self, symbol: str):
        """최근 30일 피드백 데이터 조회 및 집계"""
        rows = await self.db.fetch_feedback(
            symbol=symbol,
            since=datetime.now() - timedelta(days=30)
        )

        return FeedbackSummary(
            avg_slippage_bps=mean([r.total_slippage_bps for r in rows]),
            avg_market_impact_bps=mean([r.market_impact_bps for r in rows]),
            avg_quality_score=mean([r.execution_quality_score for r in rows])
        )
```

---

# **6. Learning Pipeline (Optional ML)**

## **6.1 ML Model Integration Point**

```python
class SlippagePredictionModel:
    """ML 기반 슬리피지 예측 모델 (Optional)"""

    def predict_slippage(
        self,
        symbol: str,
        order_qty: Decimal,
        time_of_day: datetime,
        volatility: float,
        spread: Decimal
    ) -> float:
        """예상 슬리피지 (bps) 반환"""

        # Feature Engineering
        features = {
            "symbol": symbol,
            "qty": float(order_qty),
            "hour": time_of_day.hour,
            "minute": time_of_day.minute,
            "volatility": volatility,
            "spread_bps": float(spread * 10000),
        }

        # ML Prediction (예: XGBoost, LightGBM)
        predicted_slippage_bps = self.model.predict(features)

        return predicted_slippage_bps
```

---

## **6.2 Model Training Pipeline**

```python
async def train_slippage_model():
    """주기적 모델 재학습 (예: 매주 일요일)"""

    # 1. 학습 데이터 조회 (최근 90일)
    training_data = await db.fetch_feedback(
        since=datetime.now() - timedelta(days=90)
    )

    # 2. Feature Engineering
    X, y = prepare_training_data(training_data)

    # 3. Model Training
    model = train_xgboost(X, y)

    # 4. Model Evaluation
    score = evaluate_model(model, test_data)
    log_info(f"Model trained: R² = {score:.4f}")

    # 5. Model Deployment
    save_model(model, "slippage_model_v2.pkl")
```

---

# **7. Performance Metrics & KPIs**

## **7.1 Execution Quality KPIs**

| Metric | Target | Measurement |
|--------|--------|-------------|
| Avg Slippage | < 10 bps | Mean(total_slippage_bps) |
| Execution Quality Score | > 0.85 | Mean(execution_quality_score) |
| Fill Ratio | > 95% | 1 - Mean(partial_fill_ratio) |
| Avg Fill Latency | < 100ms | Mean(avg_fill_latency_ms) |
| Market Impact | < 15 bps | Mean(market_impact_bps) |

---

## **7.2 Feedback Loop Health Metrics**

```python
# Feedback Coverage Rate
feedback_coverage = (
    count(feedback_data) / count(executions)
)
# Target: > 99%

# Feedback Latency (실행 완료 → 피드백 생성)
feedback_latency_ms = (
    feedback_generated_at - execution_end
).total_seconds() * 1000
# Target: < 60s

# Model Accuracy (if ML enabled)
model_accuracy = 1 - abs(
    predicted_slippage - actual_slippage
) / actual_slippage
# Target: > 0.8 (80% 정확도)
```

---

## **7.3 Dashboard Visualization**

```sql
-- 종목별 평균 슬리피지 (최근 30일)
SELECT
    symbol,
    avg(total_slippage_bps) AS avg_slippage_bps,
    count(*) AS execution_count
FROM feedback_data
WHERE time >= NOW() - INTERVAL '30 days'
GROUP BY symbol
ORDER BY avg_slippage_bps DESC;

-- 시간대별 실행 품질
SELECT
    time_bucket('1 hour', time) AS hour,
    avg(execution_quality_score) AS avg_quality,
    count(*) AS count
FROM feedback_data
WHERE time >= NOW() - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour;

-- 전략별 시장 충격
SELECT
    strategy_tag,
    avg(market_impact_bps) AS avg_impact,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY market_impact_bps) AS p95_impact
FROM feedback_data
WHERE time >= NOW() - INTERVAL '30 days'
GROUP BY strategy_tag;
```

---

# **8. Failure Handling**

## **8.1 Feedback Aggregation Failure**

```python
async def safe_aggregate_feedback(execution_result):
    """Fail-Safe Feedback Aggregation"""
    try:
        feedback = await aggregator.aggregate_feedback(execution_result)
        await db.store_feedback(feedback)
        return feedback
    except Exception as e:
        log_error(f"Feedback aggregation failed: {e}")
        # Execution 자체는 성공했으므로 계속 진행
        return None
```

**원칙**: 피드백 실패가 매매를 중단시키지 않음.

---

## **8.2 Feedback Data Missing**

```python
async def get_historical_feedback_with_fallback(symbol: str):
    """피드백 데이터 없을 때 Fallback"""
    try:
        feedback = await db.fetch_feedback(symbol)
        if not feedback:
            # 피드백 데이터 없음 - 기본값 사용
            log_warning(f"No feedback data for {symbol}, using defaults")
            return FeedbackSummary(
                avg_slippage_bps=10.0,  # Conservative default
                avg_market_impact_bps=15.0,
                avg_quality_score=0.75
            )
        return feedback
    except Exception as e:
        log_error(f"Feedback query failed: {e}")
        return FeedbackSummary(
            avg_slippage_bps=10.0,
            avg_market_impact_bps=15.0,
            avg_quality_score=0.75
        )
```

---

# **9. Appendix**

## **9.1 Complete Feedback Query Examples**

```sql
-- 1. 최근 1시간 삼성전자 실행 품질
SELECT
    avg(execution_quality_score) AS avg_quality,
    avg(total_slippage_bps) AS avg_slippage,
    count(*) AS count
FROM feedback_data
WHERE symbol = '005930'
  AND time >= NOW() - INTERVAL '1 hour';

-- 2. Scalp 전략 슬리피지 분포
SELECT
    percentile_cont(0.50) WITHIN GROUP (ORDER BY total_slippage_bps) AS p50_slippage,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY total_slippage_bps) AS p95_slippage,
    percentile_cont(0.99) WITHIN GROUP (ORDER BY total_slippage_bps) AS p99_slippage
FROM feedback_data
WHERE strategy_tag = 'SCALP'
  AND time >= NOW() - INTERVAL '7 days';

-- 3. 시장 충격 vs 주문 크기 상관관계
SELECT
    CASE
        WHEN original_qty < 100 THEN 'Small'
        WHEN original_qty < 500 THEN 'Medium'
        ELSE 'Large'
    END AS order_size,
    avg(market_impact_bps) AS avg_impact
FROM feedback_data
WHERE time >= NOW() - INTERVAL '30 days'
GROUP BY order_size;
```

---

## **9.2 Feedback Data Sample**

```json
{
  "symbol": "005930",
  "execution_start": "2026-01-31T09:30:00.000Z",
  "execution_end": "2026-01-31T09:30:05.123Z",
  "feedback_generated_at": "2026-01-31T09:30:10.456Z",
  "scalp_ticks": [...],
  "total_slippage_bps": 8.5,
  "avg_fill_latency_ms": 45.2,
  "partial_fill_ratio": 0.0,
  "total_filled_qty": 100,
  "avg_fill_price": 75063.5,
  "volatility_at_execution": 0.012,
  "spread_at_execution": 5.3,
  "depth_at_execution": 15000,
  "execution_quality_score": 0.92,
  "market_impact_bps": 3.2,
  "strategy_tag": "SCALP_RSI",
  "order_type": "LIMIT",
  "original_qty": 100
}
```

---

**QTS Feedback Loop Architecture v1.0.0 — 완료됨**
