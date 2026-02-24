import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Calendar, ChevronLeft, ChevronRight, TrendingUp } from 'lucide-react';
import { endpoints } from '../config';

interface Earning {
    symbol: string;
    company: string;
    date: string;
    eps_estimate: number | null;
    market_cap: number | null;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const EarningsPage: React.FC = () => {
    const [earnings, setEarnings] = useState<Earning[]>([]);
    const [loading, setLoading] = useState(true);
    const [view, setView] = useState<'list' | 'calendar'>('list');
    const [today] = useState(new Date());
    const [month, setMonth] = useState(today.getMonth());
    const [year, setYear] = useState(today.getFullYear());
    const navigate = useNavigate();

    useEffect(() => {
        const fetch = async () => {
            setLoading(true);
            try {
                const res = await axios.get(endpoints.earnings);
                setEarnings(res.data.earnings || []);
            } catch { setEarnings([]); }
            setLoading(false);
        };
        fetch();
    }, []);

    const byDate: Record<string, Earning[]> = {};
    earnings.forEach(e => {
        if (!byDate[e.date]) byDate[e.date] = [];
        byDate[e.date].push(e);
    });

    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const firstDay = new Date(year, month, 1).getDay();

    const fmt = (n: number) => n >= 1e9 ? `₹${(n / 1e9).toFixed(1)}B` : n >= 1e7 ? `₹${(n / 1e7).toFixed(0)}Cr` : '—';

    return (
        <div className="animate-fade-in" style={{ padding: '24px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                        🗓️ Earnings Calendar
                    </h1>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '4px 0 0' }}>
                        Upcoming NSE result announcements — next 90 days
                    </p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                    {(['list', 'calendar'] as const).map(v => (
                        <button key={v} onClick={() => setView(v)} style={{
                            padding: '8px 16px', borderRadius: 8, border: '1px solid',
                            borderColor: view === v ? 'var(--accent-indigo)' : 'var(--border-subtle)',
                            background: view === v ? 'rgba(99,102,241,0.15)' : 'transparent',
                            color: view === v ? 'var(--accent-indigo)' : 'var(--text-muted)',
                            cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600, textTransform: 'capitalize',
                        }}>{v}</button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div className="shimmer" style={{ height: 300, borderRadius: 14 }} />
            ) : earnings.length === 0 ? (
                <div className="glass-card-static" style={{ padding: 40, textAlign: 'center' }}>
                    <Calendar size={40} style={{ opacity: 0.3, margin: '0 auto 12px' }} />
                    <p style={{ color: 'var(--text-muted)' }}>No upcoming earnings data available from yfinance at this time.</p>
                </div>
            ) : view === 'list' ? (
                <div className="glass-card-static" style={{ overflow: 'hidden' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                                {['Date', 'Symbol', 'Company', 'EPS Est.', 'Market Cap'].map(h => (
                                    <th key={h} style={{
                                        padding: '12px 16px', textAlign: 'left', fontSize: '0.75rem',
                                        fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em'
                                    }}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {earnings.map((e, i) => {
                                const isToday = e.date === today.toISOString().slice(0, 10);
                                return (
                                    <tr key={i} onClick={() => navigate(`/analysis/${e.symbol}`)}
                                        style={{
                                            borderBottom: '1px solid var(--border-subtle)', cursor: 'pointer',
                                            background: isToday ? 'rgba(99,102,241,0.06)' : 'transparent'
                                        }}>
                                        <td style={{ padding: '12px 16px', fontSize: '0.85rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                                            {e.date}
                                            {isToday && <span style={{ marginLeft: 8, fontSize: '0.65rem', background: '#6366f1', color: '#fff', padding: '2px 6px', borderRadius: 4, fontWeight: 700 }}>TODAY</span>}
                                        </td>
                                        <td style={{ padding: '12px 16px' }}>
                                            <span style={{ fontWeight: 700, color: 'var(--accent-indigo)', fontSize: '0.85rem' }}>{e.symbol}</span>
                                        </td>
                                        <td style={{ padding: '12px 16px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{e.company}</td>
                                        <td style={{ padding: '12px 16px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                            {e.eps_estimate != null ? `₹${e.eps_estimate.toFixed(2)}` : '—'}
                                        </td>
                                        <td style={{ padding: '12px 16px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{fmt(e.market_cap ?? 0)}</td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            ) : (
                // Calendar View
                <div className="glass-card-static" style={{ padding: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
                        <button onClick={() => { if (month === 0) { setMonth(11); setYear(y => y - 1); } else setMonth(m => m - 1); }}
                            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}><ChevronLeft /></button>
                        <h3 style={{ margin: 0, fontWeight: 700, color: 'var(--text-primary)' }}>{MONTHS[month]} {year}</h3>
                        <button onClick={() => { if (month === 11) { setMonth(0); setYear(y => y + 1); } else setMonth(m => m + 1); }}
                            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}><ChevronRight /></button>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 4, marginBottom: 8 }}>
                        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
                            <div key={d} style={{ textAlign: 'center', fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', padding: '4px 0' }}>{d}</div>
                        ))}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 4 }}>
                        {Array(firstDay).fill(null).map((_, i) => <div key={`e${i}`} />)}
                        {Array(daysInMonth).fill(null).map((_, i) => {
                            const d = i + 1;
                            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
                            const dayEarnings = byDate[dateStr] || [];
                            const isT = dateStr === today.toISOString().slice(0, 10);
                            return (
                                <div key={d} style={{
                                    minHeight: 64, padding: 6, borderRadius: 8,
                                    background: isT ? 'rgba(99,102,241,0.12)' : dayEarnings.length ? 'rgba(16,185,129,0.06)' : 'rgba(255,255,255,0.02)',
                                    border: isT ? '1px solid var(--accent-indigo)' : '1px solid var(--border-subtle)',
                                }}>
                                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: isT ? 'var(--accent-indigo)' : 'var(--text-muted)', marginBottom: 4 }}>{d}</div>
                                    {dayEarnings.map((e, ei) => (
                                        <div key={ei} onClick={() => navigate(`/analysis/${e.symbol}`)}
                                            style={{
                                                fontSize: '0.6rem', background: 'rgba(16,185,129,0.2)', color: '#10b981',
                                                borderRadius: 3, padding: '1px 4px', marginBottom: 2, cursor: 'pointer', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 2
                                            }}>
                                            <TrendingUp size={8} />{e.symbol}
                                        </div>
                                    ))}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default EarningsPage;
