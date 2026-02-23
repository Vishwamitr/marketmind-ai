-- Table for storing event impact analysis
CREATE TABLE IF NOT EXISTS event_impact (
    event_id VARCHAR(64) PRIMARY KEY, -- Unique ID for the event (e.g., hash of symbol + time)
    symbol VARCHAR(20) NOT NULL,
    event_date TIMESTAMPTZ NOT NULL,
    sentiment_score FLOAT NOT NULL,
    price_at_event FLOAT,
    price_after_24h FLOAT,
    price_change_24h FLOAT,           -- Percentage change
    impact_label VARCHAR(20),         -- POSITIVE_CORRELATION, NEGATIVE_CORRELATION, NEUTRAL
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_impact_symbol_date ON event_impact (symbol, event_date DESC);
