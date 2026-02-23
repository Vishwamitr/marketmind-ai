-- Stocks master table
CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    isin VARCHAR(12),
    is_active BOOLEAN DEFAULT true,
    listed_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    prediction_date DATE NOT NULL,
    prediction_timestamp TIMESTAMPTZ NOT NULL,
    model_version VARCHAR(50),
    timeframe VARCHAR(20), -- 1d, 1w, 1m
    predicted_direction VARCHAR(10), -- UP, DOWN, SIDEWAYS
    predicted_price DECIMAL(10,2),
    confidence_score DECIMAL(5,4),
    prediction_details JSONB, -- model weights, features used
    actual_price DECIMAL(10,2),
    actual_direction VARCHAR(10),
    prediction_error DECIMAL(10,2),
    is_correct BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_symbol_date ON predictions (symbol, prediction_date DESC);

-- Model performance tracking
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    evaluation_date DATE NOT NULL,
    metric_name VARCHAR(50), -- accuracy, precision, recall, mse, mae
    metric_value DECIMAL(10,6),
    timeframe VARCHAR(20),
    stock_symbol VARCHAR(20),
    sample_size INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Pattern occurrences
CREATE TABLE IF NOT EXISTS pattern_occurrences (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    pattern_type VARCHAR(100), -- head_shoulders, double_top, etc.
    detected_date DATE NOT NULL,
    pattern_start_date DATE,
    pattern_end_date DATE,
    confidence DECIMAL(5,4),
    historical_success_rate DECIMAL(5,4),
    price_at_detection DECIMAL(10,2),
    price_after_1d DECIMAL(10,2),
    price_after_1w DECIMAL(10,2),
    pattern_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User portfolios
CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER, -- Will reference users table once Auth is set up
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS portfolio_holdings (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER REFERENCES portfolios(id),
    symbol VARCHAR(20),
    quantity INTEGER,
    average_price DECIMAL(10,2),
    added_at TIMESTAMP DEFAULT NOW()
);
