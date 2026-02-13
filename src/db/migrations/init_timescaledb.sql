-- QTS TimescaleDB Schema Initialization
-- 근거: docs/arch/sub/18_Data_Layer_Architecture.md §3

-- Enable TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 1. Regular Tables
CREATE TABLE IF NOT EXISTS positions (
    symbol VARCHAR(20) PRIMARY KEY,
    qty DECIMAL(18, 8) NOT NULL DEFAULT 0,
    avg_price DECIMAL(18, 8) NOT NULL DEFAULT 0,
    unrealized_pnl DECIMAL(18, 8) DEFAULT 0,
    exposure_pct DECIMAL(5, 4) DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS strategies (
    strategy_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    params JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_configs (
    config_id VARCHAR(50) PRIMARY KEY,
    params JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Hypertables
CREATE TABLE IF NOT EXISTS t_ledger (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    qty DECIMAL(18, 8) NOT NULL,
    price DECIMAL(18, 8) NOT NULL,
    fee DECIMAL(18, 8) DEFAULT 0,
    strategy VARCHAR(50),
    order_id VARCHAR(100),
    broker VARCHAR(50)
);
SELECT create_hypertable('t_ledger', 'time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS tick_data (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) DEFAULT 0,
    side VARCHAR(10)
);
SELECT create_hypertable('tick_data', 'time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS ohlcv_1d (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    open DECIMAL(18, 8),
    high DECIMAL(18, 8),
    low DECIMAL(18, 8),
    close DECIMAL(18, 8),
    volume DECIMAL(18, 8)
);
SELECT create_hypertable('ohlcv_1d', 'time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS execution_logs (
    time TIMESTAMPTZ NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    latency_ms DECIMAL(10, 3),
    success BOOLEAN DEFAULT TRUE,
    error_code VARCHAR(50)
);
SELECT create_hypertable('execution_logs', 'time', if_not_exists => TRUE);

-- 3. Indexes
CREATE INDEX IF NOT EXISTS idx_t_ledger_symbol_time ON t_ledger (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_tick_data_symbol_time ON tick_data (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_ohlcv_1d_symbol_time ON ohlcv_1d (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_execution_logs_order ON execution_logs (order_id, time DESC);

-- 4. Retention Policies
SELECT add_retention_policy('tick_data', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_retention_policy('execution_logs', INTERVAL '90 days', if_not_exists => TRUE);

-- 5. Continuous Aggregates
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
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE);

SELECT add_retention_policy('ohlcv_1m', INTERVAL '30 days', if_not_exists => TRUE);
