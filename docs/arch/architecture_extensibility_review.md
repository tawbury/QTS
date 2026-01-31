# QTS Architecture Extensibility Review

Version: v1.0.0
Status: Technical Review Report
Author: AI Code Auditor
Date: 2026-01-31

---

## Executive Summary

본 보고서는 QTS(Quantitative Trading System) 아키텍처 문서(`docs/arch/`)를 확장성 관점에서 검토한 결과입니다.

### 주요 발견사항

| 영역 | 현재 상태 | 권장 방향 | 우선순위 |
|------|----------|----------|---------|
| Data Layer | Google Sheets + Local JSON | PostgreSQL + TimescaleDB | **P0** |
| Feedback Loop | 미정의 | scalp_ticks → Evaluate 학습 파이프라인 | **P1** |
| Caching Tier | 없음 | Redis In-Memory Cache | **P1** |
| Latency Optimization | 문서화됨 (100ms 목표) | Redis + Async 강화 | **P2** |

**Overall Extensibility Score: 72/100**

---

## 1. Data Layer Analysis

### 1.1 Current State (현재 상태)

현재 데이터 저장소 구조 (`01_Schema_Auto_Architecture.md`, `04_Data_Contract_Spec.md` 참조):

```
┌─────────────────────────────────────────────────────────────┐
│                    현재 데이터 저장소                        │
├─────────────────────────────────────────────────────────────┤
│  Google Sheets (10개 시트)                                  │
│  ├── Position (포지션)                                      │
│  ├── T_Ledger (거래 원장)                                   │
│  ├── History (일봉/분봉)                                    │
│  ├── Strategy (전략 파라미터)                               │
│  ├── Config (설정)                                          │
│  ├── Risk Config (리스크 설정)                              │
│  └── ... (6개 추가 시트)                                    │
│                                                              │
│  Local JSON Files                                           │
│  ├── schema.json                                            │
│  └── dividend.json                                          │
│                                                              │
│  Git DB (버전 관리용)                                        │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Limitations (제한사항)

1. **Time-Series 미지원**: Google Sheets는 시계열 쿼리에 부적합
2. **동시성 제한**: 다중 프로세스 동시 쓰기 불가
3. **쿼리 성능**: 복잡한 집계 쿼리 불가능
4. **데이터 볼륨**: 대용량 틱 데이터 저장 불가
5. **Latency**: API 호출 오버헤드 (100-500ms per request)

### 1.3 Recommended Architecture: PostgreSQL + TimescaleDB

```
┌─────────────────────────────────────────────────────────────────────┐
│                     권장 데이터 아키텍처                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    PostgreSQL + TimescaleDB                 │    │
│  │                                                              │    │
│  │  Hypertables (자동 파티셔닝)                                │    │
│  │  ├── tick_data          (시간 기반 자동 청크)               │    │
│  │  ├── ohlcv_1m           (1분봉 집계)                        │    │
│  │  ├── ohlcv_1d           (일봉 집계)                         │    │
│  │  └── execution_logs     (실행 로그)                         │    │
│  │                                                              │    │
│  │  Regular Tables                                              │    │
│  │  ├── positions          (현재 포지션)                       │    │
│  │  ├── strategies         (전략 파라미터)                     │    │
│  │  ├── risk_configs       (리스크 설정)                       │    │
│  │  └── t_ledger           (거래 원장)                         │    │
│  │                                                              │    │
│  │  Continuous Aggregates (실시간 집계 뷰)                     │    │
│  │  ├── hourly_pnl         (시간별 손익)                       │    │
│  │  ├── daily_metrics      (일별 지표)                         │    │
│  │  └── strategy_performance (전략별 성과)                     │    │
│  │                                                              │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                      Data Retention                         │    │
│  │                                                              │    │
│  │  add_retention_policy('tick_data', INTERVAL '7 days')       │    │
│  │  add_retention_policy('ohlcv_1m', INTERVAL '30 days')       │    │
│  │  add_retention_policy('execution_logs', INTERVAL '90 days') │    │
│  │                                                              │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.4 TimescaleDB Schema Design

```sql
-- Tick Data Hypertable
CREATE TABLE tick_data (
    time        TIMESTAMPTZ NOT NULL,
    symbol      VARCHAR(20) NOT NULL,
    price       DECIMAL(18, 8) NOT NULL,
    volume      BIGINT NOT NULL,
    bid         DECIMAL(18, 8),
    ask         DECIMAL(18, 8),
    source      VARCHAR(20)
);

SELECT create_hypertable('tick_data', 'time');
CREATE INDEX ON tick_data (symbol, time DESC);

-- OHLCV 1-Minute Continuous Aggregate
CREATE MATERIALIZED VIEW ohlcv_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    symbol,
    first(price, time) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price, time) AS close,
    sum(volume) AS volume
FROM tick_data
GROUP BY bucket, symbol;

-- Retention Policy
SELECT add_retention_policy('tick_data', INTERVAL '7 days');
SELECT add_retention_policy('ohlcv_1m', INTERVAL '30 days');
```

### 1.5 Migration Path

| Phase | 작업 | 예상 영향 |
|-------|------|----------|
| Phase 1 | PostgreSQL 인스턴스 설정 + TimescaleDB 확장 | 인프라 |
| Phase 2 | 스키마 마이그레이션 (Google Sheets → PostgreSQL) | 데이터 |
| Phase 3 | `ops.backup` 모듈 DB 어댑터 추가 | 코드 변경 |
| Phase 4 | ETEDA Extract 단계 DB 커넥터 | 코드 변경 |
| Phase 5 | Google Sheets를 Read-Only 뷰로 전환 | 운영 |

---

## 2. Feedback Loop Architecture

### 2.1 Gap Analysis

현재 아키텍처 문서에서 **Feedback Loop**에 대한 명시적 정의가 부재합니다.

- `02_Engine_Core_Architecture.md`: Performance Engine이 "기록/분석"만 담당
- `03_Pipeline_ETEDA_Architecture.md`: Act → 다음 사이클 Extract 연결만 명시
- **Missing**: scalp_ticks 데이터가 Evaluate 엔진 학습에 활용되는 경로 없음

### 2.2 Proposed Feedback Loop Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FEEDBACK LOOP ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  EXECUTION PHASE                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Scalp Execution Micro-Pipeline                                  │   │
│  │  (PreCheck → OrderSplit → AsyncSend → PartialFill → ...)        │   │
│  │                           │                                      │   │
│  │                           ▼                                      │   │
│  │                    ExecutionResult                               │   │
│  │                    + scalp_ticks[]                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                │                                         │
│                                ▼                                         │
│  DATA COLLECTION PHASE                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │   │
│  │  │ Tick Store   │    │ Fill Store   │    │ Slippage     │      │   │
│  │  │ (TimescaleDB)│    │ (T_Ledger)   │    │ Metrics      │      │   │
│  │  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │   │
│  │         │                   │                   │               │   │
│  │         └───────────────────┴───────────────────┘               │   │
│  │                             │                                    │   │
│  └─────────────────────────────┼────────────────────────────────────┘   │
│                                │                                         │
│                                ▼                                         │
│  LEARNING PHASE                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   Feedback Aggregator                            │   │
│  │                                                                  │   │
│  │  Input:                                                          │   │
│  │  - scalp_ticks (price, volume, timestamp)                       │   │
│  │  - execution_fills (filled_qty, filled_price, slippage)         │   │
│  │  - market_context (volatility, spread, depth)                   │   │
│  │                                                                  │   │
│  │  Processing:                                                     │   │
│  │  - Feature Engineering                                           │   │
│  │  - Pattern Recognition                                           │   │
│  │  - Slippage Prediction Model Update                             │   │
│  │                                                                  │   │
│  │  Output:                                                         │   │
│  │  - Updated Strategy Parameters                                   │   │
│  │  - Execution Quality Score                                       │   │
│  │  - Market Impact Estimation                                      │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                │                                         │
│                                ▼                                         │
│  EVALUATE PHASE (Next Cycle)                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Strategy Engine                               │   │
│  │                                                                  │   │
│  │  Enhanced Input:                                                 │   │
│  │  + historical_slippage_by_symbol                                │   │
│  │  + execution_quality_score                                      │   │
│  │  + market_impact_estimation                                     │   │
│  │                                                                  │   │
│  │  Improved Decision:                                              │   │
│  │  - Slippage-adjusted entry price                                │   │
│  │  - Volume-aware position sizing                                 │   │
│  │  - Market impact-aware timing                                   │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Feedback Data Contract

```python
@dataclass
class FeedbackData:
    """Execution → Evaluate 피드백 데이터."""

    # Tick Data
    scalp_ticks: List[TickRecord]

    # Execution Metrics
    total_slippage_bps: float          # 슬리피지 (basis points)
    avg_fill_latency_ms: float         # 평균 체결 지연
    partial_fill_ratio: float          # 부분 체결 비율

    # Market Context at Execution
    volatility_at_execution: float     # 실행 시점 변동성
    spread_at_execution: float         # 실행 시점 스프레드
    depth_at_execution: int            # 실행 시점 호가 깊이

    # Learning Signals
    execution_quality_score: float     # 0.0 ~ 1.0
    market_impact_bps: float           # 시장 충격 (basis points)

    # Timestamps
    execution_start: datetime
    execution_end: datetime
    feedback_generated_at: datetime


@dataclass
class TickRecord:
    """개별 틱 레코드."""
    timestamp: datetime
    symbol: str
    price: Decimal
    volume: int
    side: str  # BID / ASK / TRADE
```

### 2.4 Implementation Roadmap

| Phase | 작업 | 의존성 |
|-------|------|--------|
| Phase 1 | `FeedbackData` Contract 정의 | 없음 |
| Phase 2 | Scalp Execution에서 tick 수집 | Phase 1 |
| Phase 3 | `FeedbackAggregator` 모듈 구현 | Phase 1, 2 |
| Phase 4 | Strategy Engine 입력 확장 | Phase 3 |
| Phase 5 | Continuous Improvement Loop 활성화 | Phase 4 |

---

## 3. Redis Caching Tier for Scalping

### 3.1 Latency Requirements

`15_Scalp_Execution_Micro_Architecture.md`에서 정의된 레이턴시 목표:

| Stage | 목표 p50 | 목표 p99 | 최대 |
|-------|----------|----------|------|
| PreCheck | 2ms | 5ms | 10ms |
| OrderSplit | 1ms | 3ms | 5ms |
| AsyncSend | 10ms | 20ms | 50ms |
| AdaptiveAdjust | 5ms | 10ms | 20ms |
| **Total (체결 제외)** | - | - | **100ms** |

**현재 문제**: 데이터 조회가 Google Sheets API를 통해 이루어지면 100-500ms 오버헤드 발생

### 3.2 Proposed Redis Caching Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    REDIS CACHING TIER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      SCALP HOT DATA LAYER                          │  │
│  │                         (Redis Cluster)                            │  │
│  │                                                                    │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │  │
│  │  │  Price Cache    │  │ Position Cache  │  │  Order Cache    │   │  │
│  │  │                 │  │                 │  │                 │   │  │
│  │  │ Key: price:{sym}│  │ Key: pos:{sym}  │  │ Key: ord:{id}   │   │  │
│  │  │ TTL: 100ms      │  │ TTL: 1s         │  │ TTL: 60s        │   │  │
│  │  │                 │  │                 │  │                 │   │  │
│  │  │ Fields:         │  │ Fields:         │  │ Fields:         │   │  │
│  │  │ - bid           │  │ - qty           │  │ - status        │   │  │
│  │  │ - ask           │  │ - avg_price     │  │ - filled_qty    │   │  │
│  │  │ - last          │  │ - unrealized_pnl│  │ - pending_qty   │   │  │
│  │  │ - volume        │  │ - exposure_pct  │  │ - last_update   │   │  │
│  │  │ - timestamp     │  │                 │  │                 │   │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘   │  │
│  │                                                                    │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │  │
│  │  │  Risk Cache     │  │ Strategy Cache  │  │  Orderbook      │   │  │
│  │  │                 │  │                 │  │  Snapshot       │   │  │
│  │  │ Key: risk:account│ │ Key: strat:{id} │  │                 │   │  │
│  │  │ TTL: 5s         │  │ TTL: 60s        │  │ Key: book:{sym} │   │  │
│  │  │                 │  │                 │  │ TTL: 50ms       │   │  │
│  │  │ Fields:         │  │ Fields:         │  │                 │   │  │
│  │  │ - exposure_used │  │ - params        │  │ Type: Sorted Set│   │  │
│  │  │ - daily_pnl     │  │ - active        │  │ - bid levels    │   │  │
│  │  │ - trade_count   │  │ - last_signal   │  │ - ask levels    │   │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘   │  │
│  │                                                                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
│                                   │ Cache Miss                           │
│                                   ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      WARM DATA LAYER                               │  │
│  │                    (PostgreSQL + TimescaleDB)                      │  │
│  │                                                                    │  │
│  │  - Historical tick data                                           │  │
│  │  - T_Ledger records                                               │  │
│  │  - Strategy parameters                                            │  │
│  │  - Risk configurations                                            │  │
│  │                                                                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Cache Strategy by Data Type

| Data Type | Cache Strategy | TTL | Invalidation |
|-----------|---------------|-----|--------------|
| 실시간 호가 | Write-Through | 50-100ms | Time-based |
| 포지션 | Write-Through | 1s | On execution |
| 리스크 한도 | Read-Through | 5s | On config change |
| 전략 파라미터 | Read-Through | 60s | On update |
| 주문 상태 | Write-Through | 60s | On fill/cancel |
| 호가창 스냅샷 | Write-Through | 50ms | Continuous update |

### 3.4 Redis Data Structures

```python
# Price Cache (Hash)
redis.hset("price:005930", mapping={
    "bid": "75000",
    "ask": "75100",
    "last": "75050",
    "volume": "1234567",
    "timestamp": "1706700000000"
})
redis.expire("price:005930", 0.1)  # 100ms TTL

# Orderbook Cache (Sorted Set)
redis.zadd("book:005930:bid", {
    "75000": 1000,  # price: volume
    "74900": 2500,
    "74800": 5000,
})
redis.zadd("book:005930:ask", {
    "75100": 800,
    "75200": 1500,
    "75300": 3000,
})

# Position Cache (Hash)
redis.hset("pos:005930", mapping={
    "qty": "100",
    "avg_price": "74500",
    "unrealized_pnl": "55000",
    "exposure_pct": "0.05"
})

# Risk Cache (Hash)
redis.hset("risk:account", mapping={
    "exposure_used": "0.45",
    "daily_pnl": "125000",
    "trade_count": "15",
    "remaining_limit": "0.55"
})
```

### 3.5 Latency Improvement Estimate

| Operation | Before (Sheets) | After (Redis) | Improvement |
|-----------|-----------------|---------------|-------------|
| Price Lookup | 150-300ms | 0.5-1ms | **99.7%** |
| Position Check | 200-400ms | 0.3-0.8ms | **99.8%** |
| Risk Validation | 250-500ms | 0.5-1.5ms | **99.7%** |
| Orderbook Query | N/A | 1-2ms | New capability |
| **Total PreCheck** | 600-1200ms | **2-5ms** | **99.5%** |

### 3.6 Implementation Considerations

```python
# Cache-Aside Pattern Example
class ScalpDataCache:
    def __init__(self, redis_client, db_client):
        self.redis = redis_client
        self.db = db_client

    async def get_position(self, symbol: str) -> Position:
        # 1. Try cache first
        cached = await self.redis.hgetall(f"pos:{symbol}")
        if cached:
            return Position.from_cache(cached)

        # 2. Cache miss - fetch from DB
        position = await self.db.get_position(symbol)

        # 3. Populate cache
        await self.redis.hset(
            f"pos:{symbol}",
            mapping=position.to_cache_dict()
        )
        await self.redis.expire(f"pos:{symbol}", 1)  # 1s TTL

        return position

    async def update_position_on_fill(self, fill: Fill):
        # Write-Through: Update both cache and DB
        position = await self.db.update_position(fill)
        await self.redis.hset(
            f"pos:{fill.symbol}",
            mapping=position.to_cache_dict()
        )
```

---

## 4. Document Inventory & Recommendations

### 4.1 Document List

| # | 파일명 | 상태 | 권장 조치 |
|---|--------|------|----------|
| 1 | 00_Architecture.md | Active | 유지 |
| 2 | 01_Schema_Auto_Architecture.md | Active | DB 마이그레이션 반영 필요 |
| 3 | 02_Engine_Core_Architecture.md | Active | Feedback Loop 섹션 추가 필요 |
| 4 | 03_Pipeline_ETEDA_Architecture.md | Active | 유지 |
| 5 | 04_Data_Contract_Spec.md | Active | TimescaleDB 스키마 추가 필요 |
| 6 | 05_Python_Calculation_Spec.md | Active | 유지 |
| 7 | 06_UI_Architecture.md | Active | 유지 |
| 8 | 07_FailSafe_Architecture.md | Active | 유지 |
| 9 | 08_Broker_Integration_Architecture.md | Active | 유지 |
| 10 | 09_Safety_Architecture.md | Active | 유지 |
| 11 | 10_Testability_Architecture.md | Active | 유지 |
| 12 | 11_Glossary.md | Active | 유지 |
| 13 | sub/12_TelegramBot_Architecture.md | Active | 유지 |
| 14 | sub/13_3Track_Strategy.md | Active | 유지 |
| 15 | sub/14_Capital_Flow_Architecture.md | Active | 유지 |
| 16 | sub/15_Scalp_Execution_Micro_Architecture.md | Active | Redis 캐싱 섹션 추가 필요 |
| 17 | sub/16_Micro_Risk_Loop_Architecture.md | Active | 유지 |
| 18 | sub/17_Event_Priority_Architecture.md | Active | 유지 |

### 4.2 Potentially Redundant/Obsolete Files

현재 `docs/arch/` 폴더에서 **불필요하거나 중복된 파일은 발견되지 않았습니다.**

모든 18개 문서가 고유한 역할을 수행하며 상호 참조 구조가 잘 정의되어 있습니다.

### 4.3 Missing Documentation

다음 문서 추가를 권장합니다:

| 권장 문서 | 목적 | 우선순위 |
|----------|------|---------|
| `18_Data_Layer_Architecture.md` | PostgreSQL/TimescaleDB 아키텍처 | P0 |
| `19_Caching_Architecture.md` | Redis 캐싱 계층 상세 | P1 |
| `20_Feedback_Loop_Architecture.md` | 학습 피드백 루프 상세 | P1 |
| `21_Monitoring_Architecture.md` | 메트릭/알림 시스템 | P2 |

---

## 5. Implementation Priority Matrix

### 5.1 Priority Ranking

```
┌─────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION PRIORITY                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  HIGH IMPACT                                                        │
│      │                                                              │
│      │  ┌────────────────────┐                                     │
│      │  │ P0: TimescaleDB    │ ← High Impact, Medium Effort        │
│      │  │ Data Layer         │                                     │
│      │  └────────────────────┘                                     │
│      │                                                              │
│      │  ┌────────────────────┐  ┌────────────────────┐            │
│      │  │ P1: Redis Caching  │  │ P1: Feedback Loop  │            │
│      │  │ Tier               │  │ Architecture       │            │
│      │  └────────────────────┘  └────────────────────┘            │
│      │                                                              │
│      │                          ┌────────────────────┐            │
│      │                          │ P2: Latency        │            │
│      │                          │ Monitoring         │            │
│      │                          └────────────────────┘            │
│      │                                                              │
│  LOW IMPACT ──────────────────────────────────────────────────────│
│             LOW EFFORT                              HIGH EFFORT    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Action Items Summary

| ID | Action | Owner | Dependency | Status |
|----|--------|-------|------------|--------|
| A1 | PostgreSQL + TimescaleDB 인프라 구축 | DevOps | - | TODO |
| A2 | 데이터 마이그레이션 스크립트 작성 | Backend | A1 | TODO |
| A3 | `ops.backup` DB 어댑터 구현 | Backend | A1 | TODO |
| A4 | Redis 클러스터 구축 | DevOps | - | TODO |
| A5 | `ScalpDataCache` 모듈 구현 | Backend | A4 | TODO |
| A6 | `FeedbackAggregator` 모듈 구현 | ML/Backend | A2 | TODO |
| A7 | Strategy Engine 입력 확장 | Backend | A6 | TODO |
| A8 | 아키텍처 문서 업데이트 | Tech Writer | A1-A7 | TODO |

---

## 6. Conclusion

QTS 아키텍처는 전반적으로 잘 설계되어 있으나, 다음 세 가지 영역에서 확장성 개선이 필요합니다:

1. **Data Layer**: Google Sheets → PostgreSQL + TimescaleDB 마이그레이션을 통해 시계열 데이터 처리 능력 확보

2. **Feedback Loop**: scalp_ticks 데이터를 Evaluate 엔진 학습에 활용하는 명시적 파이프라인 구축

3. **Caching Tier**: Redis 인메모리 캐시 도입으로 Scalp Execution 레이턴시 목표(100ms) 달성

이러한 개선을 통해 QTS는 실시간 고빈도 매매 시스템으로의 확장이 가능해집니다.

---

**QTS Architecture Extensibility Review v1.0.0 - Complete**
