# ============================================================
# QTS Data Layer Architecture
# ============================================================

Version: v1.0.0
Status: Architecture Specification (Final)
Author: AI Architect
Last Updated: 2026-01-31

문서 목적:
본 문서는 QTS의 **Data Layer 아키텍처**를 정의한다.
Google Sheets 기반에서 PostgreSQL + TimescaleDB로의 진화 경로를 제시하고,
시계열 데이터 저장, 쿼리, 보존 정책, 마이그레이션 전략을 상세히 기술한다.

---

# **1. Overview**

## **1.1 목적**

QTS Data Layer는 다음 목표를 달성한다:

1. **확장 가능한 데이터 저장**: 대용량 틱 데이터 및 시계열 데이터 지원
2. **고성능 쿼리**: 실시간 집계 및 분석 쿼리 지원
3. **데이터 무결성**: 트랜잭션 보장 및 동시성 제어
4. **자동화된 보존 정책**: 데이터 라이프사이클 자동 관리
5. **점진적 마이그레이션**: 기존 시스템 중단 없이 진화

---

## **1.2 범위**

포함:

- PostgreSQL + TimescaleDB 아키텍처
- 테이블 설계 및 인덱스 전략
- Hypertable 및 Continuous Aggregates
- 데이터 보존 정책
- 마이그레이션 전략
- Adapter Layer 설계

제외:

- 특정 브로커 데이터 형식 (→ Broker Integration 참조)
- 계산 로직 (→ Python Calculation Spec 참조)
- UI 렌더링 (→ UI Architecture 참조)

---

## **1.3 관련 문서**

- **Schema Automation**: [../01_Schema_Auto_Architecture.md](../01_Schema_Auto_Architecture.md)
- **Data Contract**: [../04_Data_Contract_Spec.md](../04_Data_Contract_Spec.md)
- **Engine Core**: [../02_Engine_Core_Architecture.md](../02_Engine_Core_Architecture.md)
- **ETEDA Pipeline**: [../03_Pipeline_ETEDA_Architecture.md](../03_Pipeline_ETEDA_Architecture.md)
- **Caching Architecture**: [19_Caching_Architecture.md](./19_Caching_Architecture.md)

---

## **1.4 설계 원칙**

1. **Schema Engine과 분리**: Data Layer는 Schema Engine의 추상화 하에서 동작
2. **시간 최적화**: 모든 시계열 데이터는 TimescaleDB Hypertable 사용
3. **Continuous Aggregates**: 실시간 집계 뷰 활용
4. **자동 파티셔닝**: 수동 파티션 관리 금지
5. **보존 정책 자동화**: 데이터 TTL 자동 적용

---

# **2. Architecture Overview**

## **2.1 Data Layer 구조**

```
┌──────────────────────────────────────────────────────────────────┐
│                      QTS DATA LAYER                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                Schema Engine (Abstract)                    │  │
│  │                                                             │  │
│  │  - Schema JSON 생성                                        │  │
│  │  - Field Mapping                                           │  │
│  │  - Contract Builder                                        │  │
│  │                                                             │  │
│  └─────────────────────┬─────────────────────────────────────┘  │
│                        │                                          │
│                        ▼                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               Data Adapter Interface                       │  │
│  │                                                             │  │
│  │  - fetch_raw_data(sheet_name) → RawDataContract           │  │
│  │  - store_execution_result(result) → bool                  │  │
│  │  - fetch_time_series(symbol, start, end) → List[Tick]     │  │
│  │                                                             │  │
│  └───────────────────┬──────────────────┬────────────────────┘  │
│                      │                  │                        │
│            ┌─────────▼──────┐  ┌───────▼──────────────┐         │
│            │ Google Sheets  │  │  PostgreSQL +        │         │
│            │ Adapter        │  │  TimescaleDB Adapter │         │
│            │                │  │                      │         │
│            │ - Config       │  │ - Time-Series Data   │         │
│            │ - Strategy     │  │ - Transactional Data │         │
│            │ - Read-Only    │  │ - Hot Data           │         │
│            └────────────────┘  └──────────────────────┘         │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## **2.2 PostgreSQL + TimescaleDB 선택 이유**

| 요구사항 | PostgreSQL | TimescaleDB | 대안 (InfluxDB, etc) |
|---------|-----------|-------------|---------------------|
| 시계열 최적화 | △ | ✓ | ✓ |
| SQL 호환성 | ✓ | ✓ | △ |
| 트랜잭션 지원 | ✓ | ✓ | △ |
| Continuous Aggregates | - | ✓ | △ |
| 자동 파티셔닝 | △ | ✓ | ✓ |
| Python 생태계 | ✓ | ✓ | △ |
| **선택** | - | **✓** | - |

**결론**: TimescaleDB는 PostgreSQL 기반으로 SQL 호환성과 시계열 최적화를 모두 제공.

---

# **3. Database Schema Design**

## **3.1 Regular Tables (트랜잭션 데이터)**

### **3.1.1 positions**

현재 포지션 정보 (트랜잭션 테이블).

```sql
CREATE TABLE positions (
    symbol VARCHAR(20) PRIMARY KEY,
    qty DECIMAL(18, 8) NOT NULL CHECK (qty >= 0),
    avg_price DECIMAL(18, 8) NOT NULL,
    market VARCHAR(10),
    exposure_value DECIMAL(18, 2),
    exposure_pct DECIMAL(5, 4),
    unrealized_pnl DECIMAL(18, 2),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_positions_market ON positions(market);
CREATE INDEX idx_positions_updated ON positions(updated_at DESC);
```

---

### **3.1.2 t_ledger**

거래 원장 (모든 체결 기록).

```sql
CREATE TABLE t_ledger (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(4) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    qty DECIMAL(18, 8) NOT NULL,
    price DECIMAL(18, 8) NOT NULL,
    amount DECIMAL(18, 2) NOT NULL,
    fee DECIMAL(18, 2) DEFAULT 0,
    strategy_tag VARCHAR(50),
    order_id VARCHAR(100),
    broker VARCHAR(20)
);

CREATE INDEX idx_ledger_timestamp ON t_ledger(timestamp DESC);
CREATE INDEX idx_ledger_symbol ON t_ledger(symbol, timestamp DESC);
CREATE INDEX idx_ledger_strategy ON t_ledger(strategy_tag, timestamp DESC);
```

---

### **3.1.3 strategies**

전략 파라미터.

```sql
CREATE TABLE strategies (
    strategy_id VARCHAR(50) PRIMARY KEY,
    param_name VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string',
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_strategies_updated ON strategies(updated_at DESC);
```

---

### **3.1.4 risk_configs**

리스크 설정.

```sql
CREATE TABLE risk_configs (
    config_key VARCHAR(100) PRIMARY KEY,
    value DECIMAL(18, 8) NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## **3.2 TimescaleDB Hypertables (시계열 데이터)**

### **3.2.1 tick_data**

원시 틱 데이터 (초단위 실시간 데이터).

```sql
CREATE TABLE tick_data (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(18, 8) NOT NULL,
    volume BIGINT NOT NULL,
    bid DECIMAL(18, 8),
    ask DECIMAL(18, 8),
    source VARCHAR(20)
);

-- Convert to Hypertable
SELECT create_hypertable('tick_data', 'time', chunk_time_interval => INTERVAL '1 day');

-- Indexes
CREATE INDEX idx_tick_symbol_time ON tick_data (symbol, time DESC);
CREATE INDEX idx_tick_source ON tick_data (source, time DESC);

-- Compression (7일 이후 데이터 압축)
ALTER TABLE tick_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol'
);

SELECT add_compression_policy('tick_data', INTERVAL '7 days');
```

---

### **3.2.2 ohlcv_1d**

일봉 데이터 (Hypertable).

```sql
CREATE TABLE ohlcv_1d (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume BIGINT NOT NULL,
    UNIQUE (time, symbol)
);

SELECT create_hypertable('ohlcv_1d', 'time', chunk_time_interval => INTERVAL '30 days');

CREATE INDEX idx_ohlcv_1d_symbol_time ON ohlcv_1d (symbol, time DESC);
```

---

### **3.2.3 execution_logs**

실행 로그 (레이턴시 추적).

```sql
CREATE TABLE execution_logs (
    time TIMESTAMPTZ NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    latency_ms DECIMAL(10, 3),
    success BOOLEAN NOT NULL,
    error_code VARCHAR(50)
);

SELECT create_hypertable('execution_logs', 'time', chunk_time_interval => INTERVAL '1 day');

CREATE INDEX idx_exec_logs_order ON execution_logs (order_id, time DESC);
CREATE INDEX idx_exec_logs_stage ON execution_logs (stage, time DESC);
```

---

## **3.3 Continuous Aggregates (실시간 집계 뷰)**

### **3.3.1 ohlcv_1m (1분봉)**

tick_data에서 1분봉 자동 생성.

```sql
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

-- Refresh Policy (실시간 갱신)
SELECT add_continuous_aggregate_policy('ohlcv_1m',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');

-- Index
CREATE INDEX idx_ohlcv_1m_symbol_bucket ON ohlcv_1m (symbol, bucket DESC);
```

---

### **3.3.2 daily_pnl (일별 손익)**

t_ledger 기반 일별 손익 집계.

```sql
CREATE MATERIALIZED VIEW daily_pnl
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    symbol,
    sum(CASE WHEN side = 'BUY' THEN -amount WHEN side = 'SELL' THEN amount END) AS realized_pnl,
    count(*) AS trade_count
FROM t_ledger
GROUP BY day, symbol;

SELECT add_continuous_aggregate_policy('daily_pnl',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');
```

---

### **3.3.3 hourly_execution_metrics (시간별 실행 품질)**

```sql
CREATE MATERIALIZED VIEW hourly_execution_metrics
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    stage,
    avg(latency_ms) AS avg_latency_ms,
    percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms) AS p99_latency_ms,
    count(*) FILTER (WHERE success = true) AS success_count,
    count(*) FILTER (WHERE success = false) AS failure_count
FROM execution_logs
GROUP BY hour, stage;

SELECT add_continuous_aggregate_policy('hourly_execution_metrics',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
```

---

## **3.4 Data Retention Policies**

```sql
-- tick_data: 7일 보존
SELECT add_retention_policy('tick_data', INTERVAL '7 days');

-- ohlcv_1m: 30일 보존
SELECT add_retention_policy('ohlcv_1m', INTERVAL '30 days');

-- ohlcv_1d: 영구 보존 (정책 없음)

-- execution_logs: 90일 보존
SELECT add_retention_policy('execution_logs', INTERVAL '90 days');

-- daily_pnl: 영구 보존 (정책 없음)

-- hourly_execution_metrics: 180일 보존
SELECT add_retention_policy('hourly_execution_metrics', INTERVAL '180 days');
```

---

# **4. Data Adapter Layer**

## **4.1 Adapter Interface**

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class DataSourceAdapter(ABC):
    """데이터 소스 추상 인터페이스"""

    @abstractmethod
    def fetch_positions(self) -> List[Position]:
        """포지션 조회"""
        pass

    @abstractmethod
    def update_position(self, symbol: str, qty: Decimal, avg_price: Decimal):
        """포지션 업데이트"""
        pass

    @abstractmethod
    def append_ledger(self, entry: LedgerEntry) -> bool:
        """거래 원장 추가"""
        pass

    @abstractmethod
    def fetch_ohlcv(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = '1d'
    ) -> List[OHLCV]:
        """OHLCV 데이터 조회"""
        pass

    @abstractmethod
    def fetch_tick_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime
    ) -> List[TickData]:
        """틱 데이터 조회 (TimescaleDB 전용)"""
        pass
```

---

## **4.2 TimescaleDBAdapter 구현**

```python
import psycopg2
from psycopg2.extras import RealDictCursor

class TimescaleDBAdapter(DataSourceAdapter):
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(
            connection_string,
            cursor_factory=RealDictCursor
        )

    def fetch_positions(self) -> List[Position]:
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT symbol, qty, avg_price, market,
                       exposure_value, exposure_pct, unrealized_pnl
                FROM positions
                ORDER BY symbol
            """)
            rows = cur.fetchall()
            return [Position.from_db_row(row) for row in rows]

    def fetch_tick_data(
        self,
        symbol: str,
        start: datetime,
        end: datetime
    ) -> List[TickData]:
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT time, symbol, price, volume, bid, ask, source
                FROM tick_data
                WHERE symbol = %s
                  AND time >= %s
                  AND time < %s
                ORDER BY time
            """, (symbol, start, end))
            rows = cur.fetchall()
            return [TickData.from_db_row(row) for row in rows]

    def append_ledger(self, entry: LedgerEntry) -> bool:
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO t_ledger
                (timestamp, symbol, side, qty, price, amount, fee, strategy_tag, order_id, broker)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                entry.timestamp,
                entry.symbol,
                entry.side,
                entry.qty,
                entry.price,
                entry.amount,
                entry.fee,
                entry.strategy_tag,
                entry.order_id,
                entry.broker
            ))
            self.conn.commit()
            return True
```

---

## **4.3 GoogleSheetsAdapter (Backward Compatibility)**

```python
import gspread

class GoogleSheetsAdapter(DataSourceAdapter):
    def __init__(self, credentials, spreadsheet_id):
        self.gc = gspread.authorize(credentials)
        self.sh = self.gc.open_by_key(spreadsheet_id)

    def fetch_positions(self) -> List[Position]:
        ws = self.sh.worksheet('Position')
        rows = ws.get_all_records()
        return [Position.from_sheets_row(row) for row in rows]

    def fetch_tick_data(self, symbol, start, end) -> List[TickData]:
        # Google Sheets는 틱 데이터 미지원
        raise NotImplementedError("Google Sheets does not support tick data")
```

---

## **4.4 HybridAdapter (Dual-Write Mode)**

마이그레이션 기간 동안 두 소스에 동시 쓰기.

```python
class HybridAdapter(DataSourceAdapter):
    def __init__(self, sheets_adapter, db_adapter):
        self.sheets = sheets_adapter
        self.db = db_adapter

    def append_ledger(self, entry: LedgerEntry) -> bool:
        # Dual-Write
        sheets_success = self.sheets.append_ledger(entry)
        db_success = self.db.append_ledger(entry)
        return sheets_success and db_success

    def fetch_positions(self) -> List[Position]:
        # Read from DB (primary)
        return self.db.fetch_positions()

    def fetch_tick_data(self, symbol, start, end) -> List[TickData]:
        # Only DB supports tick data
        return self.db.fetch_tick_data(symbol, start, end)
```

---

# **5. Migration Strategy**

## **5.1 Migration Phases**

| Phase | 기간 | 작업 | Risk Level |
|-------|------|------|-----------|
| Phase 0 | Week 1 | 인프라 구축 (PostgreSQL + TimescaleDB) | Low |
| Phase 1 | Week 2-3 | Schema 마이그레이션, Adapter 구현 | Medium |
| Phase 2 | Week 4-6 | Dual-Write 모드 (Sheets + DB) | Medium |
| Phase 3 | Week 7-8 | Read 트래픽 DB로 이동 | Medium |
| Phase 4 | Week 9-10 | Sheets Read-Only, 데이터 정합성 검증 | Low |
| Phase 5 | Week 11+ | Full DB Migration, Sheets 백업용 | Low |

---

## **5.2 Phase 2: Dual-Write Mode 구현**

```python
# config.py
DATA_SOURCE_MODE = "HYBRID"  # "SHEETS_ONLY" | "HYBRID" | "DB_ONLY"

# main.py
if DATA_SOURCE_MODE == "SHEETS_ONLY":
    adapter = GoogleSheetsAdapter(...)
elif DATA_SOURCE_MODE == "DB_ONLY":
    adapter = TimescaleDBAdapter(...)
elif DATA_SOURCE_MODE == "HYBRID":
    sheets = GoogleSheetsAdapter(...)
    db = TimescaleDBAdapter(...)
    adapter = HybridAdapter(sheets, db)
```

---

## **5.3 데이터 정합성 검증**

```python
def verify_data_consistency():
    """Sheets vs DB 데이터 일치 검증"""
    sheets_positions = sheets_adapter.fetch_positions()
    db_positions = db_adapter.fetch_positions()

    mismatches = []
    for sp in sheets_positions:
        dp = next((p for p in db_positions if p.symbol == sp.symbol), None)
        if not dp:
            mismatches.append(f"Missing in DB: {sp.symbol}")
        elif sp.qty != dp.qty or sp.avg_price != dp.avg_price:
            mismatches.append(f"Mismatch {sp.symbol}: Sheets({sp.qty}, {sp.avg_price}) vs DB({dp.qty}, {dp.avg_price})")

    if mismatches:
        raise DataConsistencyError("\n".join(mismatches))

    log_info("Data consistency verified: OK")
```

---

## **5.4 Rollback Plan**

Phase 3-4에서 문제 발생 시:

1. `DATA_SOURCE_MODE = "SHEETS_ONLY"` 로 즉시 전환
2. DB 트래픽 중단
3. 원인 분석 후 재시도

---

# **6. Performance Optimization**

## **6.1 Index Strategy**

```sql
-- 자주 사용되는 쿼리 패턴
-- 1. 종목별 최근 틱 데이터 조회
CREATE INDEX idx_tick_symbol_time ON tick_data (symbol, time DESC);

-- 2. 전략별 거래 내역 조회
CREATE INDEX idx_ledger_strategy_time ON t_ledger (strategy_tag, timestamp DESC);

-- 3. 최근 실행 로그 조회
CREATE INDEX idx_exec_logs_time ON execution_logs (time DESC);
```

---

## **6.2 Connection Pooling**

```python
from psycopg2 import pool

# Connection Pool 생성
db_pool = pool.ThreadedConnectionPool(
    minconn=5,
    maxconn=20,
    host="localhost",
    database="qts",
    user="qts_user",
    password="***"
)

def get_db_connection():
    return db_pool.getconn()

def release_db_connection(conn):
    db_pool.putconn(conn)
```

---

## **6.3 Query Optimization Example**

```sql
-- Bad (Sequential Scan)
SELECT * FROM tick_data WHERE symbol = '005930' ORDER BY time DESC LIMIT 1000;

-- Good (Index Scan)
SELECT time, symbol, price, volume, bid, ask
FROM tick_data
WHERE symbol = '005930' AND time >= NOW() - INTERVAL '1 hour'
ORDER BY time DESC
LIMIT 1000;
```

---

# **7. Monitoring & Operations**

## **7.1 Database Health Metrics**

```sql
-- Hypertable 상태 확인
SELECT * FROM timescaledb_information.hypertables;

-- Chunk 상태
SELECT * FROM timescaledb_information.chunks;

-- Compression 상태
SELECT * FROM timescaledb_information.compression_settings;

-- 데이터 사이즈
SELECT
    hypertable_name,
    pg_size_pretty(hypertable_size(format('%I.%I', hypertable_schema, hypertable_name)::regclass))
FROM timescaledb_information.hypertables;
```

---

## **7.2 Backup Strategy**

```bash
# Daily Backup
pg_dump -h localhost -U qts_user -d qts -F c -f qts_backup_$(date +%Y%m%d).dump

# Restore
pg_restore -h localhost -U qts_user -d qts qts_backup_20260131.dump
```

---

## **7.3 Alert Rules**

| Metric | Threshold | Action |
|--------|----------|--------|
| Connection Pool Usage | > 90% | Scale up |
| Query Latency p99 | > 500ms | Optimize query |
| Disk Usage | > 80% | Retention policy adjustment |
| Replication Lag | > 10s | Check replication |

---

# **8. Appendix**

## **8.1 Complete Schema DDL**

(모든 테이블 DDL 포함)

## **8.2 Sample Queries**

```sql
-- 최근 1시간 삼성전자 1분봉
SELECT * FROM ohlcv_1m
WHERE symbol = '005930' AND bucket >= NOW() - INTERVAL '1 hour'
ORDER BY bucket DESC;

-- 오늘 전략별 손익
SELECT
    strategy_tag,
    sum(CASE WHEN side = 'SELL' THEN amount - fee ELSE -(amount + fee) END) AS pnl
FROM t_ledger
WHERE timestamp >= CURRENT_DATE
GROUP BY strategy_tag;

-- PreCheck 단계 평균 레이턴시 (최근 1시간)
SELECT
    avg(latency_ms) AS avg_ms,
    percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms) AS p99_ms
FROM execution_logs
WHERE stage = 'PRECHECK' AND time >= NOW() - INTERVAL '1 hour';
```

---

**QTS Data Layer Architecture v1.0.0 — 완료됨**
