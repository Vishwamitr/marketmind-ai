import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Globe, Clock, TrendingUp, TrendingDown } from 'lucide-react';
import { endpoints } from '../config';

interface IndexData {
    name: string;
    ticker: string;
    value: number;
    change: number;
    change_pct: number;
}

interface MarketHoursData {
    status: string;
    status_label: string;
    ist_time: string;
    weekday: string;
    indices: IndexData[];
}

const MarketHoursWidget: React.FC = () => {
    const [data, setData] = useState<MarketHoursData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await axios.get(endpoints.market_hours);
                setData(res.data);
            } catch (err) {
                console.error('Market hours fetch failed', err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
        const interval = setInterval(fetchData, 60000); // refresh every 60s
        return () => clearInterval(interval);
    }, []);

    const statusColor = data?.status === 'open' ? '#34d399' : data?.status === 'pre_market' ? '#fbbf24' : '#f87171';
    const statusIcon = data?.status === 'open' ? '🟢' : data?.status === 'pre_market' ? '🟡' : '🔴';

    if (loading) {
        return (
            <div className="glass-card-static" style={{ padding: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    <Globe size={16} className="animate-spin" style={{ opacity: 0.3 }} /> Loading market data...
                </div>
            </div>
        );
    }

    if (!data) return null;

    return (
        <div className="glass-card-static animate-fade-in" style={{ padding: '20px' }}>
            {/* Market Status Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                    <h3 className="section-title" style={{ marginBottom: '4px' }}>
                        <Globe size={16} /> Market Status
                    </h3>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span>{statusIcon}</span>
                        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: statusColor }}>{data.status_label}</span>
                    </div>
                </div>
                <div style={{ textAlign: 'right', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    <Clock size={12} style={{ display: 'inline', marginRight: '4px' }} />
                    {data.ist_time}
                </div>
            </div>

            {/* Global Indices Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: '10px' }}>
                {data.indices.map((idx) => (
                    <div key={idx.ticker} style={{
                        padding: '12px', borderRadius: '10px',
                        background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)',
                        transition: 'all 0.2s ease',
                    }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            {idx.change_pct >= 0 ? <TrendingUp size={12} style={{ color: '#34d399' }} /> : <TrendingDown size={12} style={{ color: '#f87171' }} />}
                            {idx.name}
                        </div>
                        <div style={{ fontSize: '1rem', fontWeight: 700, fontFamily: 'monospace', color: 'var(--text-primary)' }}>
                            {idx.value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                        </div>
                        <div style={{
                            fontSize: '0.75rem', fontWeight: 600, fontFamily: 'monospace',
                            color: idx.change_pct >= 0 ? '#34d399' : '#f87171',
                        }}>
                            {idx.change >= 0 ? '+' : ''}{idx.change.toFixed(2)} ({idx.change_pct >= 0 ? '+' : ''}{idx.change_pct.toFixed(2)}%)
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default MarketHoursWidget;
