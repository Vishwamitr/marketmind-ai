import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Target, RefreshCw } from 'lucide-react';
import {
    BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
    ResponsiveContainer, ReferenceLine
} from 'recharts';
import { endpoints } from '../config';

interface OptionEntry {
    strike: number;
    last_price: number;
    bid: number;
    ask: number;
    volume: number;
    open_interest: number;
    implied_volatility: number;
    in_the_money: boolean;
    change_pct: number;
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
}

interface OverviewEntry {
    symbol: string;
    name?: string;
    lot_size?: number;
    total_call_oi: number;
    total_put_oi: number;
    put_call_ratio: number;
    max_iv_pct: number;
    total_contracts: number;
    nearest_expiry: string;
    sentiment: string;
}

const OptionsPage: React.FC = () => {
    const [overview, setOverview] = useState<OverviewEntry[]>([]);
    const [isStatic, setIsStatic] = useState(false);
    const [symbol, setSymbol] = useState('');
    const [expiries, setExpiries] = useState<string[]>([]);
    const [selectedExpiry, setSelectedExpiry] = useState('');
    const [calls, setCalls] = useState<OptionEntry[]>([]);
    const [puts, setPuts] = useState<OptionEntry[]>([]);
    const [pcr, setPcr] = useState(0);
    const [maxPain, setMaxPain] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);
    const [, setChainLoading] = useState(false);
    const [ivSmileData, setIvSmileData] = useState<{ calls: { strike: number; iv: number }[]; puts: { strike: number; iv: number }[]; atm_strike: number; atm_iv: number; skew: number } | null>(null);

    useEffect(() => { fetchOverview(); }, []);

    const fetchIvSmile = async (sym: string) => {
        try {
            const res = await axios.get(endpoints.options_iv_smile(sym));
            setIvSmileData(res.data);
        } catch { setIvSmileData(null); }
    };

    const fetchOverview = async () => {
        setLoading(true);
        try {
            const res = await axios.get(endpoints.options_overview);
            setOverview(res.data.overview || []);
            setIsStatic(res.data.static || false);
        } catch (err) {
            console.error('Failed to fetch options overview', err);
        } finally {
            setLoading(false);
        }
    };

    const fetchChain = async (sym: string, expiry?: string) => {
        setChainLoading(true);
        setSymbol(sym);
        try {
            // Fetch expiries
            const expRes = await axios.get(endpoints.options_expiries(sym));
            const exps = expRes.data.expiries || [];
            setExpiries(exps);

            const selectedExp = expiry || exps[0] || '';
            setSelectedExpiry(selectedExp);

            // Fetch chain
            const chainRes = await axios.get(endpoints.options_chain(sym), { params: { expiry: selectedExp } });
            setCalls(chainRes.data.calls || []);
            setPuts(chainRes.data.puts || []);
            setPcr(chainRes.data.pcr || 0);

            // Fetch max pain
            try {
                const mpRes = await axios.get(endpoints.options_max_pain(sym), { params: { expiry: selectedExp } });
                setMaxPain(mpRes.data.max_pain_strike || null);
            } catch { setMaxPain(null); }

            // Fetch IV Smile
            fetchIvSmile(sym);
        } catch {
            setCalls([]); setPuts([]); setPcr(0); setMaxPain(null);
        }
        setChainLoading(false);
    };

    const getSentimentBadge = (sentiment: string) => {
        switch (sentiment) {
            case 'Bullish': return <span className="badge badge-bullish">🟢 Bullish</span>;
            case 'Bearish': return <span className="badge badge-bearish">🔴 Bearish</span>;
            default: return <span className="badge badge-sideways">🟡 Neutral</span>;
        }
    };

    // Prepare OI chart data
    const oiChartData = calls.map((c, i) => ({
        strike: c.strike,
        call_oi: c.open_interest,
        put_oi: puts[i]?.open_interest || 0,
    })).filter(d => d.call_oi > 0 || d.put_oi > 0);

    return (
        <div className="animate-fade-in">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1>🎯 Options Chain</h1>
                    <p>F&O data with OI analysis, Put-Call Ratio, and Max Pain</p>
                </div>
                <button className="btn btn-ghost" onClick={fetchOverview} disabled={loading}>
                    <RefreshCw size={14} /> Refresh
                </button>
            </div>

            {/* Overview Table */}
            <div className="glass-card-static" style={{ padding: '0', overflow: 'hidden', marginBottom: '24px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                            <th style={thStyle}>Symbol</th>
                            {isStatic ? (
                                <>
                                    <th style={{ ...thStyle, textAlign: 'left' }}>Name</th>
                                    <th style={{ ...thStyle, textAlign: 'center' }}>Lot Size</th>
                                </>
                            ) : (
                                <>
                                    <th style={{ ...thStyle, textAlign: 'right' }}>Call OI</th>
                                    <th style={{ ...thStyle, textAlign: 'right' }}>Put OI</th>
                                    <th style={{ ...thStyle, textAlign: 'center' }}>PCR</th>
                                    <th style={{ ...thStyle, textAlign: 'center' }}>Max IV</th>
                                    <th style={{ ...thStyle, textAlign: 'center' }}>Sentiment</th>
                                    <th style={{ ...thStyle, textAlign: 'right' }}>Nearest Expiry</th>
                                </>
                            )}
                            <th style={{ ...thStyle, textAlign: 'center' }}>Analyze</th>
                        </tr>
                    </thead>
                    <tbody>
                        {overview.map((ov) => (
                            <tr key={ov.symbol} style={{
                                borderBottom: '1px solid var(--border-subtle)',
                                background: symbol === ov.symbol ? 'rgba(99,102,241,0.08)' : 'transparent',
                                cursor: 'pointer',
                            }}
                                onClick={() => fetchChain(ov.symbol)}
                            >
                                <td style={{ ...tdStyle, fontWeight: 700 }}>{ov.symbol}</td>
                                {isStatic ? (
                                    <>
                                        <td style={{ ...tdStyle, fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{ov.name || ov.symbol}</td>
                                        <td style={{ ...tdStyle, textAlign: 'center', fontFamily: 'monospace' }}>{ov.lot_size || '—'}</td>
                                    </>
                                ) : (
                                    <>
                                        <td style={{ ...tdStyle, textAlign: 'right', fontFamily: 'monospace', color: 'var(--accent-green)' }}>
                                            {ov.total_call_oi.toLocaleString()}
                                        </td>
                                        <td style={{ ...tdStyle, textAlign: 'right', fontFamily: 'monospace', color: 'var(--accent-red)' }}>
                                            {ov.total_put_oi.toLocaleString()}
                                        </td>
                                        <td style={{ ...tdStyle, textAlign: 'center', fontWeight: 600 }}>{ov.put_call_ratio}</td>
                                        <td style={{ ...tdStyle, textAlign: 'center' }}>{ov.max_iv_pct}%</td>
                                        <td style={{ ...tdStyle, textAlign: 'center' }}>{getSentimentBadge(ov.sentiment)}</td>
                                        <td style={{ ...tdStyle, textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            {ov.nearest_expiry}
                                        </td>
                                    </>
                                )}
                                <td style={{ ...tdStyle, textAlign: 'center' }}>
                                    <button className="btn btn-ghost" style={{ padding: '4px 10px', fontSize: '0.7rem' }}>
                                        ⛓️ Chain
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Chain Detail */}
            {symbol && (calls.length > 0 || puts.length > 0) && (
                <div className="animate-fade-in">
                    {/* Stats Row */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                        <div className="glass-card-static" style={{ padding: '16px', textAlign: 'center' }}>
                            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>Put-Call Ratio</div>
                            <div style={{
                                fontSize: '1.5rem', fontWeight: 700,
                                color: pcr > 1.2 ? 'var(--accent-red)' : pcr < 0.8 ? 'var(--accent-green)' : 'var(--accent-amber)',
                            }}>{pcr.toFixed(3)}</div>
                        </div>
                        {maxPain && (
                            <div className="glass-card-static" style={{ padding: '16px', textAlign: 'center' }}>
                                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>Max Pain</div>
                                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-indigo)' }}>₹{maxPain.toLocaleString()}</div>
                            </div>
                        )}
                        <div className="glass-card-static" style={{ padding: '16px', textAlign: 'center' }}>
                            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>Total Calls</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-green)' }}>{calls.length}</div>
                        </div>
                        <div className="glass-card-static" style={{ padding: '16px', textAlign: 'center' }}>
                            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>Total Puts</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-red)' }}>{puts.length}</div>
                        </div>
                    </div>

                    {/* Expiry Selector */}
                    {expiries.length > 1 && (
                        <div className="glass-card-static" style={{ padding: '12px 16px', marginBottom: '16px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Expiry:</span>
                                {expiries.map(exp => (
                                    <button
                                        key={exp}
                                        className={`btn ${selectedExpiry === exp ? 'btn-primary' : 'btn-ghost'}`}
                                        style={{ padding: '4px 12px', fontSize: '0.75rem' }}
                                        onClick={() => { setSelectedExpiry(exp); fetchChain(symbol, exp); }}
                                    >
                                        {exp}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* OI Chart */}
                    {oiChartData.length > 0 && (
                        <div className="glass-card-static" style={{ padding: '20px', marginBottom: '24px' }}>
                            <h3 style={{ margin: '0 0 16px', fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                                Open Interest by Strike — {symbol}
                            </h3>
                            <div style={{ height: '300px' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={oiChartData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="strike" />
                                        <YAxis />
                                        <Tooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '10px' }} />
                                        <Legend />
                                        {maxPain && <ReferenceLine x={maxPain} stroke="#6366f1" strokeDasharray="5 5" label={{ value: 'Max Pain', fill: '#6366f1', fontSize: 11 }} />}
                                        <Bar dataKey="call_oi" name="Call OI" fill="#10b981" radius={[2, 2, 0, 0]} />
                                        <Bar dataKey="put_oi" name="Put OI" fill="#ef4444" radius={[2, 2, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}

                    {/* IV Smile/Skew Chart */}
                    {ivSmileData && (ivSmileData.calls.length > 0 || ivSmileData.puts.length > 0) && (
                        <div className="glass-card-static" style={{ padding: '20px', marginBottom: '24px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                                <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                                    📈 IV Smile / Skew — {symbol}
                                </h3>
                                <div style={{ display: 'flex', gap: 16, fontSize: '0.78rem' }}>
                                    <span style={{ color: 'var(--text-muted)' }}>ATM IV: <strong style={{ color: 'var(--accent-indigo)' }}>{ivSmileData.atm_iv}%</strong></span>
                                    <span style={{ color: 'var(--text-muted)' }}>Skew: <strong style={{ color: ivSmileData.skew > 0 ? 'var(--accent-red)' : 'var(--accent-green)' }}>{ivSmileData.skew > 0 ? '+' : ''}{ivSmileData.skew}%</strong></span>
                                </div>
                            </div>
                            <div style={{ height: '280px' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={[
                                        ...ivSmileData.calls.map(c => ({ strike: c.strike, call_iv: c.iv })),
                                    ].reduce((acc, item) => {
                                        const existing = acc.find(a => a.strike === item.strike);
                                        if (existing) Object.assign(existing, item);
                                        else {
                                            const putMatch = ivSmileData.puts.find(p => p.strike === item.strike);
                                            acc.push({ ...item, put_iv: putMatch?.iv });
                                        }
                                        return acc;
                                    }, ivSmileData.puts.map(p => ({ strike: p.strike, put_iv: p.iv } as Record<string, number | undefined>))).sort((a, b) => (a.strike || 0) - (b.strike || 0))}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                                        <XAxis dataKey="strike" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                                        <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} tickFormatter={(v: number) => `${v}%`} />
                                        <Tooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 10 }} formatter={(v: number | undefined) => [`${v ?? 0}%`]} />
                                        <Legend />
                                        {ivSmileData.atm_strike > 0 && <ReferenceLine x={ivSmileData.atm_strike} stroke="#6366f1" strokeDasharray="5 5" label={{ value: 'ATM', fill: '#6366f1', fontSize: 11 }} />}
                                        <Line type="monotone" dataKey="call_iv" name="Call IV" stroke="#10b981" strokeWidth={2} dot={{ r: 2 }} connectNulls />
                                        <Line type="monotone" dataKey="put_iv" name="Put IV" stroke="#ef4444" strokeWidth={2} dot={{ r: 2 }} connectNulls />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}

                    {/* Calls & Puts Tables Side by Side */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                        {/* Calls */}
                        <div className="glass-card-static" style={{ padding: '0', overflow: 'hidden' }}>
                            <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)', background: 'rgba(16,185,129,0.06)' }}>
                                <h3 style={{ margin: 0, fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-green)' }}>📗 CALLS</h3>
                            </div>
                            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                    <thead>
                                        <tr style={{ borderBottom: '1px solid var(--border-subtle)', position: 'sticky', top: 0, background: 'var(--bg-primary)' }}>
                                            <th style={thSmall}>Strike</th>
                                            <th style={thSmall}>LTP</th>
                                            <th style={thSmall}>OI</th>
                                            <th style={thSmall}>IV%</th>
                                            <th style={thSmall}>Δ</th>
                                            <th style={thSmall}>Γ</th>
                                            <th style={thSmall}>Θ</th>
                                            <th style={thSmall}>ν</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {calls.map((c, i) => (
                                            <tr key={i} style={{
                                                borderBottom: '1px solid var(--border-subtle)',
                                                background: c.in_the_money ? 'rgba(16,185,129,0.04)' : 'transparent',
                                            }}>
                                                <td style={{ ...tdSmall, fontWeight: 600 }}>{c.strike}</td>
                                                <td style={tdSmall}>₹{c.last_price?.toFixed(2) || '—'}</td>
                                                <td style={{ ...tdSmall, fontFamily: 'monospace' }}>{c.open_interest.toLocaleString()}</td>
                                                <td style={tdSmall}>{c.implied_volatility}%</td>
                                                <td style={{ ...tdSmall, fontFamily: 'monospace', color: (c.delta || 0) > 0.5 ? '#22c55e' : 'var(--text-muted)' }}>{c.delta?.toFixed(2) || '—'}</td>
                                                <td style={{ ...tdSmall, fontFamily: 'monospace', fontSize: '0.7rem' }}>{c.gamma?.toFixed(4) || '—'}</td>
                                                <td style={{ ...tdSmall, fontFamily: 'monospace', color: '#ef4444' }}>{c.theta?.toFixed(2) || '—'}</td>
                                                <td style={{ ...tdSmall, fontFamily: 'monospace' }}>{c.vega?.toFixed(2) || '—'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Puts */}
                        <div className="glass-card-static" style={{ padding: '0', overflow: 'hidden' }}>
                            <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)', background: 'rgba(239,68,68,0.06)' }}>
                                <h3 style={{ margin: 0, fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-red)' }}>📕 PUTS</h3>
                            </div>
                            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                    <thead>
                                        <tr style={{ borderBottom: '1px solid var(--border-subtle)', position: 'sticky', top: 0, background: 'var(--bg-primary)' }}>
                                            <th style={thSmall}>Strike</th>
                                            <th style={thSmall}>LTP</th>
                                            <th style={thSmall}>OI</th>
                                            <th style={thSmall}>IV%</th>
                                            <th style={thSmall}>Δ</th>
                                            <th style={thSmall}>Γ</th>
                                            <th style={thSmall}>Θ</th>
                                            <th style={thSmall}>ν</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {puts.map((p, i) => (
                                            <tr key={i} style={{
                                                borderBottom: '1px solid var(--border-subtle)',
                                                background: p.in_the_money ? 'rgba(239,68,68,0.04)' : 'transparent',
                                            }}>
                                                <td style={{ ...tdSmall, fontWeight: 600 }}>{p.strike}</td>
                                                <td style={tdSmall}>₹{p.last_price?.toFixed(2) || '—'}</td>
                                                <td style={{ ...tdSmall, fontFamily: 'monospace' }}>{p.open_interest.toLocaleString()}</td>
                                                <td style={tdSmall}>{p.implied_volatility}%</td>
                                                <td style={{ ...tdSmall, fontFamily: 'monospace', color: '#ef4444' }}>{p.delta?.toFixed(2) || '—'}</td>
                                                <td style={{ ...tdSmall, fontFamily: 'monospace', fontSize: '0.7rem' }}>{p.gamma?.toFixed(4) || '—'}</td>
                                                <td style={{ ...tdSmall, fontFamily: 'monospace', color: '#ef4444' }}>{p.theta?.toFixed(2) || '—'}</td>
                                                <td style={{ ...tdSmall, fontFamily: 'monospace' }}>{p.vega?.toFixed(2) || '—'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Search & Empty State */}
            {!loading && overview.length === 0 && !symbol && (
                <div className="glass-card-static" style={{ padding: '40px', textAlign: 'center' }}>
                    <Target size={48} style={{ color: 'var(--accent-indigo)', opacity: 0.3, marginBottom: '16px' }} />
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
                        Search for any F&O stock to view its live options chain
                    </p>
                    <form onSubmit={(e) => { e.preventDefault(); const input = (e.target as HTMLFormElement).elements.namedItem('sym') as HTMLInputElement; if (input.value.trim()) fetchChain(input.value.trim().toUpperCase()); }}
                        style={{ display: 'flex', gap: '10px', justifyContent: 'center', maxWidth: '400px', margin: '0 auto' }}
                    >
                        <input name="sym" className="input" placeholder="e.g. RELIANCE, NIFTY, BANKNIFTY..." style={{ flex: 1, textAlign: 'center' }} />
                        <button type="submit" className="btn btn-primary">⛓️ Analyze</button>
                    </form>
                    <div style={{ marginTop: '16px', display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
                        {['RELIANCE', 'TCS', 'HDFCBANK', 'NIFTY', 'BANKNIFTY', 'INFY'].map(s => (
                            <button key={s} className="btn btn-ghost" style={{ padding: '4px 12px', fontSize: '0.75rem' }} onClick={() => fetchChain(s)}>
                                {s}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

const thStyle: React.CSSProperties = {
    padding: '12px 16px', fontSize: '0.7rem', fontWeight: 600,
    color: 'var(--text-muted)', textAlign: 'left', textTransform: 'uppercase',
    letterSpacing: '0.05em',
};
const tdStyle: React.CSSProperties = {
    padding: '10px 16px', fontSize: '0.82rem', color: 'var(--text-primary)',
};
const thSmall: React.CSSProperties = {
    padding: '8px 10px', fontSize: '0.65rem', fontWeight: 600,
    color: 'var(--text-muted)', textAlign: 'center', textTransform: 'uppercase',
};
const tdSmall: React.CSSProperties = {
    padding: '6px 10px', fontSize: '0.78rem', color: 'var(--text-primary)', textAlign: 'center',
};

export default OptionsPage;
