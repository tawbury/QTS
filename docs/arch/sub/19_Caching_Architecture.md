# ============================================================
# QTS Caching Architecture
# ============================================================

Version: v1.0.0
Status: Architecture Specification (Final)
Author: AI Architect
Last Updated: 2026-01-31

문서 목적:
본 문서는 QTS의 **Redis 기반 Caching 아키텍처**를 정의한다.
Scalp Execution의 레이턴시 목표 (<100ms) 달성을 위한
캐시 계층 설계, 전략, 무효화 규칙, Fallback 처리를 상세히 기술한다.

---

# **1. Overview**

## **1.1 목적**

QTS Caching Layer는 다음 목표를 달성한다:

1. **Ultra-Low Latency**: PreCheck 단계 < 5ms (p99)
2. **High Availability**: Cache 장애 시에도 시스템 계속 동작
3. **Data Freshness**: TTL 기반 자동 무효화
4. **Minimal Complexity**: 단순하고 예측 가능한 캐시 전략

---

## **1.2 범위**

포함:

- Redis 캐시 계층 설계
- 캐시 데이터 타입 및 TTL 전략
- Write-Through / Read-Through 패턴
- Cache Invalidation 규칙
- Fallback 및 Failure Handling
- Connection Pooling 및 Performance Tuning

제외:

- Redis 클러스터 인프라 구축 (→ DevOps)
- 브로커 API 캐싱 (→ Broker Integration)
- UI 렌더링 캐싱 (→ UI Architecture)

---

## **1.3 관련 문서**

- **Scalp Execution**: [15_Scalp_Execution_Micro_Architecture.md](./15_Scalp_Execution_Micro_Architecture.md)
- **Data Layer**: [18_Data_Layer_Architecture.md](./18_Data_Layer_Architecture.md)
- **Engine Core**: [../02_Engine_Core_Architecture.md](../02_Engine_Core_Architecture.md)
- **ETEDA Pipeline**: [../03_Pipeline_ETEDA_Architecture.md](../03_Pipeline_ETEDA_Architecture.md)

---

## **1.4 설계 원칙**

1. **Cache-Aside Pattern 기본**: 애플리케이션이 캐시 로직 제어
2. **Explicit TTL**: 모든 캐시 키는 명시적 TTL 설정
3. **Graceful Degradation**: 캐시 장애 시 DB로 Fallback
4. **No Business Logic in Cache**: 캐시는 단순 데이터 저장소
5. **Monitoring First**: 캐시 히트율, 레이턴시 필수 모니터링

---

# **2. Cache Architecture**

## **2.1 Redis Topology**

```
┌──────────────────────────────────────────────────────────────┐
│                    REDIS CACHE LAYER                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Redis Cluster (3 Master + 3 Replica)      │  │
│  │                                                         │  │
│  │  Master 1         Master 2         Master 3            │  │
│  │  (Slots 0-5461)   (Slots 5462-10922) (Slots 10923-16383)│
│  │     │                 │                 │               │  │
│  │     ├─ Replica 1      ├─ Replica 2      ├─ Replica 3   │  │
│  │                                                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                              │                                │
│                              ▼                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │            Application Connection Pool                  │  │
│  │            (redis-py with ConnectionPool)               │  │
│  │                                                         │  │
│  │  Min Connections: 10                                   │  │
│  │  Max Connections: 50                                   │  │
│  │  Socket Timeout: 100ms                                 │  │
│  │  Socket Connect Timeout: 500ms                         │  │
│  │                                                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                              │                                │
│                              ▼                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                 QTS Application                         │  │
│  │                 (ScalpDataCache)                        │  │
│  │                                                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## **2.2 Data Partitioning Strategy**

| Cache Type | Redis Data Structure | Sharding Key | Reason |
|-----------|---------------------|--------------|--------|
| Price | Hash | `symbol` | Symbol-based access |
| Position | Hash | `symbol` | Symbol-based access |
| Orderbook | Sorted Set | `symbol` | Symbol-based access |
| Risk Limits | Hash | `account` | Single account |
| Order Status | Hash | `order_id` | Order-based access |
| Strategy Params | Hash | `strategy_id` | Strategy-based access |

**Sharding**: Redis Cluster는 키 기반 자동 샤딩 (CRC16 해싱).

---

# **3. Cache Data Models**

## **3.1 Price Cache**

**목적**: 실시간 호가 저장 (100ms TTL).

```python
# Redis Key: price:{symbol}
# Type: Hash

redis.hset("price:005930", mapping={
    "bid": "75000",
    "ask": "75100",
    "last": "75050",
    "volume": "1234567",
    "timestamp": "1706700000123"  # Unix ms
})
redis.expire("price:005930", 0.1)  # 100ms TTL
```

**필드 정의:**

| Field | Type | Description |
|-------|------|-------------|
| bid | str (decimal) | 매수 최우선 호가 |
| ask | str (decimal) | 매도 최우선 호가 |
| last | str (decimal) | 최근 체결가 |
| volume | str (int) | 누적 거래량 |
| timestamp | str (int) | Unix timestamp (ms) |

---

## **3.2 Position Cache**

**목적**: 현재 포지션 정보 (1s TTL).

```python
# Redis Key: pos:{symbol}
# Type: Hash

redis.hset("pos:005930", mapping={
    "qty": "100",
    "avg_price": "74500",
    "unrealized_pnl": "55000",
    "exposure_pct": "0.05",
    "updated_at": "1706700000000"
})
redis.expire("pos:005930", 1)  # 1s TTL
```

**필드 정의:**

| Field | Type | Description |
|-------|------|-------------|
| qty | str (decimal) | 보유 수량 |
| avg_price | str (decimal) | 평균 단가 |
| unrealized_pnl | str (decimal) | 미실현 손익 |
| exposure_pct | str (decimal) | 계좌 대비 노출 비중 |
| updated_at | str (int) | 마지막 업데이트 시각 |

---

## **3.3 Orderbook Cache**

**목적**: 호가창 스냅샷 (50ms TTL).

```python
# Redis Keys: book:{symbol}:bid, book:{symbol}:ask
# Type: Sorted Set (Score = Volume, Member = Price)

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

redis.expire("book:005930:bid", 0.05)  # 50ms TTL
redis.expire("book:005930:ask", 0.05)
```

**조회 예시:**

```python
# Top 5 Bid Levels
top_bids = redis.zrevrange("book:005930:bid", 0, 4, withscores=True)
# [('75000', 1000.0), ('74900', 2500.0), ...]
```

---

## **3.4 Risk Cache**

**목적**: 리스크 한도 및 계좌 상태 (5s TTL).

```python
# Redis Key: risk:account
# Type: Hash

redis.hset("risk:account", mapping={
    "exposure_used": "0.45",
    "daily_pnl": "125000",
    "trade_count": "15",
    "remaining_limit": "0.55",
    "max_exposure_pct": "0.8",
    "daily_loss_limit": "-500000",
    "updated_at": "1706700000000"
})
redis.expire("risk:account", 5)  # 5s TTL
```

---

## **3.5 Order Status Cache**

**목적**: 주문 상태 추적 (60s TTL).

```python
# Redis Key: ord:{order_id}
# Type: Hash

redis.hset("ord:ORD123456", mapping={
    "status": "PARTIALLY_FILLED",
    "filled_qty": "50",
    "pending_qty": "50",
    "avg_fill_price": "75050",
    "last_update": "1706700000500"
})
redis.expire("ord:ORD123456", 60)  # 60s TTL
```

---

## **3.6 Strategy Parameters Cache**

**목적**: 전략 파라미터 (60s TTL).

```python
# Redis Key: strat:{strategy_id}
# Type: Hash

redis.hset("strat:SCALP_RSI", mapping={
    "active": "true",
    "rsi_oversold": "30",
    "rsi_overbought": "70",
    "position_size": "0.02",
    "updated_at": "1706700000000"
})
redis.expire("strat:SCALP_RSI", 60)  # 60s TTL
```

---

# **4. Cache Patterns**

## **4.1 Cache-Aside (Lazy Loading)**

기본 패턴: 캐시 미스 시 DB 조회 후 캐시 채움.

```python
class ScalpDataCache:
    def __init__(self, redis_client, db_adapter):
        self.redis = redis_client
        self.db = db_adapter

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
        await self.redis.expire(f"pos:{symbol}", 1)

        return position
```

**장점**: 필요한 데이터만 캐싱
**단점**: First request는 느림 (DB 조회)

---

## **4.2 Write-Through**

데이터 쓰기 시 DB와 캐시 동시 업데이트.

```python
async def update_position_on_fill(self, fill: Fill):
    # 1. Update DB (primary)
    position = await self.db.update_position(fill)

    # 2. Update Cache (write-through)
    await self.redis.hset(
        f"pos:{fill.symbol}",
        mapping=position.to_cache_dict()
    )
    await self.redis.expire(f"pos:{fill.symbol}", 1)

    return position
```

**장점**: 캐시 일관성 보장
**단점**: 쓰기 레이턴시 증가

---

## **4.3 Real-Time Push (Market Data)**

Market Data Feed → Redis 직접 업데이트.

```python
async def on_tick(self, tick: TickData):
    """WebSocket 또는 Market Data Feed에서 호출"""
    await self.redis.hset(f"price:{tick.symbol}", mapping={
        "bid": str(tick.bid),
        "ask": str(tick.ask),
        "last": str(tick.last),
        "volume": str(tick.volume),
        "timestamp": str(int(tick.timestamp.timestamp() * 1000))
    })
    await self.redis.expire(f"price:{tick.symbol}", 0.1)
```

**장점**: 초저지연 (sub-millisecond)
**단점**: Feed 장애 시 캐시 비어있음

---

## **4.4 Read-Through**

캐시가 자동으로 DB 조회 (Adapter 패턴).

```python
async def get_risk_limits(self) -> RiskLimits:
    # 1. Try cache
    cached = await self.redis.hgetall("risk:account")
    if cached:
        return RiskLimits.from_cache(cached)

    # 2. Cache miss - auto-populate
    limits = await self.db.get_risk_limits()
    await self.redis.hset("risk:account", mapping=limits.to_cache_dict())
    await self.redis.expire("risk:account", 5)

    return limits
```

---

# **5. Cache Invalidation**

## **5.1 TTL-Based Invalidation (Primary)**

모든 캐시는 TTL로 자동 만료.

| Cache Type | TTL | Reason |
|-----------|-----|--------|
| Price | 100ms | 실시간 호가는 매우 빠르게 변함 |
| Position | 1s | 포지션은 체결 시에만 변함 |
| Orderbook | 50ms | 호가창은 극도로 빠르게 변함 |
| Risk Limits | 5s | 리스크 설정은 자주 변하지 않음 |
| Order Status | 60s | 주문 상태는 체결 완료 후 안정 |
| Strategy Params | 60s | 전략 파라미터는 거의 변하지 않음 |

**구현:**

```python
# TTL 설정은 MANDATORY
await self.redis.set(key, value)
await self.redis.expire(key, ttl_seconds)  # MUST

# 또는 SETEX 사용
await self.redis.setex(key, ttl_seconds, value)
```

---

## **5.2 Event-Based Invalidation (Secondary)**

특정 이벤트 발생 시 즉시 무효화.

```python
async def on_execution_result(self, result: ExecutionResult):
    """주문 체결 시 포지션 캐시 무효화"""
    symbol = result.symbol

    # Invalidate position cache
    await self.redis.delete(f"pos:{symbol}")

    # Immediately refresh from DB
    position = await self.db.get_position(symbol)
    await self.redis.hset(f"pos:{symbol}", mapping=position.to_cache_dict())
    await self.redis.expire(f"pos:{symbol}", 1)
```

**이벤트 트리거:**
- 주문 체결 → Position 캐시 무효화
- 전략 파라미터 변경 → Strategy 캐시 무효화
- 리스크 설정 변경 → Risk 캐시 무효화

---

## **5.3 Manual Invalidation (Emergency)**

운영자가 수동으로 캐시 플러시.

```python
async def flush_all_cache():
    """전체 캐시 삭제 (Emergency Only)"""
    await self.redis.flushdb()
    log_warning("All cache flushed manually")
```

**사용 시나리오:**
- 데이터 불일치 감지
- 캐시 오염 의심
- 시스템 재시작 후

---

# **6. Failure Handling**

## **6.1 Graceful Degradation**

Cache 장애 시 DB로 Fallback.

```python
class CacheAwareDataAccess:
    def __init__(self, redis_client, db_adapter):
        self.redis = redis_client
        self.db = db_adapter

    async def get_position(self, symbol: str) -> Position:
        try:
            # Try Redis first
            cached = await self.redis.hgetall(f"pos:{symbol}")
            if cached:
                return Position.from_cache(cached)
        except RedisConnectionError as e:
            log_warning(f"Redis unavailable: {e}, falling back to DB")
        except RedisTimeoutError as e:
            log_warning(f"Redis timeout: {e}, falling back to DB")

        # Fallback to DB
        return await self.db.get_position(symbol)
```

---

## **6.2 Circuit Breaker Pattern**

반복 실패 시 일정 시간 Redis 우회.

```python
from circuitbreaker import circuit

class CircuitBreakerCache:
    @circuit(failure_threshold=5, recovery_timeout=60)
    async def get_from_cache(self, key):
        """Circuit Breaker 적용"""
        return await self.redis.get(key)

    async def get_position(self, symbol: str) -> Position:
        try:
            cached = await self.get_from_cache(f"pos:{symbol}")
            if cached:
                return Position.from_cache(cached)
        except CircuitBreakerOpen:
            log_warning("Circuit breaker open, using DB only")

        # Fallback to DB
        return await self.db.get_position(symbol)
```

**Circuit States:**
- **Closed**: 정상 동작 (Redis 사용)
- **Open**: 장애 감지 (Redis 우회, DB 직접 조회)
- **Half-Open**: 회복 시도 (제한적 Redis 사용)

---

## **6.3 Stale Data Detection**

캐시 데이터가 너무 오래되면 거부.

```python
def is_stale(cached_data: dict, threshold_ms: int = 100) -> bool:
    """캐시 데이터 신선도 검사"""
    timestamp_ms = int(cached_data.get("timestamp", 0))
    now_ms = int(time.time() * 1000)
    age_ms = now_ms - timestamp_ms
    return age_ms > threshold_ms

async def get_price(self, symbol: str) -> Price:
    cached = await self.redis.hgetall(f"price:{symbol}")
    if cached:
        if is_stale(cached, threshold_ms=100):
            log_warning(f"Price data for {symbol} is stale ({cached['timestamp']})")
            raise CacheStaleDataError(f"Price too old: {symbol}")
        return Price.from_cache(cached)

    # Fetch fresh data
    raise PriceDataUnavailableError(f"No price data: {symbol}")
```

---

## **6.4 Retry Strategy**

일시적 네트워크 오류 시 재시도.

```python
from tenacity import retry, stop_after_attempt, wait_fixed

class RetryableCache:
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0.01))  # 10ms 간격 3회 재시도
    async def get_with_retry(self, key: str):
        return await self.redis.get(key)
```

---

# **7. Performance Tuning**

## **7.1 Connection Pooling**

```python
import redis.asyncio as redis

# Connection Pool 생성
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    max_connections=50,
    decode_responses=True,
    socket_connect_timeout=0.5,  # 500ms
    socket_timeout=0.1,  # 100ms
    socket_keepalive=True
)

redis_client = redis.Redis(connection_pool=pool)
```

**설정 가이드:**
- `max_connections`: 동시 요청 * 2 (권장)
- `socket_timeout`: 100ms (Scalp 요구사항)
- `socket_connect_timeout`: 500ms
- `decode_responses=True`: 자동 UTF-8 디코딩

---

## **7.2 Pipeline (Batch Operations)**

다수의 Redis 명령을 한 번에 전송.

```python
async def fetch_multiple_prices(self, symbols: List[str]) -> Dict[str, Price]:
    pipe = self.redis.pipeline()
    for symbol in symbols:
        pipe.hgetall(f"price:{symbol}")

    results = await pipe.execute()

    return {
        symbol: Price.from_cache(result)
        for symbol, result in zip(symbols, results)
        if result
    }
```

**성능 향상:** RTT (Round-Trip Time) 1회로 감소.

---

## **7.3 Compression (선택적)**

큰 데이터 저장 시 압축 고려.

```python
import zlib
import json

def compress_data(data: dict) -> bytes:
    json_str = json.dumps(data)
    return zlib.compress(json_str.encode('utf-8'))

def decompress_data(compressed: bytes) -> dict:
    json_str = zlib.decompress(compressed).decode('utf-8')
    return json.loads(json_str)

# 사용 예
compressed = compress_data(position.to_dict())
await self.redis.set(f"pos:{symbol}", compressed)
```

**Trade-off:** CPU 비용 vs 네트워크 비용

---

## **7.4 Lua Scripts (Atomic Operations)**

복잡한 연산을 원자적으로 수행.

```lua
-- increment_and_check.lua
local count = redis.call('INCR', KEYS[1])
if count > tonumber(ARGV[1]) then
    return 0
else
    return count
end
```

```python
script = """
local count = redis.call('INCR', KEYS[1])
if count > tonumber(ARGV[1]) then
    return 0
else
    return count
end
"""

# 일일 거래 횟수 체크 (원자적)
trade_count = await self.redis.eval(
    script,
    keys=['daily_trade_count'],
    args=[100]  # Max 100 trades/day
)
if trade_count == 0:
    raise TradeLimitExceededError("Daily trade limit reached")
```

---

# **8. Monitoring & Metrics**

## **8.1 Cache Hit Rate**

```python
class MetricsCache:
    def __init__(self, redis_client, db_adapter):
        self.redis = redis_client
        self.db = db_adapter
        self.hit_count = 0
        self.miss_count = 0

    async def get_position(self, symbol: str) -> Position:
        cached = await self.redis.hgetall(f"pos:{symbol}")
        if cached:
            self.hit_count += 1
            return Position.from_cache(cached)

        self.miss_count += 1
        position = await self.db.get_position(symbol)
        await self.redis.hset(f"pos:{symbol}", mapping=position.to_cache_dict())
        await self.redis.expire(f"pos:{symbol}", 1)
        return position

    def get_hit_rate(self) -> float:
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0
```

**목표 Hit Rate:**
- Position: > 95%
- Price: > 99%
- Risk: > 90%

---

## **8.2 Latency Tracking**

```python
import time

async def get_position_with_metrics(self, symbol: str) -> Position:
    start = time.perf_counter()

    position = await self.get_position(symbol)

    latency_ms = (time.perf_counter() - start) * 1000
    record_metric("cache_latency_ms", latency_ms, tags={"type": "position"})

    return position
```

---

## **8.3 Alert Rules**

| Metric | Threshold | Action |
|--------|----------|--------|
| Cache Hit Rate | < 85% | Investigate |
| Cache Latency p99 | > 5ms | Optimize |
| Connection Pool Usage | > 90% | Scale up |
| Redis Memory Usage | > 80% | Eviction policy check |
| Circuit Breaker Open | Any | Critical Alert |

---

# **9. Appendix**

## **9.1 Complete Cache Configuration**

```python
CACHE_CONFIG = {
    "REDIS_HOST": "localhost",
    "REDIS_PORT": 6379,
    "REDIS_DB": 0,
    "REDIS_PASSWORD": None,
    "POOL_MAX_CONNECTIONS": 50,
    "SOCKET_TIMEOUT_MS": 100,
    "SOCKET_CONNECT_TIMEOUT_MS": 500,

    "TTL": {
        "price": 0.1,  # 100ms
        "position": 1,  # 1s
        "orderbook": 0.05,  # 50ms
        "risk": 5,  # 5s
        "order": 60,  # 60s
        "strategy": 60,  # 60s
    },

    "CIRCUIT_BREAKER": {
        "failure_threshold": 5,
        "recovery_timeout": 60,  # seconds
    },

    "RETRY": {
        "max_attempts": 3,
        "wait_ms": 10,
    }
}
```

---

## **9.2 Redis CLI Debugging Commands**

```bash
# 모든 price 키 조회
redis-cli KEYS "price:*"

# 특정 position 조회
redis-cli HGETALL "pos:005930"

# TTL 확인
redis-cli TTL "price:005930"

# 캐시 히트 통계 (INFO)
redis-cli INFO stats

# 메모리 사용량
redis-cli INFO memory

# 슬로우 로그 확인
redis-cli SLOWLOG GET 10
```

---

## **9.3 Sample Integration Test**

```python
import pytest

@pytest.mark.asyncio
async def test_position_cache_hit():
    cache = ScalpDataCache(redis_client, db_adapter)

    # First call (cache miss)
    pos1 = await cache.get_position("005930")
    assert pos1.symbol == "005930"

    # Second call (cache hit)
    pos2 = await cache.get_position("005930")
    assert pos2.symbol == "005930"
    assert pos2.qty == pos1.qty

    # Verify hit rate
    assert cache.get_hit_rate() == 0.5  # 1 hit / 2 total

@pytest.mark.asyncio
async def test_cache_stale_data():
    cache = ScalpDataCache(redis_client, db_adapter)

    # Set stale data
    await redis_client.hset("price:005930", mapping={
        "bid": "75000",
        "timestamp": str(int(time.time() * 1000) - 500)  # 500ms ago
    })

    # Should raise stale error
    with pytest.raises(CacheStaleDataError):
        await cache.get_price("005930")
```

---

**QTS Caching Architecture v1.0.0 — 완료됨**
