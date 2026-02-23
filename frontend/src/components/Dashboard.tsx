import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import MetricsCard from './MetricsCard';
import {
    Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area
} from 'recharts';
import {
    TrendingUp, TrendingDown, Activity, BarChart3, Zap, RefreshCw
} from 'lucide-react';
import { endpoints } from '../config';
import MarketHoursWidget from './MarketHoursWidget';

interface StockOverview {
    symbol: string;
    timestamp: string;
    price: number;
    open: number;
    high: number;
    low: number;
    volume: number;
    prev_close: number | null;
    change_pct: number;
    regime: string;
}

interface Mover {
    symbol: string;
    price: number;
    volume: number;
    prev_close: number;
    change_pct: number;
}

const Dashboard: React.FC = () => {
    const [stocks, setStocks] = useState<StockOverview[]>([]);
    const [gainers, setGainers] = useState<Mover[]>([]);
    const [losers, setLosers] = useState<Mover[]>([]);
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdate, setLastUpdate] = useState<string>('');
    const navigate = useNavigate();

    const fetchData = async () => {
        try {
            setLoading(true);

            // Use allSettled so partial failures don't kill the whole dashboard
            const [overviewResult, moversResult] = await Promise.allSettled([
                axios.get(endpoints.market_overview, { timeout: 15000 }),
                axios.get(`${endpoints.market_movers}?limit=5`, { timeout: 15000 }),
            ]);

            // Check if at least one request succeeded
            const overviewOk = overviewResult.status === 'fulfilled';
            const moversOk = moversResult.status === 'fulfilled';

            if (!overviewOk && !moversOk) {
                // Both failed — show error
                setError('Unable to connect to MarketMind API. Start the backend with: cd ml-services && uvicorn api.main:app --reload');
                setLoading(false);
                return;
            }

            if (overviewOk) {
                setStocks(overviewResult.value.data.stocks || []);
            }
            if (moversOk) {
                setGainers(moversResult.value.data.gainers || []);
                setLosers(moversResult.value.data.losers || []);
            }

            setLastUpdate(new Date().toLocaleTimeString());

            // Fetch history for the top stock (non-critical, ignore errors)
            try {
                const stockList = overviewOk ? overviewResult.value.data.stocks : [];
                if (stockList?.length > 0) {
                    const topSymbol = stockList[0].symbol;
                    const histRes = await axios.get(`${endpoints.market_history(topSymbol)}?limit=60`, { timeout: 10000 });
                    setHistory(histRes.data || []);
                }
            } catch {
                // History fetch failed — not critical, ignore
            }

            setError(null);
        } catch (err: any) {
            console.error(err);
            setError('Unable to connect to MarketMind API. Start the backend with: cd ml-services && uvicorn api.main:app --reload');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5 * 60 * 1000);
        return () => clearInterval(interval);
    }, []);

    const getRegimeBadge = (regime: string) => {
        const r = regime.toLowerCase();
        if (r.includes('bull')) return <span className="badge badge-bullish">● Bullish</span>;
        if (r.includes('bear')) return <span className="badge badge-bearish">● Bearish</span>;
        if (r.includes('volatile')) return <span className="badge badge-volatile">● Volatile</span>;
        if (r.includes('sideways')) return <span className="badge badge-sideways">● Sideways</span>;
        return <span className="badge badge-unknown">● Unknown</span>;
    };

    const formatVolume = (v: number) => {
        if (v >= 10000000) return `${(v / 10000000).toFixed(1)}Cr`;
        if (v >= 100000) return `${(v / 100000).toFixed(1)}L`;
        if (v >= 1000) return `${(v / 1000).toFixed(1)}K`;
        return v.toString();
    };

    // Summary metrics
    const totalStocks = stocks.length;
    const bullishCount = stocks.filter(s => s.regime.toLowerCase().includes('bull')).length;
    const bearishCount = stocks.filter(s => s.regime.toLowerCase().includes('bear')).length;
    const avgChange = stocks.length > 0
        ? (stocks.reduce((sum, s) => sum + s.change_pct, 0) / stocks.length).toFixed(2)
        : '0';

    if (error && stocks.length === 0) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', flexDirection: 'column', gap: '16px' }}>
                <Zap size={48} style={{ color: 'var(--accent-indigo)', opacity: 0.5 }} />
                <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', textAlign: 'center', maxWidth: '500px' }}>
                    MarketMind API is not reachable. Make sure the backend server is running.
                </p>
                <code style={{ padding: '8px 16px', borderRadius: '8px', background: 'var(--bg-glass)', border: '1px solid var(--border-subtle)', fontSize: '0.8rem', color: 'var(--accent-indigo)' }}>
                    cd ml-services && uvicorn api.main:app --reload
                </code>
                <button className="btn btn-primary" onClick={fetchData}>
                    <RefreshCw size={16} /> Retry Connection
                </button>
            </div>
        );
    }

    return (
        <div className="animate-fade-in">
            {/* Header */}
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1>Market Dashboard</h1>
                    <p>Real-time overview of all tracked stocks</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {lastUpdate && (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            Updated {lastUpdate}
                        </span>
                    )}
                    <button className="btn btn-ghost" onClick={fetchData} disabled={loading}>
                        <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                        Refresh
                    </button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid-metrics">
                <MetricsCard
                    label="Tracked Stocks"
                    value={totalStocks}
                    color="blue"
                    icon={<BarChart3 size={28} />}
                />
                <MetricsCard
                    label="Market Sentiment"
                    value={`${avgChange}%`}
                    trend={parseFloat(avgChange) > 0 ? 'up' : parseFloat(avgChange) < 0 ? 'down' : 'neutral'}
                    subValue="Avg daily change"
                    color={parseFloat(avgChange) >= 0 ? 'green' : 'red'}
                    icon={<Activity size={28} />}
                />
                <MetricsCard
                    label="Bullish Stocks"
                    value={bullishCount}
                    subValue={`${totalStocks > 0 ? ((bullishCount / totalStocks) * 100).toFixed(0) : 0}% of market`}
                    color="green"
                    trend="up"
                    icon={<TrendingUp size={28} />}
                />
                <MetricsCard
                    label="Bearish Stocks"
                    value={bearishCount}
                    subValue={`${totalStocks > 0 ? ((bearishCount / totalStocks) * 100).toFixed(0) : 0}% of market`}
                    color="red"
                    trend="down"
                    icon={<TrendingDown size={28} />}
                />
            </div>

            {/* Market Hours & Global Indices */}
            <MarketHoursWidget />

            {/* Main Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '20px', marginBottom: '24px' }}>
                {/* Price Chart */}
                <div className="glass-card-static" style={{ padding: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                        <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                            {stocks[0]?.symbol || 'Stock'} Price History
                        </h3>
                    </div>
                    <div style={{ height: '280px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={history}>
                                <defs>
                                    <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                                        <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="timestamp" tickFormatter={(t) => new Date(t).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })} />
                                <YAxis domain={['auto', 'auto']} />
                                <Tooltip
                                    labelFormatter={(t) => new Date(t).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                                    contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '10px' }}
                                />
                                <Area type="monotone" dataKey="close" stroke="#6366f1" strokeWidth={2} fill="url(#priceGradient)" />
                                <Line type="monotone" dataKey="sma_200" stroke="#ef4444" dot={false} strokeWidth={1} strokeDasharray="4 4" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Top Movers */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    {/* Gainers */}
                    <div className="glass-card-static" style={{ padding: '20px', flex: 1 }}>
                        <h3 className="section-title">
                            <TrendingUp size={16} style={{ color: 'var(--accent-green)' }} /> Top Gainers
                        </h3>
                        {gainers.map((stock, i) => (
                            <div
                                key={stock.symbol}
                                onClick={() => navigate(`/analysis/${stock.symbol}`)}
                                className="animate-fade-in"
                                style={{
                                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                    padding: '10px 12px', borderRadius: '8px', marginBottom: '4px',
                                    cursor: 'pointer', transition: 'var(--transition)',
                                    animationDelay: `${i * 50}ms`,
                                    background: 'transparent',
                                }}
                                onMouseOver={(e) => (e.currentTarget.style.background = 'var(--bg-glass-hover)')}
                                onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
                            >
                                <div>
                                    <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{stock.symbol}</span>
                                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginLeft: '8px' }}>₹{stock.price.toFixed(2)}</span>
                                </div>
                                <span className="text-gain" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                                    +{stock.change_pct}%
                                </span>
                            </div>
                        ))}
                        {gainers.length === 0 && <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No data yet</p>}
                    </div>

                    {/* Losers */}
                    <div className="glass-card-static" style={{ padding: '20px', flex: 1 }}>
                        <h3 className="section-title">
                            <TrendingDown size={16} style={{ color: 'var(--accent-red)' }} /> Top Losers
                        </h3>
                        {losers.map((stock, i) => (
                            <div
                                key={stock.symbol}
                                onClick={() => navigate(`/analysis/${stock.symbol}`)}
                                className="animate-fade-in"
                                style={{
                                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                    padding: '10px 12px', borderRadius: '8px', marginBottom: '4px',
                                    cursor: 'pointer', transition: 'var(--transition)',
                                    animationDelay: `${i * 50}ms`,
                                }}
                                onMouseOver={(e) => (e.currentTarget.style.background = 'var(--bg-glass-hover)')}
                                onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
                            >
                                <div>
                                    <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{stock.symbol}</span>
                                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginLeft: '8px' }}>₹{stock.price.toFixed(2)}</span>
                                </div>
                                <span className="text-loss" style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                                    {stock.change_pct}%
                                </span>
                            </div>
                        ))}
                        {losers.length === 0 && <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No data yet</p>}
                    </div>
                </div>
            </div>

            {/* Market Overview Table */}
            <div className="glass-card-static" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 className="section-title" style={{ margin: 0 }}>
                        <BarChart3 size={16} /> All Stocks
                    </h3>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{totalStocks} stocks tracked</span>
                </div>
                <div style={{ overflowX: 'auto' }}>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Price</th>
                                <th>Change</th>
                                <th>Open</th>
                                <th>High</th>
                                <th>Low</th>
                                <th>Volume</th>
                                <th>Regime</th>
                            </tr>
                        </thead>
                        <tbody>
                            {stocks.map((stock, i) => (
                                <tr
                                    key={stock.symbol}
                                    onClick={() => navigate(`/analysis/${stock.symbol}`)}
                                    className="animate-fade-in"
                                    style={{ animationDelay: `${i * 30}ms` }}
                                >
                                    <td style={{ fontWeight: 600 }}>{stock.symbol}</td>
                                    <td>₹{stock.price.toFixed(2)}</td>
                                    <td>
                                        <span className={stock.change_pct >= 0 ? 'text-gain' : 'text-loss'} style={{ fontWeight: 600 }}>
                                            {stock.change_pct >= 0 ? '+' : ''}{stock.change_pct}%
                                        </span>
                                    </td>
                                    <td style={{ color: 'var(--text-secondary)' }}>₹{stock.open.toFixed(2)}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>₹{stock.high.toFixed(2)}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>₹{stock.low.toFixed(2)}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{formatVolume(stock.volume)}</td>
                                    <td>{getRegimeBadge(stock.regime)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {stocks.length === 0 && !loading && (
                    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                        No stock data available. Make sure Docker containers and ML services are running.
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
