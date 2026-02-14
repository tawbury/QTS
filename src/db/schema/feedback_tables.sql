-- ETEDA DB Feedback Loop - DDL
-- feedback_data, decision_log 테이블 + retention 정책

-- feedback_data: 실행 품질 피드백 (Hypertable, 7일 청크)
CREATE TABLE IF NOT EXISTS feedback_data (
    time            TIMESTAMPTZ      NOT NULL,
    symbol          TEXT             NOT NULL,
    strategy_tag    TEXT             NOT NULL DEFAULT '',
    order_id        TEXT,
    slippage_bps    DOUBLE PRECISION NOT NULL DEFAULT 0,
    quality_score   DOUBLE PRECISION NOT NULL DEFAULT 0,
    impact_bps      DOUBLE PRECISION NOT NULL DEFAULT 0,
    fill_latency_ms DOUBLE PRECISION NOT NULL DEFAULT 0,
    fill_ratio      DOUBLE PRECISION NOT NULL DEFAULT 0,
    filled_qty      NUMERIC          NOT NULL DEFAULT 0,
    fill_price      NUMERIC          NOT NULL DEFAULT 0,
    original_qty    NUMERIC          NOT NULL DEFAULT 0,
    volatility      DOUBLE PRECISION NOT NULL DEFAULT 0,
    spread_bps      DOUBLE PRECISION NOT NULL DEFAULT 0,
    depth           INTEGER          NOT NULL DEFAULT 0,
    order_type      TEXT             NOT NULL DEFAULT 'MARKET'
);

SELECT create_hypertable('feedback_data', 'time',
       chunk_time_interval => INTERVAL '7 days',
       if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_feedback_symbol_time
    ON feedback_data (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_strategy_time
    ON feedback_data (strategy_tag, time DESC);

-- decision_log: 의사결정 감사 추적
CREATE TABLE IF NOT EXISTS decision_log (
    time                   TIMESTAMPTZ      NOT NULL,
    cycle_id               TEXT             NOT NULL,
    symbol                 TEXT             NOT NULL,
    action                 TEXT             NOT NULL,
    strategy_tag           TEXT             NOT NULL DEFAULT '',
    price                  NUMERIC,
    qty                    INTEGER,
    signal_confidence      DOUBLE PRECISION,
    risk_score             DOUBLE PRECISION,
    operating_state        TEXT,
    feedback_applied       BOOLEAN          NOT NULL DEFAULT FALSE,
    feedback_slippage_bps  DOUBLE PRECISION,
    feedback_quality_score DOUBLE PRECISION,
    capital_blocked        BOOLEAN          NOT NULL DEFAULT FALSE,
    approved               BOOLEAN          NOT NULL DEFAULT FALSE,
    reason                 TEXT,
    act_status             TEXT,
    metadata               JSONB
);

SELECT create_hypertable('decision_log', 'time',
       chunk_time_interval => INTERVAL '30 days',
       if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_decision_symbol_time
    ON decision_log (symbol, time DESC);

-- retention policies
SELECT add_retention_policy('feedback_data',
       INTERVAL '180 days', if_not_exists => TRUE);
SELECT add_retention_policy('decision_log',
       INTERVAL '365 days', if_not_exists => TRUE);
