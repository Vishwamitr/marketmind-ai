import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Trash2, TrendingUp, TrendingDown, BarChart2 } from 'lucide-react';
import { endpoints } from '../config';

interface Trade {
    id: number;
    symbol: string;
    direction: string;
    entry_price: number;
    exit_price: number;
    quantity: number;
    trade_date: string;
    strategy: string;
    notes: string;
    pnl_per_share: number;
    total_pnl: number;
    pnl_pct: number;
}

interface Stats {
    total_trades: number;
    win_rate: number;
    total_pnl: number;
    avg_pnl: number;
    best_trade: { symbol: string; pnl: number; date: string } | null;
    worst_trade: { symbol: string; pnl: number; date: string } | null;
}

const JournalPage: React.FC = () => {
    const [trades, setTrades] = useState<Trade[]>([]);
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState<'log' | 'stats'>('log');

    // Form state
    const [symbol, setSymbol] = useState('');
    const [direction, setDirection] = useState('LONG');
    const [entry, setEntry] = useState('');
    const [exit, setExit] = useState('');
    const [qty, setQty] = useState('1');
    const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
    const [strategy, setStrategy] = useState('');
    const [notes, setNotes] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const fetch = async () => {
        setLoading(true);
        try {
            const [tRes, sRes] = await Promise.all([
                axios.get(endpoints.journal),
                axios.get(endpoints.journal_stats),
            ]);
            setTrades(tRes.data.trades || []);
            setStats(sRes.data);
        } catch { /* ignore */ }
        setLoading(false);
    };

    useEffect(() => { fetch(); }, []);

    const submit = async () => {
        if (!symbol || !entry || !exit) return;
        setSubmitting(true);
        try {
            await axios.post(endpoints.journal, {
                symbol, direction, entry_price: parseFloat(entry), exit_price: parseFloat(exit),
                quantity: parseInt(qty) || 1, trade_date: date, strategy, notes,
            });
            setSymbol(''); setEntry(''); setExit(''); setQty('1'); setStrategy(''); setNotes('');
            await fetch();
        } catch { /* ignore */ }
        setSubmitting(false);
    };

    const del = async (id: number) => {
        try {
            await axios.delete(endpoints.journal_delete(id));
            await fetch();
        } catch { /* ignore */ }
    };

    const pclr = (v: number) => v >= 0 ? '#10b981' : '#ef4444';

    return (
        <div className="animate-fade-in" style={{ padding: '24px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>📔 Trade Journal</h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '4px 0 0' }}>
                        Log your trades and track performance over time
                    </p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                    {(['log', 'stats'] as const).map(v => (
                        <button key={v} onClick={() => setTab(v)} style={{
                            padding: '8px 18px', borderRadius: 8, border: '1px solid',
                            borderColor: tab === v ? 'var(--accent-indigo)' : 'var(--border-subtle)',
                            background: tab === v ? 'rgba(99,102,241,0.15)' : 'transparent',
                            color: tab === v ? 'var(--accent-indigo)' : 'var(--text-muted)',
                            cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600, textTransform: 'capitalize',
                        }}>{v === 'log' ? '📋 Trade Log' : '📊 Analytics'}</button>
                    ))}
                </div>
            </div>

            {/* Add Trade Form */}
            <div className="glass-card-static" style={{ padding: 20, marginBottom: 20 }}>
                <h3 style={{ margin: '0 0 16px', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>+ Log New Trade</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 10 }}>
                    {[
                        { label: 'Symbol', value: symbol, setter: setSymbol, placeholder: 'e.g. TCS' },
                        { label: 'Entry Price (₹)', value: entry, setter: setEntry, placeholder: '3400' },
                        { label: 'Exit Price (₹)', value: exit, setter: setExit, placeholder: '3500' },
                        { label: 'Qty', value: qty, setter: setQty, placeholder: '10' },
                        { label: 'Date', value: date, setter: setDate, placeholder: '' },
                        { label: 'Strategy', value: strategy, setter: setStrategy, placeholder: 'Breakout' },
                    ].map(({ label, value, setter, placeholder }) => (
                        <div key={label}>
                            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>{label}</label>
                            <input value={value} onChange={e => setter(e.target.value)} placeholder={placeholder}
                                type={label === 'Date' ? 'date' : 'text'}
                                style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '0.83rem', boxSizing: 'border-box' }} />
                        </div>
                    ))}
                </div>
                <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
                    <div style={{ flex: 1 }}>
                        <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Direction</label>
                        <select value={direction} onChange={e => setDirection(e.target.value)}
                            style={{ padding: '8px 10px', borderRadius: 8, border: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)', color: direction === 'LONG' ? '#10b981' : '#ef4444', fontSize: '0.83rem', fontWeight: 600 }}>
                            <option value="LONG">LONG</option>
                            <option value="SHORT">SHORT</option>
                        </select>
                    </div>
                    <div style={{ flex: 2 }}>
                        <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Notes</label>
                        <input value={notes} onChange={e => setNotes(e.target.value)} placeholder="What was your thesis?"
                            style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '0.83rem', boxSizing: 'border-box' }} />
                    </div>
                    <button onClick={submit} disabled={submitting || !symbol || !entry || !exit} style={{
                        padding: '9px 20px', borderRadius: 8, background: 'var(--gradient-primary)', border: 'none',
                        color: '#fff', cursor: 'pointer', fontWeight: 600, fontSize: '0.83rem', display: 'flex', alignItems: 'center', gap: 6,
                        opacity: (!symbol || !entry || !exit) ? 0.5 : 1,
                    }}>
                        <Plus size={15} /> Add Trade
                    </button>
                </div>
            </div>

            {tab === 'log' ? (
                loading ? (
                    <div className="shimmer" style={{ height: 300, borderRadius: 14 }} />
                ) : trades.length === 0 ? (
                    <div className="glass-card-static" style={{ padding: 40, textAlign: 'center' }}>
                        <BarChart2 size={40} style={{ opacity: 0.3, margin: '0 auto 12px' }} />
                        <p style={{ color: 'var(--text-muted)' }}>No trades logged yet. Add your first trade above!</p>
                    </div>
                ) : (
                    <div className="glass-card-static" style={{ overflow: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 750 }}>
                            <thead>
                                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                                    {['Date', 'Symbol', 'Dir', 'Entry', 'Exit', 'Qty', 'P&L/Share', 'Total P&L', 'P&L%', 'Strategy', 'Notes', ''].map(h => (
                                        <th key={h} style={{ padding: '11px 14px', textAlign: 'left', fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', whiteSpace: 'nowrap' }}>{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {trades.map(t => (
                                    <tr key={t.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                                        <td style={{ padding: '11px 14px', fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>{t.trade_date}</td>
                                        <td style={{ padding: '11px 14px', fontWeight: 700, color: 'var(--accent-indigo)', fontSize: '0.85rem' }}>{t.symbol}</td>
                                        <td style={{ padding: '11px 14px' }}>
                                            <span style={{
                                                fontSize: '0.72rem', fontWeight: 700, padding: '2px 8px', borderRadius: 6,
                                                background: t.direction === 'LONG' ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
                                                color: t.direction === 'LONG' ? '#10b981' : '#ef4444'
                                            }}>{t.direction}</span>
                                        </td>
                                        <td style={{ padding: '11px 14px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>₹{t.entry_price.toLocaleString()}</td>
                                        <td style={{ padding: '11px 14px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>₹{t.exit_price.toLocaleString()}</td>
                                        <td style={{ padding: '11px 14px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{t.quantity}</td>
                                        <td style={{ padding: '11px 14px', fontSize: '0.85rem', fontWeight: 600, color: pclr(t.pnl_per_share) }}>
                                            {t.pnl_per_share >= 0 ? '+' : ''}₹{t.pnl_per_share}
                                        </td>
                                        <td style={{ padding: '11px 14px', fontSize: '0.88rem', fontWeight: 700, color: pclr(t.total_pnl) }}>
                                            {t.total_pnl >= 0 ? <TrendingUp size={12} style={{ display: 'inline', marginRight: 3 }} /> : <TrendingDown size={12} style={{ display: 'inline', marginRight: 3 }} />}
                                            {t.total_pnl >= 0 ? '+' : ''}₹{t.total_pnl.toLocaleString()}
                                        </td>
                                        <td style={{ padding: '11px 14px', fontSize: '0.85rem', fontWeight: 600, color: pclr(t.pnl_pct) }}>
                                            {t.pnl_pct >= 0 ? '+' : ''}{t.pnl_pct}%
                                        </td>
                                        <td style={{ padding: '11px 14px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>{t.strategy || '—'}</td>
                                        <td style={{ padding: '11px 14px', fontSize: '0.8rem', color: 'var(--text-muted)', maxWidth: 150 }}>{t.notes || '—'}</td>
                                        <td style={{ padding: '11px 14px' }}>
                                            <button onClick={() => del(t.id)} style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 6, cursor: 'pointer', color: '#ef4444', padding: '4px 6px', display: 'flex', alignItems: 'center' }}>
                                                <Trash2 size={13} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )
            ) : (
                /* Stats Tab */
                stats && (
                    <div>
                        <div className="grid-metrics" style={{ marginBottom: 20 }}>
                            {[
                                { label: 'Total Trades', value: stats.total_trades, color: 'var(--accent-indigo)' },
                                { label: 'Win Rate', value: `${stats.win_rate}%`, color: stats.win_rate >= 50 ? '#10b981' : '#ef4444' },
                                { label: 'Total P&L', value: `${stats.total_pnl >= 0 ? '+' : ''}₹${stats.total_pnl.toLocaleString()}`, color: pclr(stats.total_pnl) },
                                { label: 'Avg P&L/Trade', value: `${stats.avg_pnl >= 0 ? '+' : ''}₹${stats.avg_pnl}`, color: pclr(stats.avg_pnl) },
                            ].map((c, i) => (
                                <div key={i} className="glass-card-static" style={{ padding: '20px 24px' }}>
                                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>{c.label}</div>
                                    <div style={{ fontSize: '1.6rem', fontWeight: 700, color: c.color }}>{c.value}</div>
                                </div>
                            ))}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                            {[
                                { label: '🏆 Best Trade', data: stats.best_trade, color: '#10b981' },
                                { label: '📉 Worst Trade', data: stats.worst_trade, color: '#ef4444' },
                            ].map(({ label, data, color }) => data && (
                                <div key={label} className="glass-card-static" style={{ padding: 20, borderLeft: `3px solid ${color}` }}>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 8 }}>{label}</div>
                                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color }}>{data.symbol}</div>
                                    <div style={{ fontSize: '1.3rem', fontWeight: 700, color }}>{data.pnl >= 0 ? '+' : ''}₹{data.pnl.toLocaleString()}</div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>{data.date}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )
            )}
        </div>
    );
};

export default JournalPage;
