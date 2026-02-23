import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Shield, Users, FileText, RefreshCw, Search } from 'lucide-react';
import MetricsCard from '../components/MetricsCard';
import { endpoints } from '../config';

interface AdminStats {
    total_users: number;
    total_stocks: number;
    total_news: number;
    active_sessions: number;
}

interface AuditLog {
    timestamp: string;
    action: string;
    user: string;
    details: string;
    ip_address?: string;
}

const AdminPage: React.FC = () => {
    const [stats, setStats] = useState<AdminStats | null>(null);
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [logFilter, setLogFilter] = useState('');

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [statsRes, logsRes] = await Promise.all([
                axios.get(endpoints.admin_stats).catch(() => ({ data: { total_users: 0, total_stocks: 0, total_news: 0, active_sessions: 0 } })),
                axios.get(endpoints.admin_logs, { params: { limit: 50 } }).catch(() => ({ data: [] })),
            ]);
            setStats(statsRes.data);
            setLogs(logsRes.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const filteredLogs = logFilter
        ? logs.filter(l => l.action?.toLowerCase().includes(logFilter.toLowerCase()) || l.user?.toLowerCase().includes(logFilter.toLowerCase()))
        : logs;

    return (
        <div className="animate-fade-in">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1>🛡️ Admin Panel</h1>
                    <p>System statistics and audit logs</p>
                </div>
                <button className="btn btn-ghost" onClick={fetchData} disabled={loading}>
                    <RefreshCw size={14} /> Refresh
                </button>
            </div>

            {stats && (
                <div className="grid-metrics">
                    <MetricsCard label="Total Users" value={stats.total_users} color="blue" icon={<Users size={24} />} />
                    <MetricsCard label="Tracked Stocks" value={stats.total_stocks} color="green" icon={<Shield size={24} />} />
                    <MetricsCard label="News Articles" value={stats.total_news} color="purple" icon={<FileText size={24} />} />
                    <MetricsCard label="Active Sessions" value={stats.active_sessions} color="amber" icon={<Users size={24} />} />
                </div>
            )}

            {/* Audit Logs */}
            <div className="glass-card-static" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 className="section-title" style={{ margin: 0 }}>
                        <FileText size={16} /> Audit Logs
                    </h3>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--bg-glass)', borderRadius: '10px', padding: '4px 12px', border: '1px solid var(--border-subtle)' }}>
                        <Search size={14} style={{ color: 'var(--text-muted)' }} />
                        <input
                            className="input"
                            style={{ border: 'none', background: 'transparent', padding: '6px 0', width: '200px' }}
                            placeholder="Filter logs..."
                            value={logFilter}
                            onChange={(e) => setLogFilter(e.target.value)}
                        />
                    </div>
                </div>
                <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Action</th>
                                <th>User</th>
                                <th>Details</th>
                                <th>IP</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredLogs.map((log, i) => (
                                <tr key={i}>
                                    <td style={{ whiteSpace: 'nowrap', fontSize: '0.8rem' }}>
                                        {new Date(log.timestamp).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                                    </td>
                                    <td>
                                        <span className="badge badge-unknown" style={{ textTransform: 'none' }}>{log.action}</span>
                                    </td>
                                    <td style={{ fontWeight: 500 }}>{log.user}</td>
                                    <td style={{ color: 'var(--text-secondary)', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {log.details}
                                    </td>
                                    <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{log.ip_address || '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {filteredLogs.length === 0 && (
                    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                        {logFilter ? 'No logs match your filter' : 'No audit logs available'}
                    </div>
                )}
            </div>
        </div>
    );
};

export default AdminPage;
