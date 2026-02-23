-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Stock prices table
CREATE TABLE IF NOT EXISTS stock_prices (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    vwap DECIMAL(10,2),
    trades INTEGER,
    deliverable_qty BIGINT,
    deliverable_percent DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, symbol)
);

-- Convert to hypertable
SELECT create_hypertable('stock_prices', 'timestamp', if_not_exists => TRUE);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol ON stock_prices (symbol, timestamp DESC);

-- Technical indicators table
CREATE TABLE IF NOT EXISTS technical_indicators (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    rsi_14 DECIMAL(5,2),
    macd DECIMAL(10,4),
    macd_signal DECIMAL(10,4),
    bb_upper DECIMAL(10,2),
    bb_middle DECIMAL(10,2),
    bb_lower DECIMAL(10,2),
    sma_20 DECIMAL(10,2),
    sma_50 DECIMAL(10,2),
    sma_200 DECIMAL(10,2),
    ema_12 DECIMAL(10,2),
    ema_26 DECIMAL(10,2),
    adx DECIMAL(5,2),
    atr DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, symbol)
);

-- Convert to hypertable
SELECT create_hypertable('technical_indicators', 'timestamp', if_not_exists => TRUE);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_technical_indicators_symbol ON technical_indicators (symbol, timestamp DESC);
