import React, { useState } from 'react';
import axios from 'axios';
import { GitCompareArrows, Plus, X, TrendingUp, TrendingDown } from 'lucide-react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { endpoints } from '../config';

interface StockData {
    symbol: string;
    prices: { date: string; close: number }[];
    current: number;
    change_pct: number;
    rsi: number;
    high_52w: number;
    low_52w: number;
}

const COLORS = ['#6366f1', '#f59e0b', '#10b981', '#ef4444'];

const ComparePage: React.FC = () => {
    const [symbols, setSymbols] = useState<string[]>([]);
    const [input, setInput] = useState('');
    const [data, setData] = useState<StockData[]>([]);
    const [loading, setLoading] = useState(false);
    const [chartData, setChartData] = useState<Record<string, number | string>[]>([]);

    const addSymbol = async () => {
        const sym = input.trim().toUpperCase();
        if (!sym || symbols.includes(sym) || symbols.length >= 4) return;

        setLoading(true);
        try {
            const histRes = await axios.get(endpoints.market_history(sym), { params: { period: '6mo' } });
            const prices = histRes.data.data || histRes.data.prices || [];

            // Normalize prices to percentage change from first day
            const firstClose = prices.length > 0 ? prices[0].close : 1;
            const normalizedPrices = prices.map((p: { date: string; close: number }) => ({
                date: p.date,
                close: ((p.close - firstClose) / firstClose) * 100,
            }));

            const latest = prices.length > 0 ? prices[prices.length - 1] : { close: 0 };
            const prev = prices.length > 1 ? prices[prices.length - 2] : latest;
            const changePct = prev.close > 0 ? ((latest.close - prev.close) / prev.close) * 100 : 0;

            const newStock: StockData = {
                symbol: sym,
                prices: normalizedPrices,
                current: latest.close || 0,
                change_pct: Math.round(changePct * 100) / 100,
                rsi: 50,
                high_52w: Math.max(...prices.map((p: { close: number }) => p.close)),
                low_52w: Math.min(...prices.map((p: { close: number }) => p.close)),
            };

            const newSymbols = [...symbols, sym];
            const newData = [...data, newStock];
            setSymbols(newSymbols);
            setData(newData);
            setInput('');

            // Rebuild chart data
            rebuildChartData(newData);
        } catch {
            /* ignore */
        }
        setLoading(false);
    };

    const rebuildChartData = (stockData: StockData[]) => {
        if (stockData.length === 0) { setChartData([]); return; }

        const maxLen = Math.max(...stockData.map(s => s.prices.length));
        const merged: Record<string, number | string>[] = [];

        for (let i = 0; i < maxLen; i++) {
            const point: Record<string, number | string> = {};
            point['date'] = stockData[0].prices[i]?.date || '';
            for (const s of stockData) {
                if (i < s.prices.length) {
                    point[s.symbol] = Math.round(s.prices[i].close * 100) / 100;
                }
            }
            merged.push(point);
        }
        setChartData(merged);
    };

    const removeSymbol = (sym: string) => {
        const newSymbols = symbols.filter(s => s !== sym);
        const newData = data.filter(d => d.symbol !== sym);
        setSymbols(newSymbols);
        setData(newData);
        rebuildChartData(newData);
    };

    const cardStyle: React.CSSProperties = {
        background: 'var(--card-bg)', borderRadius: 16, padding: 24,
        border: '1px solid var(--border-color)',
    };

    return (
        <div style={{ padding: '32px 40px', maxWidth: 1100, margin: '0 auto' }}>
            <div style={{ marginBottom: 24 }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 10 }}>
                    <GitCompareArrows size={28} /> Stock Comparison
                </h1>
                <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>
                    Compare up to 4 stocks side-by-side with overlaid price charts
                </p>
            </div>

            {/* Symbol Input */}
            <div style={{ display: 'flex', gap: 10, marginBottom: 20, alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: 6, flex: 1, flexWrap: 'wrap' }}>
                    {symbols.map((s, i) => (
                        <span key={s} style={{
                            padding: '6px 12px', borderRadius: 8, fontSize: '0.85rem', fontWeight: 600,
                            background: `${COLORS[i]}20`, color: COLORS[i], display: 'flex', alignItems: 'center', gap: 6,
                        }}>
                            <span style={{ width: 8, height: 8, borderRadius: '50%', background: COLORS[i], display: 'inline-block' }} />
                            {s}
                            <X size={14} style={{ cursor: 'pointer', opacity: 0.7 }} onClick={() => removeSymbol(s)} />
                        </span>
                    ))}
                </div>
                {symbols.length < 4 && (
                    <div style={{ display: 'flex', gap: 6 }}>
                        <input value={input} onChange={e => setInput(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && addSymbol()}
                            placeholder="Add symbol..." disabled={loading}
                            style={{
                                padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border-color)',
                                background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: '0.9rem', width: 150,
                            }} />
                        <button onClick={addSymbol} disabled={loading || !input.trim()}
                            style={{
                                padding: '10px 16px', borderRadius: 10, border: 'none',
                                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#fff',
                                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.85rem',
                            }}>
                            <Plus size={16} /> Add
                        </button>
                    </div>
                )}
            </div>

            {/* Chart */}
            {chartData.length > 0 && (
                <div style={{ ...cardStyle, marginBottom: 20 }}>
                    <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>
                        Normalized Price Performance (%)
                    </h3>
                    <ResponsiveContainer width="100%" height={360}>
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                            <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                                tickFormatter={(v: string) => v ? v.slice(5) : ''} />
                            <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                                tickFormatter={(v: number) => `${v}%`} />
                            <Tooltip
                                contentStyle={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: 10 }}
                                formatter={(value: number | undefined) => [`${(value ?? 0).toFixed(2)}%`]}
                            />
                            <Legend />
                            {symbols.map((sym, i) => (
                                <Line key={sym} type="monotone" dataKey={sym} stroke={COLORS[i]}
                                    strokeWidth={2} dot={false} />
                            ))}
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Comparison Table */}
            {data.length > 0 && (
                <div style={{ ...cardStyle, overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr>
                                <th style={thStyle}>Metric</th>
                                {data.map((d, i) => (
                                    <th key={d.symbol} style={{ ...thStyle, color: COLORS[i] }}>{d.symbol}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {[
                                { label: 'Price', render: (d: StockData) => `₹${d.current.toLocaleString()}` },
                                {
                                    label: 'Day Change', render: (d: StockData) => (
                                        <span style={{ color: d.change_pct >= 0 ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                                            {d.change_pct >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                                            {' '}{d.change_pct >= 0 ? '+' : ''}{d.change_pct}%
                                        </span>
                                    )
                                },
                                { label: '52W High', render: (d: StockData) => `₹${d.high_52w.toLocaleString()}` },
                                { label: '52W Low', render: (d: StockData) => `₹${d.low_52w.toLocaleString()}` },
                                {
                                    label: 'From 52W High', render: (d: StockData) => {
                                        const pct = ((d.current - d.high_52w) / d.high_52w * 100).toFixed(1);
                                        return <span style={{ color: '#ef4444' }}>{pct}%</span>;
                                    }
                                },
                            ].map(row => (
                                <tr key={row.label}>
                                    <td style={tdStyle}>{row.label}</td>
                                    {data.map(d => (
                                        <td key={d.symbol} style={{ ...tdStyle, textAlign: 'center' }}>
                                            {typeof row.render(d) === 'string' ? row.render(d) : row.render(d)}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {data.length === 0 && (
                <div style={{ ...cardStyle, textAlign: 'center', padding: 60, color: 'var(--text-muted)' }}>
                    <GitCompareArrows size={48} style={{ marginBottom: 12, opacity: 0.3 }} />
                    <p>Add stocks above to start comparing</p>
                </div>
            )}
        </div>
    );
};

const thStyle: React.CSSProperties = {
    padding: '12px 16px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)',
    textAlign: 'left', textTransform: 'uppercase', borderBottom: '1px solid var(--border-color)',
};
const tdStyle: React.CSSProperties = {
    padding: '12px 16px', fontSize: '0.85rem', color: 'var(--text-primary)',
    borderBottom: '1px solid var(--border-color)',
};

export default ComparePage;
