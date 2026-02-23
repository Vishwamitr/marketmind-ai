import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Grid3X3 } from 'lucide-react';
import { endpoints } from '../config';

interface Stock {
    symbol: string;
    price: number;
    change_pct: number;
    volume: number;
    rsi: number;
    market_cap: number;
}

const SECTOR_MAP: Record<string, string[]> = {
    'Banking': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'KOTAKBANK', 'AXISBANK', 'BAJFINANCE'],
    'IT': ['TCS', 'INFY', 'HCLTECH', 'WIPRO', 'TECHM'],
    'Energy': ['RELIANCE', 'NTPC', 'POWERGRID'],
    'FMCG': ['HINDUNILVR', 'ITC', 'NESTLEIND'],
    'Auto': ['MARUTI', 'TATAMOTORS', 'M&M'],
    'Metals': ['TATASTEEL', 'JSWSTEEL'],
    'Pharma': ['SUNPHARMA', 'DRREDDY'],
    'Others': ['LT', 'BHARTIARTL', 'TITAN', 'ASIANPAINT', 'ULTRACEMCO', 'ADANIENT'],
};

const getColor = (change: number): string => {
    if (change >= 3) return '#059669';
    if (change >= 1.5) return '#10b981';
    if (change >= 0.5) return '#34d399';
    if (change >= 0) return '#6ee7b7';
    if (change >= -0.5) return '#fca5a5';
    if (change >= -1.5) return '#f87171';
    if (change >= -3) return '#ef4444';
    return '#dc2626';
};

const HeatmapPage: React.FC = () => {
    const [stocks, setStocks] = useState<Stock[]>([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        axios.get(endpoints.market_screener).then(res => {
            setStocks(res.data.stocks || []);
        }).catch(() => { }).finally(() => setLoading(false));
    }, []);

    // Group stocks by sector
    const sectorData: Record<string, Stock[]> = {};
    for (const [sector, syms] of Object.entries(SECTOR_MAP)) {
        const matched = stocks.filter(s => syms.includes(s.symbol));
        if (matched.length > 0) sectorData[sector] = matched;
    }

    if (loading) return (
        <div style={{ padding: '32px 40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <div className="shimmer" style={{ height: 400, borderRadius: 16 }} />
        </div>
    );

    return (
        <div style={{ padding: '32px 40px' }}>
            <div style={{ marginBottom: 24 }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Grid3X3 size={28} /> Market Heatmap
                </h1>
                <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>
                    NSE NIFTY 50 stocks colored by daily change — click any stock to view analysis
                </p>
            </div>

            {/* Legend */}
            <div style={{ display: 'flex', gap: 16, marginBottom: 20, justifyContent: 'center', flexWrap: 'wrap' }}>
                {[
                    { label: '≥ +3%', color: '#059669' },
                    { label: '+1.5%', color: '#10b981' },
                    { label: '+0.5%', color: '#34d399' },
                    { label: '0%', color: '#6ee7b7' },
                    { label: '-0.5%', color: '#fca5a5' },
                    { label: '-1.5%', color: '#f87171' },
                    { label: '≤ -3%', color: '#dc2626' },
                ].map(l => (
                    <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        <div style={{ width: 14, height: 14, borderRadius: 3, background: l.color }} />
                        {l.label}
                    </div>
                ))}
            </div>

            {/* Sector Blocks */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {Object.entries(sectorData).map(([sector, stks]) => (
                    <div key={sector}>
                        <h3 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            {sector}
                        </h3>
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            {stks.map(s => {
                                const bg = getColor(s.change_pct);
                                const textColor = Math.abs(s.change_pct) >= 1 ? '#fff' : 'rgba(0,0,0,0.8)';
                                return (
                                    <div key={s.symbol}
                                        onClick={() => navigate(`/analysis/${s.symbol}`)}
                                        style={{
                                            background: bg, borderRadius: 10, padding: '14px 18px',
                                            minWidth: 120, flex: '1 1 140px', maxWidth: 200,
                                            cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s',
                                            display: 'flex', flexDirection: 'column', alignItems: 'center',
                                            gap: 2,
                                        }}
                                        onMouseEnter={e => {
                                            (e.currentTarget as HTMLElement).style.transform = 'scale(1.05)';
                                            (e.currentTarget as HTMLElement).style.boxShadow = '0 8px 24px rgba(0,0,0,0.2)';
                                        }}
                                        onMouseLeave={e => {
                                            (e.currentTarget as HTMLElement).style.transform = 'scale(1)';
                                            (e.currentTarget as HTMLElement).style.boxShadow = 'none';
                                        }}>
                                        <span style={{ fontWeight: 700, fontSize: '0.9rem', color: textColor }}>{s.symbol}</span>
                                        <span style={{ fontSize: '0.85rem', color: textColor }}>₹{s.price.toLocaleString()}</span>
                                        <span style={{ fontWeight: 600, fontSize: '0.85rem', color: textColor }}>
                                            {s.change_pct >= 0 ? '+' : ''}{s.change_pct}%
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                ))}
            </div>

            {stocks.length === 0 && !loading && (
                <div style={{
                    textAlign: 'center', padding: 60, color: 'var(--text-muted)',
                    background: 'var(--card-bg)', borderRadius: 16, border: '1px solid var(--border-color)',
                }}>
                    <Grid3X3 size={48} style={{ marginBottom: 12, opacity: 0.3 }} />
                    <p>No stock data available. Start the backend server first.</p>
                </div>
            )}
        </div>
    );
};

export default HeatmapPage;
