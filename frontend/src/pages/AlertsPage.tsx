import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Bell, Plus, Trash2, CheckCircle, AlertTriangle, RefreshCw } from 'lucide-react';
import { endpoints } from '../config';

interface Alert {
    id: number;
    symbol: string;
    condition: string;
    threshold: number;
    status: string;
    created_at: number;
    triggered_at: number | null;
    current_value: number | null;
    note: string;
}

const CONDITION_LABELS: Record<string, string> = {
    price_above: 'Price Above',
    price_below: 'Price Below',
    rsi_above: 'RSI Above',
    rsi_below: 'RSI Below',
    volume_spike: 'Volume Spike ≥',
};

const AlertsPage: React.FC = () => {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [triggered, setTriggered] = useState<Alert[]>([]);
    const [tab, setTab] = useState<'active' | 'triggered'>('active');
    const [loading, setLoading] = useState(true);
    const [checking, setChecking] = useState(false);

    // Form state
    const [symbol, setSymbol] = useState('');
    const [condition, setCondition] = useState('price_above');
    const [threshold, setThreshold] = useState('');
    const [note, setNote] = useState('');
    const [showForm, setShowForm] = useState(false);

    const fetchAlerts = async () => {
        setLoading(true);
        try {
            const [activeRes, triggeredRes] = await Promise.all([
                axios.get(endpoints.alerts),
                axios.get(endpoints.alerts_triggered),
            ]);
            setAlerts(activeRes.data.alerts || []);
            setTriggered(triggeredRes.data.alerts || []);
        } catch { /* ignore */ }
        setLoading(false);
    };

    useEffect(() => { fetchAlerts(); }, []);

    const createAlert = async () => {
        if (!symbol || !threshold) return;
        try {
            await axios.post(endpoints.alerts, {
                symbol: symbol.toUpperCase(),
                condition,
                threshold: parseFloat(threshold),
                note,
            });
            setSymbol(''); setThreshold(''); setNote('');
            setShowForm(false);
            fetchAlerts();
            // Browser notification permission
            if (Notification.permission === 'default') Notification.requestPermission();
        } catch { /* ignore */ }
    };

    const deleteAlert = async (id: number) => {
        try {
            await axios.delete(endpoints.alerts_delete(id));
            fetchAlerts();
        } catch { /* ignore */ }
    };

    const checkAlerts = async () => {
        setChecking(true);
        try {
            const res = await axios.post(endpoints.alerts_check);
            if (res.data.triggered > 0 && Notification.permission === 'granted') {
                new Notification('🔔 MarketMind Alert', {
                    body: `${res.data.triggered} alert(s) triggered!`,
                });
            }
            fetchAlerts();
        } catch { /* ignore */ }
        setChecking(false);
    };

    const formatTime = (ts: number) => new Date(ts * 1000).toLocaleString('en-IN');

    const cardStyle: React.CSSProperties = {
        background: 'var(--card-bg)', borderRadius: 16, padding: 24,
        border: '1px solid var(--border-color)',
    };

    return (
        <div style={{ padding: '32px 40px', maxWidth: 960, margin: '0 auto' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 10 }}>
                        <Bell size={28} /> Price Alerts
                    </h1>
                    <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>
                        Get notified when stocks hit your price targets
                    </p>
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                    <button onClick={checkAlerts} disabled={checking}
                        style={{
                            padding: '10px 18px', borderRadius: 10, border: '1px solid var(--border-color)',
                            background: 'var(--card-bg)', color: 'var(--text-primary)', cursor: 'pointer',
                            display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem',
                        }}>
                        <RefreshCw size={16} className={checking ? 'spin' : ''} /> Check Now
                    </button>
                    <button onClick={() => setShowForm(!showForm)}
                        style={{
                            padding: '10px 18px', borderRadius: 10, border: 'none',
                            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#fff',
                            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
                            fontSize: '0.85rem', fontWeight: 600,
                        }}>
                        <Plus size={16} /> New Alert
                    </button>
                </div>
            </div>

            {/* Create Alert Form */}
            {showForm && (
                <div style={{ ...cardStyle, marginBottom: 20, animation: 'fadeIn 0.3s ease' }}>
                    <h3 style={{ marginBottom: 16, color: 'var(--text-primary)', fontWeight: 600 }}>Create Alert</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 12 }}>
                        <div>
                            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Symbol</label>
                            <input value={symbol} onChange={e => setSymbol(e.target.value)} placeholder="RELIANCE"
                                style={{
                                    width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-color)',
                                    background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: '0.9rem',
                                    boxSizing: 'border-box',
                                }} />
                        </div>
                        <div>
                            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Condition</label>
                            <select value={condition} onChange={e => setCondition(e.target.value)}
                                style={{
                                    width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-color)',
                                    background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: '0.9rem',
                                    boxSizing: 'border-box',
                                }}>
                                {Object.entries(CONDITION_LABELS).map(([k, v]) => (
                                    <option key={k} value={k}>{v}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Threshold</label>
                            <input type="number" value={threshold} onChange={e => setThreshold(e.target.value)} placeholder="2850"
                                style={{
                                    width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-color)',
                                    background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: '0.9rem',
                                    boxSizing: 'border-box',
                                }} />
                        </div>
                    </div>
                    <input value={note} onChange={e => setNote(e.target.value)} placeholder="Optional note..."
                        style={{
                            width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-color)',
                            background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: '0.9rem',
                            marginBottom: 12, boxSizing: 'border-box',
                        }} />
                    <button onClick={createAlert}
                        style={{
                            padding: '10px 24px', borderRadius: 10, border: 'none',
                            background: 'linear-gradient(135deg, #10b981, #059669)', color: '#fff',
                            cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem',
                        }}>
                        Create Alert
                    </button>
                </div>
            )}

            {/* Tabs */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
                {(['active', 'triggered'] as const).map(t => (
                    <button key={t} onClick={() => setTab(t)}
                        style={{
                            padding: '8px 20px', borderRadius: 8, border: 'none', cursor: 'pointer',
                            background: tab === t ? 'var(--accent-primary)' : 'var(--card-bg)',
                            color: tab === t ? '#fff' : 'var(--text-muted)',
                            fontWeight: tab === t ? 600 : 400, fontSize: '0.85rem',
                            textTransform: 'capitalize',
                        }}>
                        {t === 'active' ? `Active (${alerts.length})` : `Triggered (${triggered.length})`}
                    </button>
                ))}
            </div>

            {/* Alert List */}
            {loading ? (
                <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-muted)' }}>Loading alerts...</div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {(tab === 'active' ? alerts : triggered).length === 0 && (
                        <div style={{ ...cardStyle, textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>
                            <Bell size={40} style={{ marginBottom: 12, opacity: 0.4 }} />
                            <p>No {tab} alerts</p>
                        </div>
                    )}
                    {(tab === 'active' ? alerts : triggered).map(a => (
                        <div key={a.id} style={{
                            ...cardStyle, padding: '16px 20px',
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            borderLeft: `4px solid ${a.status === 'triggered' ? '#f59e0b' : '#6366f1'}`,
                        }}>
                            <div style={{ flex: 1 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                                    <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-primary)' }}>
                                        {a.symbol}
                                    </span>
                                    <span style={{
                                        padding: '2px 10px', borderRadius: 6,
                                        background: a.status === 'triggered' ? 'rgba(245,158,11,0.15)' : 'rgba(99,102,241,0.15)',
                                        color: a.status === 'triggered' ? '#f59e0b' : '#6366f1',
                                        fontSize: '0.7rem', fontWeight: 600,
                                    }}>
                                        {a.status === 'triggered' ? <><AlertTriangle size={12} /> TRIGGERED</> : <><CheckCircle size={12} /> ACTIVE</>}
                                    </span>
                                </div>
                                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                    {CONDITION_LABELS[a.condition] || a.condition}: <strong style={{ color: 'var(--text-primary)' }}>
                                        {a.condition.includes('price') ? `₹${a.threshold.toLocaleString()}` : a.threshold}
                                    </strong>
                                    {a.current_value !== null && a.status === 'triggered' && (
                                        <span> → Current: <strong style={{ color: '#f59e0b' }}>
                                            {a.condition.includes('price') ? `₹${a.current_value.toLocaleString()}` : a.current_value}
                                        </strong></span>
                                    )}
                                </div>
                                {a.note && <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4, fontStyle: 'italic' }}>📝 {a.note}</div>}
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4 }}>
                                    Created: {formatTime(a.created_at)}
                                    {a.triggered_at && ` • Triggered: ${formatTime(a.triggered_at)}`}
                                </div>
                            </div>
                            <button onClick={() => deleteAlert(a.id)}
                                style={{
                                    padding: 8, borderRadius: 8, border: 'none', cursor: 'pointer',
                                    background: 'rgba(239,68,68,0.1)', color: '#ef4444',
                                }}>
                                <Trash2 size={16} />
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default AlertsPage;
