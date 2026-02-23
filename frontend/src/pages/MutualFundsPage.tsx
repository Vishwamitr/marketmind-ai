import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Landmark, RefreshCw, Filter, Search } from 'lucide-react';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { endpoints } from '../config';

interface MFund {
    symbol: string;
    fund_name: string;
    nav: number;
    category: string;
    timestamp: string;
}

const MutualFundsPage: React.FC = () => {
    const [funds, setFunds] = useState<MFund[]>([]);
    const [categories, setCategories] = useState<string[]>([]);
    const [selectedCategory, setSelectedCategory] = useState('');
    const [selectedFund, setSelectedFund] = useState<string | null>(null);
    const [navHistory, setNavHistory] = useState<any[]>([]);
    const [returnPct, setReturnPct] = useState(0);
    const [loading, setLoading] = useState(true);
    const [historyLoading, setHistoryLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => { fetchFunds(); }, [selectedCategory]);

    // Debounced search: re-fetch when searchTerm changes (after 400ms)
    useEffect(() => {
        const timer = setTimeout(() => { fetchFunds(); }, 400);
        return () => clearTimeout(timer);
    }, [searchTerm]);

    const fetchFunds = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (selectedCategory) params.set('category', selectedCategory);
            if (searchTerm.trim()) params.set('search', searchTerm.trim());
            params.set('limit', '100');
            const qs = params.toString() ? `?${params.toString()}` : '';
            const res = await axios.get(`${endpoints.mf_list}${qs}`);
            setFunds(res.data.funds || []);
            setCategories(res.data.categories || []);
        } catch (err) {
            console.error('Failed to fetch MF list', err);
        } finally {
            setLoading(false);
        }
    };

    const fetchHistory = async (symbol: string) => {
        setSelectedFund(symbol);
        setHistoryLoading(true);
        try {
            const res = await axios.get(endpoints.mf_history(symbol));
            setNavHistory(res.data.history || []);
            setReturnPct(res.data.total_return_pct || 0);
        } catch (err) {
            console.error('Failed to fetch MF history', err);
        } finally {
            setHistoryLoading(false);
        }
    };

    const tooltipStyle = {
        contentStyle: { background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '10px' },
    };

    // funds already filtered server-side — use directly
    const filteredFunds = funds;

    return (
        <div className="animate-fade-in">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1>🏛️ Mutual Funds</h1>
                    <p>Track NAV, returns, and performance across fund categories</p>
                </div>
                <button className="btn btn-ghost" onClick={fetchFunds} disabled={loading}>
                    <RefreshCw size={14} /> Refresh
                </button>
            </div>

            {/* Search Bar */}
            <div className="glass-card-static" style={{ padding: '12px 20px', marginBottom: '16px', display: 'flex', gap: '12px', alignItems: 'center' }}>
                <Search size={18} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                <input
                    className="input"
                    style={{ flex: 1, background: 'transparent', border: 'none', padding: '4px 0' }}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search funds by name or symbol (e.g. Nifty, Gold, Bank...)"
                />
                {searchTerm && (
                    <button className="btn btn-ghost" style={{ padding: '4px 8px', fontSize: '0.75rem' }} onClick={() => setSearchTerm('')}>✕ Clear</button>
                )}
                {searchTerm && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', flexShrink: 0 }}>{filteredFunds.length} results</span>
                )}
            </div>

            {/* Category Filter */}
            <div className="glass-card-static" style={{ padding: '16px', marginBottom: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                    <Filter size={16} style={{ color: 'var(--text-muted)' }} />
                    <button
                        className={`btn ${!selectedCategory ? 'btn-primary' : 'btn-ghost'}`}
                        onClick={() => setSelectedCategory('')}
                        style={{ padding: '6px 14px', fontSize: '0.78rem' }}
                    >
                        All
                    </button>
                    {categories.map(cat => (
                        <button
                            key={cat}
                            className={`btn ${selectedCategory === cat ? 'btn-primary' : 'btn-ghost'}`}
                            onClick={() => setSelectedCategory(cat)}
                            style={{ padding: '6px 14px', fontSize: '0.78rem' }}
                        >
                            {cat}
                        </button>
                    ))}
                </div>
            </div>

            {/* NAV History Chart */}
            {selectedFund && navHistory.length > 0 && (
                <div className="glass-card-static animate-fade-in" style={{ padding: '20px', marginBottom: '24px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                        <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                            NAV History — {funds.find(f => f.symbol === selectedFund)?.fund_name || selectedFund}
                        </h3>
                        <span className={`badge ${returnPct >= 0 ? 'badge-bullish' : 'badge-bearish'}`}>
                            {returnPct >= 0 ? '▲' : '▼'} {returnPct.toFixed(2)}%
                        </span>
                    </div>
                    <div style={{ height: '280px' }}>
                        {historyLoading ? (
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
                                Loading chart...
                            </div>
                        ) : (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={navHistory}>
                                    <defs>
                                        <linearGradient id="navGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor={returnPct >= 0 ? '#10b981' : '#ef4444'} stopOpacity={0.2} />
                                            <stop offset="100%" stopColor={returnPct >= 0 ? '#10b981' : '#ef4444'} stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="timestamp" tickFormatter={(t) => new Date(t).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })} />
                                    <YAxis domain={['auto', 'auto']} />
                                    <Tooltip {...tooltipStyle} labelFormatter={(t) => new Date(t).toLocaleDateString('en-IN')} />
                                    <Area
                                        type="monotone" dataKey="nav"
                                        stroke={returnPct >= 0 ? '#10b981' : '#ef4444'}
                                        fill="url(#navGrad)" strokeWidth={2} name="NAV"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>
            )}

            {/* Funds Table */}
            <div className="glass-card-static" style={{ padding: '0', overflow: 'hidden' }}>
                <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                            <th style={thStyle}>Fund Name</th>
                            <th style={{ ...thStyle, textAlign: 'center' }}>Category</th>
                            <th style={{ ...thStyle, textAlign: 'right' }}>NAV (₹)</th>
                            <th style={{ ...thStyle, textAlign: 'right' }}>Updated</th>
                            <th style={{ ...thStyle, textAlign: 'center' }}>Chart</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredFunds.map((fund, i) => (
                            <tr key={fund.symbol} style={{
                                borderBottom: '1px solid var(--border-subtle)',
                                background: selectedFund === fund.symbol ? 'rgba(99,102,241,0.08)' : 'transparent',
                                animationDelay: `${i * 30}ms`,
                            }}>
                                <td style={tdStyle}>
                                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{fund.fund_name}</div>
                                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{fund.symbol}</div>
                                </td>
                                <td style={{ ...tdStyle, textAlign: 'center' }}>
                                    <span className="badge badge-sideways" style={{ fontSize: '0.7rem' }}>{fund.category}</span>
                                </td>
                                <td style={{ ...tdStyle, textAlign: 'right', fontWeight: 700, fontSize: '0.95rem', fontFamily: 'monospace' }}>
                                    ₹{fund.nav.toFixed(2)}
                                </td>
                                <td style={{ ...tdStyle, textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                    {new Date(fund.timestamp).toLocaleDateString('en-IN')}
                                </td>
                                <td style={{ ...tdStyle, textAlign: 'center' }}>
                                    <button
                                        className="btn btn-ghost"
                                        style={{ padding: '4px 10px', fontSize: '0.7rem' }}
                                        onClick={() => fetchHistory(fund.symbol)}
                                    >
                                        📈 View
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Loading & Empty */}
            {loading && (
                <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
                    <Landmark size={48} style={{ opacity: 0.3, marginBottom: '16px' }} />
                    <p>Loading mutual funds...</p>
                </div>
            )}

            {!loading && funds.length === 0 && (
                <div className="glass-card-static" style={{ padding: '60px', textAlign: 'center' }}>
                    <Landmark size={48} style={{ color: 'var(--accent-indigo)', opacity: 0.3, marginBottom: '16px' }} />
                    <p style={{ color: 'var(--text-secondary)' }}>
                        Unable to load mutual fund data. Make sure the backend server is running.
                    </p>
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
    padding: '12px 16px', fontSize: '0.85rem', color: 'var(--text-primary)',
};

export default MutualFundsPage;
