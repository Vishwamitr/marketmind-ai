import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Briefcase, RefreshCw, ShoppingCart, DollarSign, TrendingUp, PieChart, BarChart3, Shield, Zap, Target } from 'lucide-react';
import MetricsCard from '../components/MetricsCard';
import { endpoints } from '../config';

interface Holding {
    symbol: string;
    quantity: number;
    avg_price: number;
    current_price: number;
    market_value: number;
    unrealized_pnl: number;
    return_pct: number;
}

interface PortfolioState {
    cash: number;
    equity: number;
    holdings_value: number;
    holdings: Holding[];
}

interface AllocationItem { sector: string; value: number; pct: number; }
interface ReturnPoint { date: string; return_pct: number; }
interface RiskMetrics {
    sharpe_ratio?: number; beta?: number; max_drawdown?: number;
    annualized_return?: number; annualized_volatility?: number;
    best_day?: number; worst_day?: number; win_rate?: number;
    total_invested?: number; current_value?: number;
}
interface AnalyticsData {
    risk_metrics: RiskMetrics;
    allocation: AllocationItem[];
    daily_returns: ReturnPoint[];
    benchmark_returns: ReturnPoint[];
}

const SECTOR_COLORS: Record<string, string> = {
    IT: '#818cf8', Banking: '#60a5fa', Energy: '#f59e0b', FMCG: '#34d399',
    Auto: '#f87171', Pharma: '#a78bfa', Finance: '#fb923c', Telecom: '#38bdf8',
    Infra: '#94a3b8', Consumer: '#e879f9', Metals: '#6ee7b7', Power: '#fcd34d', Other: '#64748b',
};

const PortfolioPage: React.FC = () => {
    const [portfolio, setPortfolio] = useState<PortfolioState | null>(null);
    const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [orderSymbol, setOrderSymbol] = useState('');
    const [orderQty, setOrderQty] = useState('');
    const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY');
    const [orderMsg, setOrderMsg] = useState('');
    const [activeTab, setActiveTab] = useState<'holdings' | 'analytics'>('holdings');

    const fetchPortfolio = async () => {
        setLoading(true);
        try {
            const [pRes, aRes] = await Promise.allSettled([
                axios.get(endpoints.portfolio),
                axios.get(endpoints.portfolio_analytics),
            ]);
            if (pRes.status === 'fulfilled') setPortfolio(pRes.value.data);
            if (aRes.status === 'fulfilled') setAnalytics(aRes.value.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchPortfolio(); }, []);

    const handleOrder = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await axios.post(endpoints.order, {
                symbol: orderSymbol.toUpperCase(),
                quantity: parseInt(orderQty),
                side: orderSide,
            });
            setOrderMsg(`✅ ${res.data.message || 'Order placed'}`);
            fetchPortfolio();
            setOrderSymbol('');
            setOrderQty('');
        } catch (err: unknown) {
            const axErr = err as { response?: { data?: { detail?: string } } };
            setOrderMsg(`❌ ${axErr.response?.data?.detail || 'Order failed'}`);
        }
    };

    const totalPnl = portfolio?.holdings.reduce((sum, h) => sum + h.unrealized_pnl, 0) || 0;
    const rm = analytics?.risk_metrics;

    // SVG Donut chart
    const renderDonut = (alloc: AllocationItem[]) => {
        if (!alloc.length) return null;
        const size = 200;
        const cx = size / 2, cy = size / 2, r = 70;
        let startAngle = -90;
        const paths = alloc.map((item) => {
            const angle = (item.pct / 100) * 360;
            const endAngle = startAngle + angle;
            const largeArc = angle > 180 ? 1 : 0;
            const sx = cx + r * Math.cos((startAngle * Math.PI) / 180);
            const sy = cy + r * Math.sin((startAngle * Math.PI) / 180);
            const ex = cx + r * Math.cos((endAngle * Math.PI) / 180);
            const ey = cy + r * Math.sin((endAngle * Math.PI) / 180);
            const path = `M ${cx} ${cy} L ${sx} ${sy} A ${r} ${r} 0 ${largeArc} 1 ${ex} ${ey} Z`;
            startAngle = endAngle;
            return <path key={item.sector} d={path} fill={SECTOR_COLORS[item.sector] || '#64748b'} opacity={0.85} stroke="var(--bg-primary)" strokeWidth="2" />;
        });

        return (
            <div style={{ display: 'flex', gap: '24px', alignItems: 'center', flexWrap: 'wrap' }}>
                <svg width={size} height={size}>{paths}<circle cx={cx} cy={cy} r={35} fill="var(--bg-primary)" /></svg>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {alloc.map(item => (
                        <div key={item.sector} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem' }}>
                            <div style={{ width: 10, height: 10, borderRadius: '3px', background: SECTOR_COLORS[item.sector] || '#64748b' }} />
                            <span style={{ color: 'var(--text-secondary)' }}>{item.sector}</span>
                            <span style={{ fontWeight: 600, marginLeft: 'auto', fontFamily: 'monospace', color: 'var(--text-primary)' }}>{item.pct}%</span>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    return (
        <div className="animate-fade-in">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1>💼 Portfolio</h1>
                    <p>Manage holdings, track performance, and analyze risk metrics</p>
                </div>
                <button className="btn btn-ghost" onClick={fetchPortfolio} disabled={loading}>
                    <RefreshCw size={14} /> Refresh
                </button>
            </div>

            {/* Summary Cards */}
            {portfolio && (
                <div className="grid-metrics">
                    <MetricsCard label="Total Equity" value={`₹${portfolio.equity.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`} color="blue" icon={<DollarSign size={24} />} />
                    <MetricsCard label="Cash Available" value={`₹${portfolio.cash.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`} color="cyan" icon={<Briefcase size={24} />} />
                    <MetricsCard label="Holdings Value" value={`₹${portfolio.holdings_value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`} color="purple" icon={<PieChart size={24} />} />
                    <MetricsCard label="Unrealized P&L" value={`${totalPnl >= 0 ? '+' : ''}₹${totalPnl.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`} trend={totalPnl >= 0 ? 'up' : 'down'} color={totalPnl >= 0 ? 'green' : 'red'} icon={<TrendingUp size={24} />} />
                </div>
            )}

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
                {(['holdings', 'analytics'] as const).map(tab => (
                    <button key={tab} onClick={() => setActiveTab(tab)} style={{
                        padding: '8px 20px', borderRadius: '10px', cursor: 'pointer', fontWeight: 600,
                        fontSize: '0.8rem', fontFamily: 'inherit', textTransform: 'capitalize',
                        background: activeTab === tab ? 'rgba(99,102,241,0.12)' : 'transparent',
                        border: `1px solid ${activeTab === tab ? 'rgba(99,102,241,0.3)' : 'var(--border-subtle)'}`,
                        color: activeTab === tab ? '#818cf8' : 'var(--text-muted)',
                    }}>
                        {tab === 'holdings' ? <Briefcase size={14} style={{ marginRight: 6 }} /> : <BarChart3 size={14} style={{ marginRight: 6 }} />}
                        {tab}
                    </button>
                ))}
            </div>

            {activeTab === 'holdings' ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px' }}>
                    {/* Holdings Table */}
                    <div className="glass-card-static" style={{ padding: '20px' }}>
                        <h3 className="section-title"><Briefcase size={16} /> Holdings</h3>
                        {portfolio && portfolio.holdings.length > 0 ? (
                            <table className="data-table">
                                <thead><tr><th>Symbol</th><th>Qty</th><th>Avg Price</th><th>Current</th><th>Value</th><th>P&L</th><th>Return</th></tr></thead>
                                <tbody>
                                    {portfolio.holdings.map((h) => (
                                        <tr key={h.symbol}>
                                            <td style={{ fontWeight: 600 }}>{h.symbol}</td>
                                            <td>{h.quantity}</td>
                                            <td style={{ fontFamily: 'monospace' }}>₹{h.avg_price.toFixed(2)}</td>
                                            <td style={{ fontFamily: 'monospace' }}>₹{h.current_price.toFixed(2)}</td>
                                            <td style={{ fontFamily: 'monospace' }}>₹{h.market_value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                                            <td className={h.unrealized_pnl >= 0 ? 'text-gain' : 'text-loss'} style={{ fontWeight: 600, fontFamily: 'monospace' }}>
                                                {h.unrealized_pnl >= 0 ? '+' : ''}₹{h.unrealized_pnl.toFixed(0)}
                                            </td>
                                            <td className={h.return_pct >= 0 ? 'text-gain' : 'text-loss'} style={{ fontWeight: 600, fontFamily: 'monospace' }}>
                                                {h.return_pct >= 0 ? '+' : ''}{h.return_pct.toFixed(1)}%
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                                No holdings yet. Place an order to get started.
                            </div>
                        )}
                    </div>

                    {/* Order Form */}
                    <div className="glass-card-static" style={{ padding: '20px', alignSelf: 'flex-start', position: 'sticky', top: '24px' }}>
                        <h3 className="section-title"><ShoppingCart size={16} /> Place Order</h3>
                        <form onSubmit={handleOrder} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            <div>
                                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Side</label>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                                    {(['BUY', 'SELL'] as const).map(side => (
                                        <button key={side} type="button" onClick={() => setOrderSide(side)} style={{
                                            padding: '10px', borderRadius: '10px', border: '1px solid', fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', fontSize: '0.875rem',
                                            background: orderSide === side ? (side === 'BUY' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)') : 'transparent',
                                            borderColor: orderSide === side ? (side === 'BUY' ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)') : 'var(--border-subtle)',
                                            color: orderSide === side ? (side === 'BUY' ? 'var(--accent-green)' : 'var(--accent-red)') : 'var(--text-muted)',
                                        }}>{side}</button>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Symbol</label>
                                <input className="input" placeholder="e.g. INFY" value={orderSymbol} onChange={(e) => setOrderSymbol(e.target.value)} required />
                            </div>
                            <div>
                                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Quantity</label>
                                <input className="input" type="number" placeholder="e.g. 10" value={orderQty} onChange={(e) => setOrderQty(e.target.value)} required min="1" />
                            </div>
                            <button type="submit" className={`btn ${orderSide === 'BUY' ? 'btn-success' : 'btn-danger'}`} style={{ width: '100%', justifyContent: 'center', marginTop: '4px' }}>
                                {orderSide === 'BUY' ? 'Buy' : 'Sell'}
                            </button>
                        </form>
                        {orderMsg && (
                            <div style={{ marginTop: '12px', padding: '10px', borderRadius: '8px', fontSize: '0.8rem', background: orderMsg.includes('✅') ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', color: orderMsg.includes('✅') ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                                {orderMsg}
                            </div>
                        )}
                    </div>
                </div>
            ) : (
                /* Analytics Tab */
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                    {/* Risk Metrics */}
                    <div className="glass-card-static" style={{ padding: '20px' }}>
                        <h3 className="section-title"><Shield size={16} /> Risk Metrics</h3>
                        {rm ? (
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                {[
                                    { label: 'Sharpe Ratio', value: rm.sharpe_ratio?.toFixed(2), icon: <Zap size={14} />, color: (rm.sharpe_ratio || 0) > 1 ? '#34d399' : (rm.sharpe_ratio || 0) > 0 ? '#fbbf24' : '#f87171' },
                                    { label: 'Beta', value: rm.beta?.toFixed(2), icon: <BarChart3 size={14} />, color: '#60a5fa' },
                                    { label: 'Max Drawdown', value: `${rm.max_drawdown}%`, icon: <TrendingUp size={14} />, color: '#f87171' },
                                    { label: 'Ann. Return', value: `${rm.annualized_return}%`, icon: <Target size={14} />, color: (rm.annualized_return || 0) >= 0 ? '#34d399' : '#f87171' },
                                    { label: 'Volatility', value: `${rm.annualized_volatility}%`, icon: <BarChart3 size={14} />, color: '#fbbf24' },
                                    { label: 'Win Rate', value: `${rm.win_rate}%`, icon: <Zap size={14} />, color: (rm.win_rate || 0) > 50 ? '#34d399' : '#f87171' },
                                    { label: 'Best Day', value: `+${rm.best_day}%`, icon: <TrendingUp size={14} />, color: '#34d399' },
                                    { label: 'Worst Day', value: `${rm.worst_day}%`, icon: <TrendingUp size={14} />, color: '#f87171' },
                                ].map((m, i) => (
                                    <div key={i} style={{ padding: '12px', borderRadius: '10px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px', color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                                            {m.icon} {m.label}
                                        </div>
                                        <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'monospace', color: m.color }}>{m.value ?? '—'}</div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>No analytics data — add holdings first.</div>
                        )}
                    </div>

                    {/* Sector Allocation Donut */}
                    <div className="glass-card-static" style={{ padding: '20px' }}>
                        <h3 className="section-title"><PieChart size={16} /> Sector Allocation</h3>
                        {analytics?.allocation && analytics.allocation.length > 0 ? (
                            renderDonut(analytics.allocation)
                        ) : (
                            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>No allocation data.</div>
                        )}
                    </div>

                    {/* Benchmark Comparison */}
                    <div className="glass-card-static" style={{ padding: '20px', gridColumn: 'span 2' }}>
                        <h3 className="section-title"><BarChart3 size={16} /> Portfolio vs NIFTY 50 (Cumulative Returns)</h3>
                        {analytics?.daily_returns && analytics.daily_returns.length > 0 ? (
                            <div style={{ position: 'relative', height: '200px', overflow: 'hidden' }}>
                                <svg width="100%" height="200" viewBox={`0 0 ${analytics.daily_returns.length * 12} 200`} preserveAspectRatio="none">
                                    {/* Portfolio line */}
                                    <polyline
                                        fill="none" stroke="#818cf8" strokeWidth="2"
                                        points={analytics.daily_returns.map((p, i) => `${i * 12},${100 - p.return_pct * 2}`).join(' ')}
                                    />
                                    {/* Benchmark line */}
                                    {analytics.benchmark_returns && (
                                        <polyline
                                            fill="none" stroke="#f59e0b" strokeWidth="2" strokeDasharray="4"
                                            points={analytics.benchmark_returns.map((p, i) => `${i * 12},${100 - p.return_pct * 2}`).join(' ')}
                                        />
                                    )}
                                    <line x1="0" y1="100" x2={analytics.daily_returns.length * 12} y2="100" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
                                </svg>
                                <div style={{ display: 'flex', gap: '20px', marginTop: '8px', fontSize: '0.7rem' }}>
                                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: 12, height: 3, background: '#818cf8', display: 'inline-block' }} /> Portfolio</span>
                                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ width: 12, height: 3, background: '#f59e0b', display: 'inline-block', borderTop: '1px dashed #f59e0b' }} /> NIFTY 50</span>
                                </div>
                            </div>
                        ) : (
                            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>No return data available.</div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default PortfolioPage;
