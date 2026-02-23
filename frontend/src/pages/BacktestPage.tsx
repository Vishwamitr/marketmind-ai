import React, { useState } from 'react';
import axios from 'axios';
import { BarChart3, Play, Loader } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import MetricsCard from '../components/MetricsCard';
import { endpoints } from '../config';

interface BacktestResult {
    total_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    total_trades: number;
    equity_curve: { date: string; equity: number }[];
}

const BacktestPage: React.FC = () => {
    const [symbol, setSymbol] = useState('INFY');
    const [startDate, setStartDate] = useState('2024-01-01');
    const [endDate, setEndDate] = useState('2025-01-01');
    const [strategy, setStrategy] = useState('SMACross');
    const [scenario, setScenario] = useState('None');
    const [capital, setCapital] = useState('100000');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<BacktestResult | null>(null);
    const [error, setError] = useState('');

    const runBacktest = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setResult(null);
        try {
            const res = await axios.post(endpoints.backtest, {
                symbol, start_date: startDate, end_date: endDate, strategy,
                initial_capital: parseFloat(capital),
                scenario: scenario === 'None' ? null : scenario,
            });
            setResult(res.data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Backtest failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="animate-fade-in">
            <div className="page-header">
                <h1>📊 Backtesting Engine</h1>
                <p>Test trading strategies on historical data with stress scenarios</p>
            </div>

            {/* Config Form */}
            <div className="glass-card-static" style={{ padding: '24px', marginBottom: '24px' }}>
                <form onSubmit={runBacktest} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', alignItems: 'end' }}>
                    <div>
                        <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Symbol</label>
                        <input className="input" value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} placeholder="INFY" required />
                    </div>
                    <div>
                        <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Start Date</label>
                        <input className="input" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
                    </div>
                    <div>
                        <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>End Date</label>
                        <input className="input" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} required />
                    </div>
                    <div>
                        <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Strategy</label>
                        <select className="input" value={strategy} onChange={(e) => setStrategy(e.target.value)}>
                            <option value="SMACross">SMA Crossover</option>
                            <option value="BuyAndHold">Buy & Hold</option>
                        </select>
                    </div>
                    <div>
                        <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Capital (₹)</label>
                        <input className="input" type="number" value={capital} onChange={(e) => setCapital(e.target.value)} min="1000" />
                    </div>
                    <div>
                        <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Stress Scenario</label>
                        <select className="input" value={scenario} onChange={(e) => setScenario(e.target.value)}>
                            <option value="None">None</option>
                            <option value="FlashCrash">Flash Crash (-20%)</option>
                        </select>
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={loading} style={{ height: '42px' }}>
                        {loading ? <Loader size={16} className="animate-spin" /> : <Play size={16} />}
                        {loading ? 'Running...' : 'Run Backtest'}
                    </button>
                </form>
            </div>

            {error && (
                <div className="glass-card-static" style={{ padding: '16px', marginBottom: '24px', borderLeft: '3px solid var(--accent-red)', color: 'var(--accent-red)', fontSize: '0.875rem' }}>
                    {error}
                </div>
            )}

            {/* Results */}
            {result && (
                <div className="animate-fade-in">
                    <div className="grid-metrics">
                        <MetricsCard
                            label="Total Return"
                            value={`${result.total_return >= 0 ? '+' : ''}${result.total_return.toFixed(2)}%`}
                            trend={result.total_return >= 0 ? 'up' : 'down'}
                            color={result.total_return >= 0 ? 'green' : 'red'}
                        />
                        <MetricsCard label="Sharpe Ratio" value={result.sharpe_ratio.toFixed(2)} color="blue" />
                        <MetricsCard label="Max Drawdown" value={`${result.max_drawdown.toFixed(2)}%`} trend="down" color="red" />
                        <MetricsCard label="Win Rate" value={`${result.win_rate.toFixed(1)}%`} subValue={`${result.total_trades} trades`} color="purple" />
                    </div>

                    {result.equity_curve && result.equity_curve.length > 0 && (
                        <div className="glass-card-static" style={{ padding: '20px' }}>
                            <h3 className="section-title"><BarChart3 size={16} /> Equity Curve</h3>
                            <div style={{ height: '350px' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={result.equity_curve}>
                                        <defs>
                                            <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                                                <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="date" tickFormatter={(d) => new Date(d).toLocaleDateString('en-IN', { month: 'short', year: '2-digit' })} />
                                        <YAxis />
                                        <Tooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '10px' }} />
                                        <Area type="monotone" dataKey="equity" stroke="#6366f1" fill="url(#eqGrad)" strokeWidth={2} name="Portfolio Value" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {!result && !loading && (
                <div className="glass-card-static" style={{ padding: '60px', textAlign: 'center' }}>
                    <BarChart3 size={48} style={{ color: 'var(--accent-indigo)', opacity: 0.3, marginBottom: '16px' }} />
                    <p style={{ color: 'var(--text-secondary)' }}>Configure your backtest above and click Run</p>
                </div>
            )}
        </div>
    );
};

export default BacktestPage;
