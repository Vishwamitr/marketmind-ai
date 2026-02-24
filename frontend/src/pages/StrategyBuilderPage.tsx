import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Trash2, RefreshCw } from 'lucide-react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, ReferenceLine
} from 'recharts';
import { endpoints } from '../config';

interface Leg {
    id: number;
    option_type: 'call' | 'put';
    action: 'buy' | 'sell';
    strike: string;
    premium: string;
    quantity: string;
    lot_size: string;
}

interface PayoffPoint {
    price: number;
    pnl: number;
}

const TEMPLATES: Record<string, Leg[]> = {
    'Bull Call Spread': [
        { id: 1, option_type: 'call', action: 'buy', strike: '19000', premium: '200', quantity: '1', lot_size: '50' },
        { id: 2, option_type: 'call', action: 'sell', strike: '19200', premium: '80', quantity: '1', lot_size: '50' },
    ],
    'Bear Put Spread': [
        { id: 1, option_type: 'put', action: 'buy', strike: '19000', premium: '180', quantity: '1', lot_size: '50' },
        { id: 2, option_type: 'put', action: 'sell', strike: '18800', premium: '60', quantity: '1', lot_size: '50' },
    ],
    'Long Straddle': [
        { id: 1, option_type: 'call', action: 'buy', strike: '19000', premium: '200', quantity: '1', lot_size: '50' },
        { id: 2, option_type: 'put', action: 'buy', strike: '19000', premium: '180', quantity: '1', lot_size: '50' },
    ],
    'Iron Condor': [
        { id: 1, option_type: 'put', action: 'sell', strike: '18800', premium: '60', quantity: '1', lot_size: '50' },
        { id: 2, option_type: 'put', action: 'buy', strike: '18600', premium: '20', quantity: '1', lot_size: '50' },
        { id: 3, option_type: 'call', action: 'sell', strike: '19200', premium: '80', quantity: '1', lot_size: '50' },
        { id: 4, option_type: 'call', action: 'buy', strike: '19400', premium: '25', quantity: '1', lot_size: '50' },
    ],
};

let nextId = 10;

const StrategyBuilderPage: React.FC = () => {
    const [legs, setLegs] = useState<Leg[]>(TEMPLATES['Bull Call Spread']);
    const [spot, setSpot] = useState('19000');
    const [payoff, setPayoff] = useState<PayoffPoint[]>([]);
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState<{ maxProfit: number; maxLoss: number; breakEvens: number[] } | null>(null);

    const calculate = async () => {
        setLoading(true);
        try {
            const res = await axios.post(endpoints.options_strategy_payoff, {
                legs: legs.map(l => ({
                    option_type: l.option_type,
                    strike: parseFloat(l.strike) || 0,
                    premium: parseFloat(l.premium) || 0,
                    quantity: (parseInt(l.quantity) || 1) * (l.action === 'sell' ? -1 : 1),
                    lot_size: parseInt(l.lot_size) || 1,
                })),
                spot_price: parseFloat(spot) || 19000,
                price_range_pct: 15,
            });
            const data = res.data;
            const pts: PayoffPoint[] = (data.payoff || []).map((p: { underlying_price: number; total_pnl: number }) => ({
                price: Math.round(p.underlying_price),
                pnl: Math.round(p.total_pnl),
            }));
            setPayoff(pts);

            const pnls = pts.map(p => p.pnl);
            const maxP = Math.max(...pnls);
            const maxL = Math.min(...pnls);
            // Find breakeven crossings
            const bes: number[] = [];
            for (let i = 1; i < pts.length; i++) {
                if ((pts[i - 1].pnl < 0 && pts[i].pnl >= 0) || (pts[i - 1].pnl >= 0 && pts[i].pnl < 0)) {
                    bes.push(Math.round((pts[i - 1].price + pts[i].price) / 2));
                }
            }
            setStats({ maxProfit: maxP, maxLoss: maxL, breakEvens: bes });
        } catch { /* ignore */ }
        setLoading(false);
    };

    useEffect(() => { calculate(); }, []);

    const addLeg = () => setLegs(l => [...l, { id: nextId++, option_type: 'call', action: 'buy', strike: '19000', premium: '100', quantity: '1', lot_size: '50' }]);
    const removeLeg = (id: number) => setLegs(l => l.filter(x => x.id !== id));
    const updateLeg = (id: number, key: keyof Leg, val: string) =>
        setLegs(l => l.map(x => x.id === id ? { ...x, [key]: val } : x));

    return (
        <div className="animate-fade-in" style={{ padding: '24px 0' }}>
            <div style={{ marginBottom: 24 }}>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>📦 Strategy Builder</h1>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '4px 0 0' }}>Build multi-leg options strategies and visualize the P&L payoff</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
                {/* Templates */}
                <div className="glass-card-static" style={{ padding: 20 }}>
                    <h3 style={{ margin: '0 0 14px', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>📋 Templates</h3>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                        {Object.keys(TEMPLATES).map(t => (
                            <button key={t} onClick={() => { setLegs(TEMPLATES[t]); setTimeout(calculate, 100); }} style={{
                                padding: '6px 14px', borderRadius: 8, border: '1px solid var(--border-subtle)',
                                background: 'rgba(99,102,241,0.08)', color: 'var(--accent-indigo)', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 600,
                            }}>{t}</button>
                        ))}
                    </div>
                    <div style={{ marginTop: 16, display: 'flex', alignItems: 'center', gap: 10 }}>
                        <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Spot Price</label>
                        <input value={spot} onChange={e => setSpot(e.target.value)}
                            style={{
                                width: 100, padding: '6px 10px', borderRadius: 8, border: '1px solid var(--border-subtle)',
                                background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '0.85rem'
                            }} />
                    </div>
                </div>

                {/* Stats */}
                {stats && (
                    <div className="glass-card-static" style={{ padding: 20 }}>
                        <h3 style={{ margin: '0 0 14px', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>📊 Strategy Stats</h3>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                            {[
                                { label: 'Max Profit', value: stats.maxProfit === Infinity ? 'Unlimited' : `₹${stats.maxProfit.toLocaleString()}`, color: '#10b981' },
                                { label: 'Max Loss', value: stats.maxLoss === -Infinity ? 'Unlimited' : `₹${Math.abs(stats.maxLoss).toLocaleString()}`, color: '#ef4444' },
                                { label: 'Break-even(s)', value: stats.breakEvens.length ? stats.breakEvens.join(' / ') : 'N/A', color: '#f59e0b' },
                                { label: 'Risk:Reward', value: stats.maxLoss !== 0 ? `1:${(stats.maxProfit / Math.abs(stats.maxLoss)).toFixed(1)}` : '∞', color: 'var(--accent-indigo)' },
                            ].map((s, i) => (
                                <div key={i} style={{ padding: '10px 14px', borderRadius: 10, background: `${s.color}10`, border: `1px solid ${s.color}30` }}>
                                    <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</div>
                                    <div style={{ fontSize: '1.05rem', fontWeight: 700, color: s.color }}>{s.value}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Leg Editor */}
            <div className="glass-card-static" style={{ padding: 20, marginBottom: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                    <h3 style={{ margin: 0, fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>⚙️ Legs ({legs.length})</h3>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <button onClick={addLeg} style={{ padding: '6px 14px', borderRadius: 8, border: '1px solid var(--border-subtle)', background: 'transparent', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: 4 }}>
                            <Plus size={14} /> Add Leg
                        </button>
                        <button onClick={calculate} disabled={loading} style={{ padding: '6px 14px', borderRadius: 8, border: 'none', background: 'var(--gradient-primary)', color: '#fff', cursor: 'pointer', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: 4, fontWeight: 600 }}>
                            <RefreshCw size={14} className={loading ? 'spin' : ''} /> Calculate
                        </button>
                    </div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {legs.map(leg => (
                        <div key={leg.id} style={{ display: 'grid', gridTemplateColumns: '80px 80px 100px 100px 80px 80px 36px', gap: 8, alignItems: 'center' }}>
                            {[
                                { key: 'action', opts: ['buy', 'sell'] },
                                { key: 'option_type', opts: ['call', 'put'] },
                            ].map(({ key, opts }) => (
                                <select key={key} value={(leg as any)[key]} onChange={e => updateLeg(leg.id, key as keyof Leg, e.target.value)}
                                    style={{ padding: '6px 8px', borderRadius: 8, border: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)', color: (leg as any)[key] === 'buy' || (leg as any)[key] === 'call' ? '#10b981' : '#ef4444', fontSize: '0.8rem', fontWeight: 600 }}>
                                    {opts.map(o => <option key={o} value={o}>{o.toUpperCase()}</option>)}
                                </select>
                            ))}
                            {[
                                { key: 'strike', placeholder: 'Strike' },
                                { key: 'premium', placeholder: 'Premium' },
                                { key: 'quantity', placeholder: 'Qty' },
                                { key: 'lot_size', placeholder: 'Lot' },
                            ].map(({ key, placeholder }) => (
                                <input key={key} value={(leg as any)[key]} placeholder={placeholder}
                                    onChange={e => updateLeg(leg.id, key as keyof Leg, e.target.value)}
                                    style={{ padding: '6px 8px', borderRadius: 8, border: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '0.8rem' }} />
                            ))}
                            <button onClick={() => removeLeg(leg.id)} style={{ padding: 6, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8, cursor: 'pointer', color: '#ef4444', display: 'flex', alignItems: 'center' }}>
                                <Trash2 size={14} />
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Payoff Chart */}
            {payoff.length > 0 && (
                <div className="glass-card-static" style={{ padding: 20 }}>
                    <h3 style={{ margin: '0 0 16px', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>📈 Payoff Diagram at Expiry</h3>
                    <div style={{ height: 320 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={payoff}>
                                <defs>
                                    <linearGradient id="pnlGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                                <XAxis dataKey="price" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                                <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} tickFormatter={(v: number) => `₹${(v / 1000).toFixed(0)}K`} />
                                <Tooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 10 }}
                                    formatter={(v: number | undefined) => [`₹${(v ?? 0).toLocaleString()}`, 'P&L']} />
                                <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" />
                                {parseFloat(spot) > 0 && <ReferenceLine x={Math.round(parseFloat(spot))} stroke="#6366f1" strokeDasharray="5 5" label={{ value: 'Spot', fill: '#6366f1', fontSize: 11 }} />}
                                {stats?.breakEvens.map(be => (
                                    <ReferenceLine key={be} x={be} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: 'BE', fill: '#f59e0b', fontSize: 10 }} />
                                ))}
                                <Area type="monotone" dataKey="pnl" stroke="#6366f1" strokeWidth={2} fill="url(#pnlGrad)" name="P&L" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}
        </div>
    );
};

export default StrategyBuilderPage;
