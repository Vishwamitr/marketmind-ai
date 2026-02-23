import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, TrendingUp, Activity, BarChart3, Zap, RefreshCw } from 'lucide-react';
import MetricsCard from '../components/MetricsCard';
import AdvancedChart from '../components/AdvancedChart';
import { endpoints } from '../config';

interface LatestData {
    price: number;
    regime: string;
    adx: number;
    atr: number;
    sma_50: number;
    sma_200: number;
    reason: string;
}

const TIMEFRAMES = [
    { label: '1M', period: '1mo', interval: '1d' },
    { label: '3M', period: '3mo', interval: '1d' },
    { label: '6M', period: '6mo', interval: '1d' },
    { label: '1Y', period: '1y', interval: '1d' },
    { label: '2Y', period: '2y', interval: '1wk' },
    { label: '5Y', period: '5y', interval: '1wk' },
];

const AnalysisPage: React.FC = () => {
    const { symbol } = useParams<{ symbol: string }>();
    const [candles, setCandles] = useState<any[]>([]);
    const [latest, setLatest] = useState<LatestData | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTimeframe, setActiveTimeframe] = useState(3); // Default: 1Y
    const [refreshing, setRefreshing] = useState(false);
    const navigate = useNavigate();

    const fetchCandles = async (tfIndex?: number) => {
        const tf = TIMEFRAMES[tfIndex ?? activeTimeframe];
        try {
            setRefreshing(true);
            const res = await axios.get(
                `${endpoints.market_candles(symbol!)}?interval=${tf.interval}&period=${tf.period}`,
                { timeout: 20000 }
            );
            setCandles(res.data.candles || []);
        } catch (error) {
            console.error("Error fetching candles:", error);
        } finally {
            setRefreshing(false);
        }
    };

    useEffect(() => {
        const fetchAll = async () => {
            try {
                setLoading(true);

                // Fetch candles and latest data in parallel
                const [candleRes, latestRes] = await Promise.allSettled([
                    axios.get(
                        `${endpoints.market_candles(symbol!)}?interval=1d&period=1y`,
                        { timeout: 20000 }
                    ),
                    axios.get(endpoints.market_latest(symbol!), { timeout: 10000 }),
                ]);

                if (candleRes.status === 'fulfilled') {
                    setCandles(candleRes.value.data.candles || []);
                }
                if (latestRes.status === 'fulfilled') {
                    setLatest(latestRes.value.data);
                }
            } catch (error) {
                console.error("Error fetching data:", error);
            } finally {
                setLoading(false);
            }
        };
        if (symbol) fetchAll();
    }, [symbol]);

    const getRegimeBadge = (regime: string) => {
        const r = regime.toLowerCase();
        if (r.includes('bull')) return <span className="badge badge-bullish">● Bullish</span>;
        if (r.includes('bear')) return <span className="badge badge-bearish">● Bearish</span>;
        if (r.includes('volatile')) return <span className="badge badge-volatile">● Volatile</span>;
        if (r.includes('sideways')) return <span className="badge badge-sideways">● Sideways</span>;
        return <span className="badge badge-unknown">● Unknown</span>;
    };

    if (loading) {
        return (
            <div className="animate-fade-in">
                <div className="page-header"><h1>Loading {symbol}...</h1></div>
                <div style={{ display: 'grid', gap: '16px' }}>
                    {[1, 2].map(i => <div key={i} className="skeleton" style={{ height: i === 1 ? '500px' : '200px' }} />)}
                </div>
            </div>
        );
    }

    // Derive summary stats from candle data
    const lastCandle = candles.length > 0 ? candles[candles.length - 1] : null;
    const prevCandle = candles.length > 1 ? candles[candles.length - 2] : null;
    const price = lastCandle?.close || latest?.price || 0;
    const change = prevCandle ? price - prevCandle.close : 0;
    const changePct = prevCandle && prevCandle.close > 0 ? (change / prevCandle.close) * 100 : 0;

    return (
        <div className="animate-fade-in">
            {/* Header */}
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <button
                        onClick={() => navigate('/')}
                        className="btn btn-ghost"
                        style={{ marginBottom: '12px', padding: '6px 12px', fontSize: '0.8rem' }}
                    >
                        <ArrowLeft size={14} /> Back to Dashboard
                    </button>
                    <h1 style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        {symbol}
                        <span style={{ fontSize: '0.5em', fontWeight: 400, color: 'var(--text-muted)' }}>NSE</span>
                    </h1>
                    <p>Professional Technical Analysis — OHLCV, Moving Averages, RSI, MACD, Bollinger Bands</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '2px', letterSpacing: '-0.02em' }}>
                        ₹{price.toFixed(2)}
                    </div>
                    <div style={{
                        fontSize: '0.9rem',
                        fontWeight: 600,
                        color: change >= 0 ? '#22c55e' : '#ef4444',
                        marginBottom: '8px',
                    }}>
                        {change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePct.toFixed(2)}%)
                    </div>
                    {latest && getRegimeBadge(latest.regime)}
                </div>
            </div>

            {/* Metrics Cards */}
            {(latest || lastCandle) && (
                <div className="grid-metrics">
                    <MetricsCard
                        label="Market Regime"
                        value={latest?.regime?.replace(/_/g, ' ') || 'UNKNOWN'}
                        color={latest?.regime?.includes('BULL') ? 'green' : 'red'}
                        icon={<Zap size={24} />}
                    />
                    <MetricsCard
                        label="RSI (14)"
                        value={lastCandle?.rsi ? lastCandle.rsi.toFixed(1) : 'N/A'}
                        subValue={lastCandle?.rsi > 70 ? '⚠️ Overbought' : lastCandle?.rsi < 30 ? '🟢 Oversold' : 'Neutral'}
                        color="purple"
                        icon={<Activity size={24} />}
                    />
                    <MetricsCard
                        label="ADX"
                        value={lastCandle?.adx ? lastCandle.adx.toFixed(1) : (latest?.adx ? latest.adx.toFixed(1) : 'N/A')}
                        subValue={(lastCandle?.adx || latest?.adx || 0) > 25 ? 'Strong Trend' : 'Weak Trend'}
                        color="amber"
                        icon={<BarChart3 size={24} />}
                    />
                    <MetricsCard
                        label="SMA 200"
                        value={lastCandle?.sma_200 ? `₹${lastCandle.sma_200.toFixed(0)}` : 'N/A'}
                        subValue={lastCandle?.sma_200 && price > lastCandle.sma_200 ? 'Price Above ✅' : 'Price Below ⚠️'}
                        color="cyan"
                        icon={<TrendingUp size={24} />}
                    />
                </div>
            )}

            {/* Regime Reason */}
            {latest?.reason && (
                <div className="glass-card-static" style={{ padding: '16px 20px', marginBottom: '24px', borderLeft: '3px solid var(--accent-indigo)' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>AI Analysis</span>
                    <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>{latest.reason}</span>
                </div>
            )}

            {/* Chart Card */}
            <div className="glass-card-static" style={{ padding: '20px', marginBottom: '20px' }}>
                {/* Timeframe Selector */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                        Candlestick Chart
                    </h3>
                    <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                        {TIMEFRAMES.map((tf, idx) => (
                            <button
                                key={tf.label}
                                onClick={() => { setActiveTimeframe(idx); fetchCandles(idx); }}
                                style={{
                                    padding: '4px 10px',
                                    fontSize: '0.7rem',
                                    fontWeight: 600,
                                    borderRadius: '6px',
                                    border: `1px solid ${idx === activeTimeframe ? 'var(--accent-indigo)' : 'var(--border-subtle)'}`,
                                    background: idx === activeTimeframe ? 'rgba(99,102,241,0.15)' : 'transparent',
                                    color: idx === activeTimeframe ? 'var(--accent-indigo)' : 'var(--text-muted)',
                                    cursor: 'pointer',
                                    transition: 'all 0.15s',
                                }}
                            >
                                {tf.label}
                            </button>
                        ))}
                        <button
                            onClick={() => fetchCandles()}
                            className="btn btn-ghost"
                            style={{ padding: '4px 8px', marginLeft: '8px' }}
                            disabled={refreshing}
                        >
                            <RefreshCw size={14} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
                        </button>
                    </div>
                </div>

                {candles.length > 0 ? (
                    <AdvancedChart
                        data={candles}
                        symbol={symbol!}
                        height={500}
                        showVolume={true}
                        showSMA={true}
                        showRSI={false}
                        showMACD={false}
                    />
                ) : (
                    <div style={{
                        height: '500px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--text-muted)',
                        fontSize: '0.9rem',
                    }}>
                        {refreshing ? 'Loading chart data...' : 'No chart data available. Check if the backend is running.'}
                    </div>
                )}
            </div>
        </div>
    );
};

export default AnalysisPage;
