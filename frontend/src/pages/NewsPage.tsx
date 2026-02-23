import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Search, Calendar, ExternalLink, TrendingUp, Newspaper, RefreshCw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { endpoints } from '../config';

interface NewsArticle {
    title: string;
    summary: string;
    published_at: string;
    source: string;
    link: string;
    sentiment?: {
        label: string;
        score: number;
    };
}

interface SentimentTrend {
    _id: string;
    avg_score: number;
    count: number;
    positive_count: number;
    negative_count: number;
}

const NewsPage: React.FC = () => {
    const [news, setNews] = useState<NewsArticle[]>([]);
    const [trend, setTrend] = useState<SentimentTrend[]>([]);
    const [searchTerm, setSearchTerm] = useState("India");
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [newsRes, trendRes] = await Promise.all([
                axios.get(endpoints.news, { params: { symbol: searchTerm, limit: 50 } }),
                axios.get(endpoints.sentiment_trend, { params: { symbol: searchTerm } }),
            ]);
            setNews(newsRes.data);
            setTrend(trendRes.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, []);

    const handleSearch = (e: React.FormEvent) => { e.preventDefault(); fetchData(); };

    const getSentimentStyle = (label?: string) => {
        if (!label) return 'badge badge-unknown';
        if (label === 'positive') return 'badge badge-bullish';
        if (label === 'negative') return 'badge badge-bearish';
        return 'badge badge-sideways';
    };

    const totalPositive = trend.reduce((acc, curr) => acc + curr.positive_count, 0);
    const totalNegative = trend.reduce((acc, curr) => acc + curr.negative_count, 0);

    return (
        <div className="animate-fade-in">
            <div className="page-header">
                <h1>📰 News & Sentiment</h1>
                <p>AI-powered sentiment analysis on market news</p>
            </div>

            {/* Search */}
            <form onSubmit={handleSearch} className="glass-card-static" style={{ padding: '16px 20px', marginBottom: '24px', display: 'flex', gap: '12px', alignItems: 'center' }}>
                <Search size={18} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                <input
                    className="input"
                    style={{ flex: 1, background: 'transparent', border: 'none', padding: '4px 0' }}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search stocks or keywords (e.g. INFY, Inflation)..."
                />
                <button type="submit" className="btn btn-primary" style={{ flexShrink: 0 }}>
                    <RefreshCw size={14} /> Analyze
                </button>
            </form>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '20px' }}>
                {/* News Feed */}
                <div>
                    <h3 className="section-title">
                        <Calendar size={16} /> Results for "{searchTerm}"
                        <span style={{ marginLeft: 'auto', fontSize: '0.7rem', fontWeight: 400 }}>{news.length} articles</span>
                    </h3>

                    {loading ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {[1, 2, 3].map(i => <div key={i} className="skeleton" style={{ height: '120px' }} />)}
                        </div>
                    ) : news.length === 0 ? (
                        <div className="glass-card-static" style={{ padding: '60px', textAlign: 'center' }}>
                            <Newspaper size={40} style={{ color: 'var(--text-muted)', opacity: 0.3, marginBottom: '12px' }} />
                            <p style={{ color: 'var(--text-muted)' }}>No news found. Try a different search term.</p>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {news.map((item, idx) => (
                                <div
                                    key={idx}
                                    className="glass-card animate-fade-in"
                                    style={{ padding: '20px', animationDelay: `${idx * 40}ms` }}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                                        <span className={getSentimentStyle(item.sentiment?.label)}>
                                            {item.sentiment?.label || 'Unknown'}
                                            {item.sentiment?.score && ` ${(item.sentiment.score * 100).toFixed(0)}%`}
                                        </span>
                                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            {new Date(item.published_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                                        </span>
                                    </div>
                                    <a
                                        href={item.link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        style={{ color: 'var(--text-primary)', textDecoration: 'none', fontWeight: 600, fontSize: '0.95rem', display: 'flex', alignItems: 'flex-start', gap: '6px', marginBottom: '8px', lineHeight: 1.4 }}
                                    >
                                        {item.title}
                                        <ExternalLink size={14} style={{ flexShrink: 0, opacity: 0.4, marginTop: '3px' }} />
                                    </a>
                                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', margin: '0 0 8px', lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                                        {item.summary}
                                    </p>
                                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Source: {item.source}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Sidebar: Sentiment Trend */}
                <div>
                    <div className="glass-card-static" style={{ padding: '20px', position: 'sticky', top: '24px' }}>
                        <h3 className="section-title">
                            <TrendingUp size={16} style={{ color: 'var(--accent-indigo)' }} /> Sentiment Trend
                        </h3>
                        <div style={{ height: '220px', marginBottom: '16px' }}>
                            {trend.length === 0 ? (
                                <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                                    No trend data available
                                </div>
                            ) : (
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={trend}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="_id" tick={{ fontSize: 10 }} />
                                        <YAxis domain={[0, 1]} />
                                        <Tooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '10px' }} />
                                        <Legend />
                                        <Line type="monotone" dataKey="avg_score" stroke="#6366f1" name="Sentiment" strokeWidth={2} dot={false} />
                                    </LineChart>
                                </ResponsiveContainer>
                            )}
                        </div>

                        {/* Stats */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                            <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.15)', textAlign: 'center' }}>
                                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-green)' }}>{totalPositive}</div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Positive</div>
                            </div>
                            <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.15)', textAlign: 'center' }}>
                                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-red)' }}>{totalNegative}</div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Negative</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default NewsPage;
