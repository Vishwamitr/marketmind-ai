-- Table for storing detected chart patterns
CREATE TABLE IF NOT EXISTS chart_patterns (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL, -- e.g., 'DOJI', 'HAMMER', 'DOUBLE_TOP'
    confidence FLOAT DEFAULT 1.0,      -- 0.0 to 1.0
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    metadata JSONB,                    -- Extra details (e.g., support level price)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_pattern UNIQUE (symbol, pattern_type, start_time)
);

CREATE INDEX IF NOT EXISTS idx_patterns_symbol_time ON chart_patterns (symbol, start_time DESC);
