import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Activity, RefreshCw, AlertTriangle, CheckCircle } from 'lucide-react';

import { endpoints } from '../config';

interface ModelMetrics {
    model_name: string;
    accuracy: number;
    loss: number;
    last_trained: string;
    predictions_count: number;
    drift_score: number;
}

const ModelMonitorPage: React.FC = () => {
    const [metrics, setMetrics] = useState<ModelMetrics[]>([]);
    const [logs, setLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [recalculating, setRecalculating] = useState(false);

    useEffect(() => { fetchData(); }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [metricsRes, logsRes] = await Promise.all([
                axios.get(endpoints.monitor_metrics).catch(() => ({ data: [] })),
                axios.get(endpoints.monitor_logs).catch(() => ({ data: [] })),
            ]);
            setMetrics(metricsRes.data);
            setLogs(logsRes.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const recalculate = async () => {
        setRecalculating(true);
        try {
            await axios.post(endpoints.monitor_calculate);
            fetchData();
        } catch (err) {
            console.error(err);
        } finally {
            setRecalculating(false);
        }
    };

    const getDriftBadge = (score: number) => {
        if (score < 0.3) return <span className="badge badge-bullish">Low Drift</span>;
        if (score < 0.7) return <span className="badge badge-sideways">Medium Drift</span>;
        return <span className="badge badge-bearish">High Drift</span>;
    };

    return (
        <div className="animate-fade-in">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1>⚡ Model Monitor</h1>
                    <p>Track model performance, accuracy drift, and prediction health</p>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="btn btn-primary" onClick={recalculate} disabled={recalculating}>
                        {recalculating ? <RefreshCw size={14} className="animate-spin" /> : <Activity size={14} />}
                        Recalculate
                    </button>
                    <button className="btn btn-ghost" onClick={fetchData} disabled={loading}>
                        <RefreshCw size={14} /> Refresh
                    </button>
                </div>
            </div>

            {/* Model Cards */}
            {metrics.length > 0 ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                    {metrics.map((model, i) => (
                        <div key={model.model_name} className="glass-card-static animate-fade-in" style={{ padding: '20px', animationDelay: `${i * 80}ms` }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                                <div>
                                    <h3 style={{ margin: '0 0 4px', fontWeight: 700, fontSize: '1rem' }}>{model.model_name}</h3>
                                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                                        Last trained: {new Date(model.last_trained).toLocaleDateString('en-IN')}
                                    </span>
                                </div>
                                {getDriftBadge(model.drift_score)}
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.15)', textAlign: 'center' }}>
                                    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-green)' }}>
                                        {(model.accuracy * 100).toFixed(1)}%
                                    </div>
                                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Accuracy</div>
                                </div>
                                <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)', textAlign: 'center' }}>
                                    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-indigo)' }}>
                                        {model.predictions_count}
                                    </div>
                                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Predictions</div>
                                </div>
                            </div>

                            <div style={{ marginTop: '12px', padding: '8px 12px', borderRadius: '8px', background: 'rgba(255,255,255,0.02)', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                Loss: {model.loss.toFixed(4)} · Drift: {model.drift_score.toFixed(2)}
                            </div>
                        </div>
                    ))}
                </div>
            ) : !loading ? (
                <div className="glass-card-static" style={{ padding: '60px', textAlign: 'center', marginBottom: '24px' }}>
                    <Activity size={48} style={{ color: 'var(--accent-indigo)', opacity: 0.3, marginBottom: '16px' }} />
                    <p style={{ color: 'var(--text-secondary)' }}>No model metrics available. Click "Recalculate" to generate.</p>
                </div>
            ) : null}

            {/* Logs */}
            {logs.length > 0 && (
                <div className="glass-card-static" style={{ padding: '20px' }}>
                    <h3 className="section-title"><Activity size={16} /> Model Logs</h3>
                    <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Event</th>
                                    <th>Model</th>
                                    <th>Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                {logs.map((log, i) => (
                                    <tr key={i}>
                                        <td style={{ whiteSpace: 'nowrap', fontSize: '0.8rem' }}>
                                            {new Date(log.timestamp).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                                        </td>
                                        <td>
                                            {log.event === 'error' ? (
                                                <span style={{ color: 'var(--accent-red)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                    <AlertTriangle size={14} /> {log.event}
                                                </span>
                                            ) : (
                                                <span style={{ color: 'var(--accent-green)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                    <CheckCircle size={14} /> {log.event}
                                                </span>
                                            )}
                                        </td>
                                        <td style={{ fontWeight: 500 }}>{log.model || '—'}</td>
                                        <td style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{log.details || '—'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ModelMonitorPage;
