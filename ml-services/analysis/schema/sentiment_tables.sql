-- Table for storing aggregated sentiment scores
CREATE TABLE IF NOT EXISTS market_sentiment (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    sentiment_score FLOAT NOT NULL,   -- -1.0 to 1.0
    article_count INT NOT NULL,
    sentiment_magnitude FLOAT,        -- Average confidence/magnitude
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_sentiment_daily UNIQUE (timestamp, symbol)
);

-- Convert to Hypertable (partitioned by time)
SELECT create_hypertable('market_sentiment', 'timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_sentiment_symbol_time ON market_sentiment (symbol, timestamp DESC);
