import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Filter, TrendingUp, TrendingDown, ArrowUpDown, RefreshCw } from 'lucide-react';
import { endpoints } from '../config';

interface ScreenerStock {
    symbol: string;
    price: number;
    change_pct: number;
    volume: number;
    avg_volume: number;
    volume_ratio: number;
    rsi: number;
    high_52w: number;
    low_52w: number;
    from_52w_high: number;
    market_cap: number;
    market_cap_cr: number;
}

const PRESETS = [
    { label: '🚀 Top Gainers', params: { sort_by: 'change_pct', sort_order: 'desc' } },
    { label: '📉 Top Losers', params: { sort_by: 'change_pct', sort_order: 'asc' } },
    { label: '🔥 High Volume', params: { sort_by: 'volume_ratio', sort_order: 'desc' } },
    { label: '📊 Oversold (RSI < 30)', params: { max_rsi: 30, sort_by: 'rsi', sort_order: 'asc' } },
    { label: '⚠️ Overbought (RSI > 70)', params: { min_rsi: 70, sort_by: 'rsi', sort_order: 'desc' } },
    { label: '💎 Near 52W Low', params: { sort_by: 'from_52w_high', sort_order: 'asc' } },
];

const ScreenerPage: React.FC = () => {
    const [stocks, setStocks] = useState<ScreenerStock[]>([]);
    const [loading, setLoading] = useState(true);
    const [sortBy, setSortBy] = useState('change_pct');
    const [sortOrder, setSortOrder] = useState('desc');
    const [activePreset, setActivePreset] = useState(0);

    const fetchScreener = async (params: Record<string, any> = {}) => {
        setLoading(true);
        try {
            const queryParams = new URLSearchParams({
                sort_by: params.sort_by || sortBy,
                sort_order: params.sort_order || sortOrder,
                ...(params.min_rsi !== undefined ? { min_rsi: String(params.min_rsi) } : {}),
                ...(params.max_rsi !== undefined ? { max_rsi: String(params.max_rsi) } : {}),
            });
            const res = await axios.get(`${endpoints.market_screener}?${queryParams}`);
            setStocks(res.data.stocks || []);
        } catch (err) {
            console.error('Screener fetch failed:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchScreener(PRESETS[0].params); }, []);

    const handlePreset = (idx: number) => {
        setActivePreset(idx);
        const p = PRESETS[idx].params;
        if ('sort_by' in p) setSortBy(p.sort_by!);
        if ('sort_order' in p) setSortOrder(p.sort_order!);
        fetchScreener(p);
    };

    const handleSort = (field: string) => {
        const newOrder = sortBy === field && sortOrder === 'desc' ? 'asc' : 'desc';
        setSortBy(field);
        setSortOrder(newOrder);
        fetchScreener({ ...PRESETS[activePreset].params, sort_by: field, sort_order: newOrder });
    };

    const getRsiColor = (rsi: number) => {
        if (rsi >= 70) return '#ef4444';
        if (rsi <= 30) return '#22c55e';
        return 'var(--text-primary)';
    };

    const getRsiLabel = (rsi: number) => {
        if (rsi >= 70) return 'Overbought';
        if (rsi <= 30) return 'Oversold';
        if (rsi >= 60) return 'Bullish';
        if (rsi <= 40) return 'Bearish';
        return 'Neutral';
    };

    return (
        <div>
            {/* Header */}
            <div style={{ marginBottom: '24px' }}>
                <h1 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
                    📊 Stock Screener
                </h1>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    Filter and sort NSE stocks by technical indicators
                </p>
            </div>

            {/* Preset Filters */}
            <div className="glass-card-static" style={{ padding: '12px 16px', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <Filter size={14} style={{ color: 'var(--accent-indigo)' }} />
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginRight: '4px' }}>Presets:</span>
                    {PRESETS.map((preset, i) => (
                        <button
                            key={i}
                            className={`btn ${activePreset === i ? 'btn-primary' : 'btn-ghost'}`}
                            style={{ padding: '4px 12px', fontSize: '0.73rem' }}
                            onClick={() => handlePreset(i)}
                        >
                            {preset.label}
                        </button>
                    ))}
                    <button
                        className="btn btn-ghost"
                        style={{ padding: '4px 10px', marginLeft: 'auto' }}
                        onClick={() => fetchScreener(PRESETS[activePreset].params)}
                        disabled={loading}
                    >
                        <RefreshCw size={14} className={loading ? 'spin' : ''} />
                    </button>
                </div>
            </div>

            {/* Results Table */}
            <div className="glass-card-static" style={{ padding: '0', overflow: 'hidden' }}>
                {loading ? (
                    <div style={{ padding: '60px', textAlign: 'center' }}>
                        <div className="loading-spinner" style={{ margin: '0 auto 16px' }} />
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>Scanning {30} stocks...</p>
                    </div>
                ) : (
                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '800px' }}>
                            <thead>
                                <tr style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)' }}>
                                    {[
                                        { key: 'symbol', label: 'Symbol' },
                                        { key: 'price', label: 'Price' },
                                        { key: 'change_pct', label: 'Change %' },
                                        { key: 'rsi', label: 'RSI (14)' },
                                        { key: 'volume_ratio', label: 'Vol Ratio' },
                                        { key: 'high_52w', label: '52W High' },
                                        { key: 'low_52w', label: '52W Low' },
                                        { key: 'from_52w_high', label: 'From 52W H' },
                                        { key: 'market_cap_cr', label: 'MCap (Cr)' },
                                    ].map(col => (
                                        <th
                                            key={col.key}
                                            style={{
                                                padding: '10px 14px', fontSize: '0.68rem', fontWeight: 600,
                                                color: sortBy === col.key ? 'var(--accent-indigo)' : 'var(--text-muted)',
                                                textAlign: col.key === 'symbol' ? 'left' : 'center',
                                                textTransform: 'uppercase', letterSpacing: '0.05em',
                                                cursor: 'pointer', userSelect: 'none',
                                            }}
                                            onClick={() => handleSort(col.key)}
                                        >
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', justifyContent: col.key === 'symbol' ? 'flex-start' : 'center' }}>
                                                {col.label}
                                                {sortBy === col.key && <ArrowUpDown size={10} />}
                                            </div>
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {stocks.map((s) => (
                                    <tr
                                        key={s.symbol}
                                        style={{
                                            borderBottom: '1px solid var(--border-subtle)',
                                            transition: 'background 0.15s',
                                            cursor: 'pointer',
                                        }}
                                        onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(99,102,241,0.04)')}
                                        onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                                    >
                                        <td style={{ padding: '10px 14px', fontWeight: 600, fontSize: '0.82rem', color: 'var(--text-primary)' }}>
                                            {s.symbol}
                                        </td>
                                        <td style={{ padding: '10px 14px', textAlign: 'center', fontSize: '0.82rem', fontFamily: 'monospace' }}>
                                            ₹{s.price.toLocaleString()}
                                        </td>
                                        <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                                            <span style={{
                                                display: 'inline-flex', alignItems: 'center', gap: '3px',
                                                color: s.change_pct >= 0 ? '#22c55e' : '#ef4444',
                                                fontWeight: 600, fontSize: '0.82rem',
                                            }}>
                                                {s.change_pct >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                                                {s.change_pct >= 0 ? '+' : ''}{s.change_pct}%
                                            </span>
                                        </td>
                                        <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
                                                <span style={{ fontWeight: 600, color: getRsiColor(s.rsi), fontSize: '0.85rem', fontFamily: 'monospace' }}>
                                                    {s.rsi}
                                                </span>
                                                <span style={{ fontSize: '0.6rem', color: getRsiColor(s.rsi), opacity: 0.8 }}>{getRsiLabel(s.rsi)}</span>
                                            </div>
                                        </td>
                                        <td style={{ padding: '10px 14px', textAlign: 'center', fontFamily: 'monospace', fontSize: '0.82rem' }}>
                                            <span style={{ color: s.volume_ratio > 1.5 ? '#f59e0b' : 'var(--text-muted)' }}>
                                                {s.volume_ratio}x
                                            </span>
                                        </td>
                                        <td style={{ padding: '10px 14px', textAlign: 'center', fontSize: '0.78rem', fontFamily: 'monospace' }}>
                                            ₹{s.high_52w.toLocaleString()}
                                        </td>
                                        <td style={{ padding: '10px 14px', textAlign: 'center', fontSize: '0.78rem', fontFamily: 'monospace' }}>
                                            ₹{s.low_52w.toLocaleString()}
                                        </td>
                                        <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                                            <span style={{
                                                fontSize: '0.78rem', fontFamily: 'monospace',
                                                color: s.from_52w_high > -5 ? '#22c55e' : s.from_52w_high < -20 ? '#ef4444' : 'var(--text-muted)',
                                            }}>
                                                {s.from_52w_high}%
                                            </span>
                                        </td>
                                        <td style={{ padding: '10px 14px', textAlign: 'center', fontSize: '0.78rem', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                                            {s.market_cap_cr ? `₹${Number(s.market_cap_cr).toLocaleString()}` : '—'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Footer stats */}
            {!loading && (
                <div style={{ marginTop: '12px', textAlign: 'center', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Showing {stocks.length} stocks from Nifty 30 universe
                </div>
            )}
        </div>
    );
};

export default ScreenerPage;
