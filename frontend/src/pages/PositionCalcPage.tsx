import React, { useState } from 'react';
import { Calculator, TrendingUp, TrendingDown, DollarSign, Target } from 'lucide-react';

const PositionCalcPage: React.FC = () => {
    const [capital, setCapital] = useState('1000000');
    const [riskPct, setRiskPct] = useState('2');
    const [entry, setEntry] = useState('2850');
    const [stopLoss, setStopLoss] = useState('2780');
    const [targetPrice, setTargetPrice] = useState('3020');
    const [instrument, setInstrument] = useState<'stock' | 'futures' | 'options'>('stock');
    const [lotSize, setLotSize] = useState('25');

    const cap = parseFloat(capital) || 0;
    const risk = parseFloat(riskPct) || 0;
    const ent = parseFloat(entry) || 0;
    const sl = parseFloat(stopLoss) || 0;
    const tgt = parseFloat(targetPrice) || 0;

    const riskAmount = cap * (risk / 100);
    const slDistance = Math.abs(ent - sl);
    const rawQty = slDistance > 0 ? Math.floor(riskAmount / slDistance) : 0;
    const lot = instrument !== 'stock' ? (parseInt(lotSize) || 1) : 1;
    const qty = instrument !== 'stock' ? Math.floor(rawQty / lot) * lot : rawQty;
    const actualRisk = qty * slDistance;
    const potentialProfit = qty * Math.abs(tgt - ent);
    const riskReward = actualRisk > 0 ? (potentialProfit / actualRisk) : 0;
    const capitalRequired = qty * ent;

    const inputStyle: React.CSSProperties = {
        width: '100%', padding: '12px 14px', borderRadius: 10,
        border: '1px solid var(--border-color)', background: 'var(--bg-primary)',
        color: 'var(--text-primary)', fontSize: '1rem', fontWeight: 500,
        boxSizing: 'border-box',
    };
    const labelStyle: React.CSSProperties = {
        fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block',
        marginBottom: 6, fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.04em',
    };
    const cardStyle: React.CSSProperties = {
        background: 'var(--card-bg)', borderRadius: 16, padding: 24,
        border: '1px solid var(--border-color)',
    };
    const metricStyle: React.CSSProperties = {
        ...cardStyle, textAlign: 'center', padding: '20px 16px',
    };

    return (
        <div style={{ padding: '32px 40px', maxWidth: 900, margin: '0 auto' }}>
            <div style={{ marginBottom: 28 }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Calculator size={28} /> Position Sizing Calculator
                </h1>
                <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>
                    Calculate exact position size based on your risk management rules
                </p>
            </div>

            {/* Instrument Toggle */}
            <div style={{ display: 'flex', gap: 6, marginBottom: 20 }}>
                {(['stock', 'futures', 'options'] as const).map(t => (
                    <button key={t} onClick={() => setInstrument(t)}
                        style={{
                            padding: '8px 20px', borderRadius: 8, border: 'none', cursor: 'pointer',
                            background: instrument === t ? 'var(--accent-primary)' : 'var(--card-bg)',
                            color: instrument === t ? '#fff' : 'var(--text-muted)',
                            fontWeight: instrument === t ? 600 : 400, fontSize: '0.85rem',
                            textTransform: 'capitalize',
                        }}>{t}</button>
                ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
                {/* Inputs */}
                <div style={cardStyle}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 20 }}>
                        📊 Parameters
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                        <div>
                            <label style={labelStyle}>Total Capital (₹)</label>
                            <input type="number" value={capital} onChange={e => setCapital(e.target.value)} style={inputStyle} />
                        </div>
                        <div>
                            <label style={labelStyle}>Risk Per Trade (%)</label>
                            <input type="number" value={riskPct} onChange={e => setRiskPct(e.target.value)} step="0.5" style={inputStyle} />
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                            <div>
                                <label style={labelStyle}>Entry Price (₹)</label>
                                <input type="number" value={entry} onChange={e => setEntry(e.target.value)} style={inputStyle} />
                            </div>
                            <div>
                                <label style={labelStyle}>Stop Loss (₹)</label>
                                <input type="number" value={stopLoss} onChange={e => setStopLoss(e.target.value)} style={inputStyle} />
                            </div>
                        </div>
                        <div>
                            <label style={labelStyle}>Target Price (₹)</label>
                            <input type="number" value={targetPrice} onChange={e => setTargetPrice(e.target.value)} style={inputStyle} />
                        </div>
                        {instrument !== 'stock' && (
                            <div>
                                <label style={labelStyle}>Lot Size</label>
                                <input type="number" value={lotSize} onChange={e => setLotSize(e.target.value)} style={inputStyle} />
                            </div>
                        )}
                    </div>
                </div>

                {/* Results */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div style={{ ...metricStyle, borderLeft: '4px solid #6366f1' }}>
                        <DollarSign size={20} style={{ color: '#6366f1', marginBottom: 4 }} />
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Position Size</div>
                        <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                            {qty.toLocaleString()} <span style={{ fontSize: '0.9rem', fontWeight: 400, color: 'var(--text-muted)' }}>
                                {instrument === 'stock' ? 'shares' : `(${Math.floor(qty / lot)} lots)`}
                            </span>
                        </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                        <div style={{ ...metricStyle, borderLeft: '4px solid #ef4444' }}>
                            <TrendingDown size={18} style={{ color: '#ef4444', marginBottom: 4 }} />
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Risk Amount</div>
                            <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#ef4444' }}>
                                ₹{actualRisk.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                            </div>
                        </div>
                        <div style={{ ...metricStyle, borderLeft: '4px solid #10b981' }}>
                            <TrendingUp size={18} style={{ color: '#10b981', marginBottom: 4 }} />
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Potential Profit</div>
                            <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#10b981' }}>
                                ₹{potentialProfit.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                            </div>
                        </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                        <div style={{ ...metricStyle, borderLeft: '4px solid #f59e0b' }}>
                            <Target size={18} style={{ color: '#f59e0b', marginBottom: 4 }} />
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Risk : Reward</div>
                            <div style={{ fontSize: '1.3rem', fontWeight: 700, color: riskReward >= 2 ? '#10b981' : riskReward >= 1 ? '#f59e0b' : '#ef4444' }}>
                                1 : {riskReward.toFixed(1)}
                            </div>
                        </div>
                        <div style={{ ...metricStyle, borderLeft: '4px solid #8b5cf6' }}>
                            <DollarSign size={18} style={{ color: '#8b5cf6', marginBottom: 4 }} />
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Capital Required</div>
                            <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                                ₹{capitalRequired.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                            </div>
                        </div>
                    </div>

                    {/* Visual Risk Bar */}
                    <div style={cardStyle}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 8 }}>Capital Utilization</div>
                        <div style={{ height: 8, background: 'var(--border-color)', borderRadius: 4, overflow: 'hidden' }}>
                            <div style={{
                                height: '100%', borderRadius: 4,
                                width: `${Math.min((capitalRequired / cap) * 100, 100)}%`,
                                background: capitalRequired / cap > 0.5 ? '#ef4444' : capitalRequired / cap > 0.25 ? '#f59e0b' : '#10b981',
                                transition: 'width 0.3s ease',
                            }} />
                        </div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4 }}>
                            {((capitalRequired / cap) * 100).toFixed(1)}% of capital
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PositionCalcPage;
