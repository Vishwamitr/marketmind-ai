-- View to aggregate pattern statistics
CREATE OR REPLACE VIEW pattern_stats AS
SELECT 
    symbol,
    pattern_type,
    COUNT(*) as occurrence_count,
    MAX(start_time) as last_observed,
    AVG(confidence) as avg_confidence
FROM 
    chart_patterns
GROUP BY 
    symbol, pattern_type
ORDER BY 
    occurrence_count DESC;

-- Indexing detected patterns for faster aggregation was done in patterns.sql
