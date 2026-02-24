import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { RefreshCw, TrendingUp, TrendingDown, Zap } from 'lucide-react';
import { endpoints } from '../config';

interface Flow {
    symbol: string;
    expiry: string;
    type: 'CALL' | 'PUT';
    strike: number;
    ltp: number;
    volume: number;
    open_interest: number;
    vol_oi_ratio: number;
    iv: number;
    premium_value: number;
    flow_type: string;
    sentiment: 'bullish' | 'bearish';
}

const FlowScannerPage: React.FC = () => {
    const [flows, setFlows] = useState<Flow[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'bullish' | 'bearish'>('all');
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

    const fetch = async () => {
        setLoading(true);
        try {
            const res = await axios.get(endpoints.options_flow);
            setFlows(res.data.flows || []);
            setLastRefresh(new Date());
        } catch { setFlows([]); }
        setLoading(false);
    };

    useEffect(() => {
        fetch();
        const t = setInterval(fetch, 60000);
        return () => clearInterval(t);
    }, []);

    const visible = filter === 'all' ? flows : flows.filter(f => f.sentiment === filter);

    const fmt = (n: number) => n >= 1e7 ? `₹${(n / 1e7).toFixed(1)}Cr` : n >= 1e5 ? `₹${(n / 1e5).toFixed(0)}L` : `₹${n.toLocaleString()}`;

    const sentimentColor = (s: string) => s === 'bullish' ? '#10b981' : '#ef4444';
    const typeColor = (t: string) => t === 'CALL' ? '#10b981' : '#ef4444';

    return (
        <div className="animate-fade-in" style={{ padding: '24px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                        🌊 Options Flow Scanner
                    </h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '4px 0 0' }}>
                        Unusual options activity — Volume &gt; 5× Open Interest
                        {lastRefresh && <span style={{ marginLeft: 8 }}>· Last: {lastRefresh.toLocaleTimeString()}</span>}
                    </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {(['all', 'bullish', 'bearish'] as const).map(f => (
                        <button key={f} onClick={() => setFilter(f)} style={{
                            padding: '7px 14px', borderRadius: 8, border: '1px solid',
                            borderColor: filter === f ? (f === 'bullish' ? '#10b981' : f === 'bearish' ? '#ef4444' : 'var(--accent-indigo)') : 'var(--border-subtle)',
                            background: filter === f ? (f === 'bullish' ? 'rgba(16,185,129,0.12)' : f === 'bearish' ? 'rgba(239,68,68,0.12)' : 'rgba(99,102,241,0.12)') : 'transparent',
                            color: filter === f ? (f === 'bullish' ? '#10b981' : f === 'bearish' ? '#ef4444' : 'var(--accent-indigo)') : 'var(--text-muted)',
                            cursor: 'pointer', fontSize: '0.78rem', fontWeight: 600, textTransform: 'capitalize',
                        }}>
                            {f === 'bullish' ? '🟢' : f === 'bearish' ? '🔴' : '⚡'} {f}
                        </button>
                    ))}
                    <button onClick={fetch} disabled={loading} style={{
                        padding: '7px 14px', borderRadius: 8, border: '1px solid var(--border-subtle)',
                        background: 'transparent', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.78rem',
                    }}>
                        <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
                    </button>
                </div>
            </div>

            {/* Summary cards */}
            <div className="grid-metrics" style={{ marginBottom: 20 }}>
                {[
                    { label: 'Total Unusual Flows', value: flows.length, icon: <Zap size={18} />, color: 'var(--accent-indigo)' },
                    { label: 'Bullish Signals', value: flows.filter(f => f.sentiment === 'bullish').length, icon: <TrendingUp size={18} />, color: '#10b981' },
                    { label: 'Bearish Signals', value: flows.filter(f => f.sentiment === 'bearish').length, icon: <TrendingDown size={18} />, color: '#ef4444' },
                    { label: 'Total Premium', value: fmt(flows.reduce((s, f) => s + f.premium_value, 0)), icon: <Zap size={18} />, color: '#f59e0b' },
                ].map((card, i) => (
                    <div key={i} className="glass-card-static" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 14 }}>
                        <span style={{ color: card.color }}>{card.icon}</span>
                        <div>
                            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: card.color }}>{card.value}</div>
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{card.label}</div>
                        </div>
                    </div>
                ))}
            </div>

            {loading && flows.length === 0 ? (
                <div className="shimmer" style={{ height: 300, borderRadius: 14 }} />
            ) : visible.length === 0 ? (
                <div className="glass-card-static" style={{ padding: 40, textAlign: 'center' }}>
                    <Zap size={40} style={{ opacity: 0.3, margin: '0 auto 12px' }} />
                    <p style={{ color: 'var(--text-muted)' }}>No unusual options activity detected. Try refreshing or check back later.</p>
                </div>
            ) : (
                <div className="glass-card-static" style={{ overflow: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 800 }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                                {['Symbol', 'Type', 'Strike', 'Expiry', 'LTP', 'Volume', 'OI', 'Vol/OI', 'IV', 'Premium', 'Flow Type'].map(h => (
                                    <th key={h} style={{ padding: '12px 14px', textAlign: 'left', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', whiteSpace: 'nowrap' }}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {visible.map((f, i) => (
                                <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)', transition: 'var(--transition)' }}>
                                    <td style={{ padding: '11px 14px', fontWeight: 700, color: 'var(--accent-indigo)', fontSize: '0.85rem' }}>{f.symbol}</td>
                                    <td style={{ padding: '11px 14px' }}>
                                        <span style={{ padding: '3px 8px', borderRadius: 6, fontSize: '0.7rem', fontWeight: 700, background: `${typeColor(f.type)}22`, color: typeColor(f.type) }}>{f.type}</span>
                                    </td>
                                    <td style={{ padding: '11px 14px', fontSize: '0.85rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>₹{f.strike.toLocaleString()}</td>
                                    <td style={{ padding: '11px 14px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>{f.expiry}</td>
                                    <td style={{ padding: '11px 14px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>₹{f.ltp}</td>
                                    <td style={{ padding: '11px 14px', fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 600 }}>{f.volume.toLocaleString()}</td>
                                    <td style={{ padding: '11px 14px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{f.open_interest.toLocaleString()}</td>
                                    <td style={{ padding: '11px 14px', fontSize: '0.85rem', fontWeight: 700, color: '#f59e0b' }}>{f.vol_oi_ratio}×</td>
                                    <td style={{ padding: '11px 14px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{f.iv}%</td>
                                    <td style={{ padding: '11px 14px', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{fmt(f.premium_value)}</td>
                                    <td style={{ padding: '11px 14px' }}>
                                        <span style={{
                                            padding: '3px 8px', borderRadius: 6, fontSize: '0.7rem', fontWeight: 600,
                                            background: `${sentimentColor(f.sentiment)}18`, color: sentimentColor(f.sentiment), whiteSpace: 'nowrap'
                                        }}>
                                            {f.sentiment === 'bullish' ? '🐂' : '🐻'} {f.flow_type}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
            <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 12, opacity: 0.6 }}>
                ⚠️ Options flow data is for informational purposes only. Not investment advice. Auto-refreshes every 60s.
            </p>
        </div>
    );
};

export default FlowScannerPage;
