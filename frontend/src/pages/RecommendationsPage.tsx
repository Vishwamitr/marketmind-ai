import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Brain, RefreshCw, TrendingUp, TrendingDown, Minus, AlertTriangle, Target, Shield, Crosshair } from 'lucide-react';
import { endpoints } from '../config';

interface Signal {
    type: string;
    signal: string;
    detail: string;
}

interface Recommendation {
    symbol: string;
    action: string;
    score: number;
    confidence: number;
    confidence_pct?: number;
    entry?: number;
    target?: number;
    stop_loss?: number;
    risk_reward?: number;
    signals: Signal[];
    signal_count: number;
    error?: string;
}

const RecommendationsPage: React.FC = () => {
    const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'ALL' | 'BUY' | 'SELL' | 'HOLD'>('ALL');

    useEffect(() => { fetchRecommendations(); }, []);

    const fetchRecommendations = async () => {
        setLoading(true);
        try {
            const res = await axios.get(endpoints.recommend_all);
            setRecommendations(res.data.recommendations || []);
        } catch (err) {
            console.error('Failed to fetch recommendations', err);
        } finally {
            setLoading(false);
        }
    };

    const filtered = filter === 'ALL' ? recommendations : recommendations.filter(r => r.action === filter);

    const getActionStyle = (action: string) => {
        switch (action) {
            case 'BUY': return { bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.3)', color: '#34d399', label: '🟢 BUY' };
            case 'SELL': return { bg: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.3)', color: '#f87171', label: '🔴 SELL' };
            case 'HOLD': return { bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.3)', color: '#fbbf24', label: '🟡 HOLD' };
            default: return { bg: 'rgba(255,255,255,0.05)', border: 'rgba(255,255,255,0.1)', color: '#94a3b8', label: `⚪ ${action}` };
        }
    };

    const getActionIcon = (action: string) => {
        switch (action) {
            case 'BUY': return <TrendingUp size={20} style={{ color: 'var(--accent-green)' }} />;
            case 'SELL': return <TrendingDown size={20} style={{ color: 'var(--accent-red)' }} />;
            case 'HOLD': return <Minus size={20} style={{ color: 'var(--accent-amber)' }} />;
            default: return <AlertTriangle size={20} style={{ color: 'var(--text-muted)' }} />;
        }
    };

    const getSignalTypeIcon = (type: string) => {
        switch (type) {
            case 'regime': return '🏛️';
            case 'technical': return '📊';
            case 'momentum': return '🚀';
            case 'volume': return '📈';
            case 'sentiment': return '💬';
            case 'risk': return '⚠️';
            default: return '•';
        }
    };

    const counts = {
        BUY: recommendations.filter(r => r.action === 'BUY').length,
        SELL: recommendations.filter(r => r.action === 'SELL').length,
        HOLD: recommendations.filter(r => r.action === 'HOLD').length,
    };

    return (
        <div className="animate-fade-in">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1>🧠 AI Trade Signals</h1>
                    <p>Data-driven signals with entry, target, stop-loss levels powered by regime detection, momentum, and sentiment</p>
                </div>
                <button className="btn btn-ghost" onClick={fetchRecommendations} disabled={loading}>
                    <RefreshCw size={14} /> Refresh
                </button>
            </div>

            {/* Summary Bar */}
            {!loading && recommendations.length > 0 && (
                <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
                    {(['ALL', 'BUY', 'SELL', 'HOLD'] as const).map(f => {
                        const isActive = filter === f;
                        const count = f === 'ALL' ? recommendations.length : counts[f];
                        const style = f === 'ALL' ? { bg: 'rgba(99,102,241,0.12)', border: 'rgba(99,102,241,0.3)', color: '#818cf8' } : getActionStyle(f);
                        return (
                            <button
                                key={f}
                                onClick={() => setFilter(f)}
                                style={{
                                    padding: '8px 20px', borderRadius: '10px', cursor: 'pointer', fontWeight: 600,
                                    fontSize: '0.8rem', fontFamily: 'inherit', display: 'flex', gap: '6px', alignItems: 'center',
                                    background: isActive ? style.bg : 'transparent',
                                    border: `1px solid ${isActive ? style.border : 'var(--border-subtle)'}`,
                                    color: isActive ? style.color : 'var(--text-muted)',
                                    transition: 'all 0.2s ease',
                                }}
                            >
                                {f} <span style={{ opacity: 0.7 }}>({count})</span>
                            </button>
                        );
                    })}
                </div>
            )}

            {loading ? (
                <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
                    <Brain size={48} className="animate-spin" style={{ opacity: 0.3, marginBottom: '16px' }} />
                    <p>Analyzing all stocks...</p>
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: '16px' }}>
                    {filtered.map((rec, i) => {
                        const style = getActionStyle(rec.action);
                        return (
                            <div
                                key={rec.symbol}
                                className="glass-card-static animate-fade-in"
                                style={{ padding: '24px', animationDelay: `${i * 60}ms`, borderLeft: `3px solid ${style.color}` }}
                            >
                                {/* Header */}
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        {getActionIcon(rec.action)}
                                        <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700 }}>{rec.symbol}</h3>
                                    </div>
                                    <span style={{
                                        fontSize: '0.85rem', padding: '5px 14px', borderRadius: '8px', fontWeight: 700,
                                        background: style.bg, color: style.color, border: `1px solid ${style.border}`,
                                    }}>
                                        {style.label}
                                    </span>
                                </div>

                                {/* Confidence Bar */}
                                <div style={{ marginBottom: '16px' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                                        <span>Confidence</span>
                                        <span style={{ fontWeight: 600, color: style.color }}>{rec.confidence_pct ?? (rec.confidence * 100).toFixed(0)}%</span>
                                    </div>
                                    <div style={{ height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,0.06)' }}>
                                        <div style={{
                                            height: '100%', borderRadius: '3px', transition: 'width 0.8s ease',
                                            width: `${rec.confidence * 100}%`,
                                            background: `linear-gradient(90deg, ${style.color}80, ${style.color})`,
                                        }} />
                                    </div>
                                </div>

                                {/* Price Levels */}
                                {rec.entry && (
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginBottom: '16px' }}>
                                        <div style={{ padding: '10px', borderRadius: '10px', textAlign: 'center', background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.15)' }}>
                                            <Crosshair size={14} style={{ color: '#60a5fa', marginBottom: '4px' }} />
                                            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#60a5fa', fontFamily: 'monospace' }}>₹{rec.entry?.toLocaleString('en-IN')}</div>
                                            <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginTop: '2px' }}>ENTRY</div>
                                        </div>
                                        <div style={{ padding: '10px', borderRadius: '10px', textAlign: 'center', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.15)' }}>
                                            <Target size={14} style={{ color: '#34d399', marginBottom: '4px' }} />
                                            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#34d399', fontFamily: 'monospace' }}>₹{rec.target?.toLocaleString('en-IN')}</div>
                                            <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginTop: '2px' }}>TARGET</div>
                                        </div>
                                        <div style={{ padding: '10px', borderRadius: '10px', textAlign: 'center', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.15)' }}>
                                            <Shield size={14} style={{ color: '#f87171', marginBottom: '4px' }} />
                                            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f87171', fontFamily: 'monospace' }}>₹{rec.stop_loss?.toLocaleString('en-IN')}</div>
                                            <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginTop: '2px' }}>STOP LOSS</div>
                                        </div>
                                    </div>
                                )}

                                {/* Score + Risk:Reward + Signals Count */}
                                <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                                    <div style={{ flex: 1, padding: '10px', borderRadius: '10px', textAlign: 'center', background: rec.score > 0 ? 'rgba(16,185,129,0.08)' : rec.score < 0 ? 'rgba(239,68,68,0.08)' : 'rgba(255,255,255,0.03)', border: `1px solid ${rec.score > 0 ? 'rgba(16,185,129,0.15)' : rec.score < 0 ? 'rgba(239,68,68,0.15)' : 'rgba(255,255,255,0.05)'}` }}>
                                        <div style={{ fontSize: '1rem', fontWeight: 700, color: rec.score > 0 ? 'var(--accent-green)' : rec.score < 0 ? 'var(--accent-red)' : 'var(--text-secondary)' }}>
                                            {rec.score > 0 ? '+' : ''}{rec.score.toFixed(3)}
                                        </div>
                                        <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>AI Score</div>
                                    </div>
                                    {rec.risk_reward && (
                                        <div style={{ flex: 1, padding: '10px', borderRadius: '10px', textAlign: 'center', background: 'rgba(168,85,247,0.08)', border: '1px solid rgba(168,85,247,0.15)' }}>
                                            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#c084fc' }}>1:{rec.risk_reward}</div>
                                            <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>Risk:Reward</div>
                                        </div>
                                    )}
                                    <div style={{ flex: 1, padding: '10px', borderRadius: '10px', textAlign: 'center', background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)' }}>
                                        <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--accent-indigo)' }}>{rec.signal_count}</div>
                                        <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>Signals</div>
                                    </div>
                                </div>

                                {/* Signal Details */}
                                <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
                                    {rec.signals.map((signal, j) => (
                                        <div key={j} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', padding: '5px 0', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                            <span style={{ flexShrink: 0 }}>{getSignalTypeIcon(signal.type)}</span>
                                            <span>{signal.detail}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {!loading && recommendations.length === 0 && (
                <div className="glass-card-static" style={{ padding: '60px', textAlign: 'center' }}>
                    <Brain size={48} style={{ color: 'var(--accent-indigo)', opacity: 0.3, marginBottom: '16px' }} />
                    <p style={{ color: 'var(--text-secondary)' }}>No recommendations available. Make sure stock data is loaded.</p>
                </div>
            )}
        </div>
    );
};

export default RecommendationsPage;
