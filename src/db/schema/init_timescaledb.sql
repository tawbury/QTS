-- ============================================================
-- QTS TimescaleDB Schema Initialization
-- ============================================================
-- 근거: docs/arch/sub/18_Data_Layer_Architecture.md §3
-- 실행: psql -h $DB_HOST -U $DB_USER -d qts -f init_timescaledb.sql
-- ============================================================

-- TimescaleDB 확장 활성화
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================
-- 1. Regular Tables (트랜잭션 데이터) — §3.1
-- ============================================================

-- 1.1 positions: 현재 포지션 정보
CREATE TABLE IF NOT EXISTS positions (
    symbol VARCHAR(20) PRIMARY KEY,
    qty DECIMAL(18, 8) NOT NULL CHECK (qty >= 0),
    avg_price DECIMAL(18, 8) NOT NULL,
    market VARCHAR(10),
    exposure_value DECIMAL(18, 2),
    exposure_pct DECIMAL(5, 4),
    unrealized_pnl DECIMAL(18, 2),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_positions_market ON positions(market);
CREATE INDEX IF NOT EXISTS idx_positions_updated ON positions(updated_at DESC);

-- 1.2 t_ledger: 거래 원장
CREATE TABLE IF NOT EXISTS t_ledger (
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

CREATE INDEX IF NOT EXISTS idx_ledger_timestamp ON t_ledger(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ledger_symbol ON t_ledger(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ledger_strategy ON t_ledger(strategy_tag, timestamp DESC);

-- 1.3 strategies: 전략 파라미터
CREATE TABLE IF NOT EXISTS strategies (
    strategy_id VARCHAR(50) PRIMARY KEY,
    param_name VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string',
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_strategies_updated ON strategies(updated_at DESC);

-- 1.4 risk_configs: 리스크 설정
CREATE TABLE IF NOT EXISTS risk_configs (
    config_key VARCHAR(100) PRIMARY KEY,
    value DECIMAL(18, 8) NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================
-- 2. TimescaleDB Hypertables (시계열 데이터) — §3.2
-- ============================================================

-- 2.1 tick_data: 원시 틱 데이터
CREATE TABLE IF NOT EXISTS tick_data (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(18, 8) NOT NULL,
    volume BIGINT NOT NULL,
    bid DECIMAL(18, 8),
    ask DECIMAL(18, 8),
    source VARCHAR(20)
);

SELECT create_hypertable('tick_data', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_tick_symbol_time ON tick_data (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_tick_source ON tick_data (source, time DESC);

-- tick_data 압축 (7일 이후)
ALTER TABLE tick_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol'
);

SELECT add_compression_policy('tick_data', INTERVAL '7 days', if_not_exists => TRUE);

-- 2.2 ohlcv_1d: 일봉 데이터
CREATE TABLE IF NOT EXISTS ohlcv_1d (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    open DECIMAL(18, 8) NOT NULL,
    high DECIMAL(18, 8) NOT NULL,
    low DECIMAL(18, 8) NOT NULL,
    close DECIMAL(18, 8) NOT NULL,
    volume BIGINT NOT NULL,
    UNIQUE (time, symbol)
);

SELECT create_hypertable('ohlcv_1d', 'time',
    chunk_time_interval => INTERVAL '30 days',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_ohlcv_1d_symbol_time ON ohlcv_1d (symbol, time DESC);

-- 2.3 execution_logs: 실행 로그
CREATE TABLE IF NOT EXISTS execution_logs (
    time TIMESTAMPTZ NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    latency_ms DECIMAL(10, 3),
    success BOOLEAN NOT NULL,
    error_code VARCHAR(50)
);

SELECT create_hypertable('execution_logs', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_exec_logs_order ON execution_logs (order_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_exec_logs_stage ON execution_logs (stage, time DESC);

-- 2.4 feedback_data: 피드백 루프 데이터 (§20 Feedback Loop)
CREATE TABLE IF NOT EXISTS feedback_data (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    strategy_tag VARCHAR(50),
    total_slippage_bps DECIMAL(10, 3),
    avg_fill_latency_ms DECIMAL(10, 3),
    partial_fill_ratio DECIMAL(5, 4),
    total_filled_qty DECIMAL(18, 8),
    avg_fill_price DECIMAL(18, 8),
    volatility_at_execution DECIMAL(10, 6),
    spread_at_execution DECIMAL(10, 3),
    depth_at_execution INT,
    execution_quality_score DECIMAL(5, 4),
    market_impact_bps DECIMAL(10, 3),
    order_type VARCHAR(20),
    original_qty DECIMAL(18, 8)
);

SELECT create_hypertable('feedback_data', 'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_feedback_symbol_time ON feedback_data (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_strategy_time ON feedback_data (strategy_tag, time DESC);


-- ============================================================
-- 3. Continuous Aggregates — §3.3
-- ============================================================

-- 3.1 ohlcv_1m: tick_data → 1분봉
CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_1m
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
GROUP BY bucket, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('ohlcv_1m',
    start_offset => INTERVAL '1 hour',
    end_offset   => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);

-- 3.2 daily_pnl: t_ledger → 일별 손익
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_pnl
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    symbol,
    sum(CASE WHEN side = 'BUY' THEN -amount WHEN side = 'SELL' THEN amount END) AS realized_pnl,
    count(*) AS trade_count
FROM t_ledger
GROUP BY day, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('daily_pnl',
    start_offset => INTERVAL '7 days',
    end_offset   => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- 3.3 hourly_execution_metrics: 시간별 실행 품질
CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_execution_metrics
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    stage,
    avg(latency_ms) AS avg_latency_ms,
    percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms) AS p99_latency_ms,
    count(*) FILTER (WHERE success = true) AS success_count,
    count(*) FILTER (WHERE success = false) AS failure_count
FROM execution_logs
GROUP BY hour, stage
WITH NO DATA;

SELECT add_continuous_aggregate_policy('hourly_execution_metrics',
    start_offset => INTERVAL '3 days',
    end_offset   => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);


-- ============================================================
-- 4. Retention Policies — §3.4
-- ============================================================

SELECT add_retention_policy('tick_data', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_retention_policy('execution_logs', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('feedback_data', INTERVAL '180 days', if_not_exists => TRUE);
-- ohlcv_1d: 영구 보존 (정책 없음)
-- daily_pnl: 영구 보존 (정책 없음)


-- ============================================================
-- QTS TimescaleDB Schema v1.0.0 — 완료
-- ============================================================
