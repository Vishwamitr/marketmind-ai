const API_BASE_URL = "http://localhost:8000";

export const endpoints = {
    // Market Data
    market_overview: `${API_BASE_URL}/api/market/overview`,
    market_movers: `${API_BASE_URL}/api/market/movers`,
    market_bulk: `${API_BASE_URL}/api/market/bulk`,
    market_history: (symbol: string) => `${API_BASE_URL}/api/market/history/${symbol}`,
    market_latest: (symbol: string) => `${API_BASE_URL}/api/market/latest/${symbol}`,
    market_anomalies: `${API_BASE_URL}/api/market/anomalies`,
    market_candles: (symbol: string) => `${API_BASE_URL}/api/market/candles/${symbol}`,

    // Watchlist
    watchlist: `${API_BASE_URL}/api/watchlist`,
    watchlist_data: `${API_BASE_URL}/api/watchlist/data`,
    watchlist_search: (q: string) => `${API_BASE_URL}/api/watchlist/search?q=${encodeURIComponent(q)}`,
    watchlist_remove: (symbol: string) => `${API_BASE_URL}/api/watchlist/${symbol}`,

    // AI Recommendations
    recommend: (symbol: string) => `${API_BASE_URL}/api/recommend/${symbol}`,
    recommend_all: `${API_BASE_URL}/api/recommend/all/overview`,

    // Predictions
    predict: (symbol: string) => `${API_BASE_URL}/api/predict/${symbol}`,
    predict_all: `${API_BASE_URL}/api/predict/batch/overview`,

    // News & Sentiment
    news: `${API_BASE_URL}/api/news`,
    sentiment_trend: `${API_BASE_URL}/api/news/sentiment_trend`,
    news_sentiment: (symbol: string) => `${API_BASE_URL}/api/news/sentiment/${symbol}`,

    // Backtest
    backtest: `${API_BASE_URL}/api/backtest/run`,

    // Portfolio
    portfolio: `${API_BASE_URL}/api/portfolio`,
    order: `${API_BASE_URL}/api/order`,

    // Admin
    admin_stats: `${API_BASE_URL}/api/admin/stats`,
    admin_logs: `${API_BASE_URL}/api/admin/logs`,

    // Model Monitor
    monitor_metrics: `${API_BASE_URL}/api/monitor/metrics`,
    monitor_calculate: `${API_BASE_URL}/api/monitor/calculate`,
    monitor_logs: `${API_BASE_URL}/api/monitor/logs`,

    // Mutual Funds
    mf_list: `${API_BASE_URL}/api/mf/list`,
    mf_search: (q: string) => `${API_BASE_URL}/api/mf/search?q=${encodeURIComponent(q)}`,
    mf_history: (symbol: string) => `${API_BASE_URL}/api/mf/history/${symbol}`,
    mf_top_performers: `${API_BASE_URL}/api/mf/top-performers`,
    mf_categories: `${API_BASE_URL}/api/mf/categories`,

    // Options
    options_chain: (symbol: string) => `${API_BASE_URL}/api/options/chain/${symbol}`,
    options_expiries: (symbol: string) => `${API_BASE_URL}/api/options/expiries/${symbol}`,
    options_overview: `${API_BASE_URL}/api/options/overview`,
    options_max_pain: (symbol: string) => `${API_BASE_URL}/api/options/max-pain/${symbol}`,
    options_strategy_payoff: `${API_BASE_URL}/api/options/strategy/payoff`,
    options_strategy_templates: `${API_BASE_URL}/api/options/strategies/templates`,
    market_screener: `${API_BASE_URL}/api/market/screener`,
    market_hours: `${API_BASE_URL}/api/market/hours`,

    // IV Smile
    options_iv_smile: (symbol: string) => `${API_BASE_URL}/api/options/iv-smile/${symbol}`,

    // Portfolio Analytics
    portfolio_analytics: `${API_BASE_URL}/api/portfolio/analytics`,

    // Alerts
    alerts: `${API_BASE_URL}/api/alerts`,
    alerts_triggered: `${API_BASE_URL}/api/alerts/triggered`,
    alerts_check: `${API_BASE_URL}/api/alerts/check`,
    alerts_delete: (id: number) => `${API_BASE_URL}/api/alerts/${id}`,
};

export default API_BASE_URL;
