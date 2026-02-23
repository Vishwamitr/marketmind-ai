import React, { useEffect, useState, useRef, useCallback } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Star, Plus, Trash2, RefreshCw, Search } from 'lucide-react';
import { endpoints } from '../config';

interface WatchStock {
    symbol: string;
    name: string;
    price: number;
    change: number;
    change_pct: number;
    regime: string;
    adx: number | null;
    sma_200: number | null;
    atr: number | null;
    volume: number;
    timestamp: string;
}

interface SearchResult {
    symbol: string;
    index: string;
}

const WatchlistPage: React.FC = () => {
    const [stockData, setStockData] = useState<WatchStock[]>([]);
    const [newSymbol, setNewSymbol] = useState('');
    const [loading, setLoading] = useState(true);
    const [missing, setMissing] = useState<string[]>([]);
    const [addLoading, setAddLoading] = useState(false);
    const [suggestions, setSuggestions] = useState<SearchResult[]>([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [highlightIdx, setHighlightIdx] = useState(-1);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const navigate = useNavigate();

    useEffect(() => { fetchWatchlistData(); }, []);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
                setShowDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const fetchWatchlistData = async () => {
        setLoading(true);
        try {
            const res = await axios.get(endpoints.watchlist_data);
            setStockData(res.data.stocks || []);
            setMissing(res.data.missing || []);
        } catch (err) {
            console.error('Failed to fetch watchlist data', err);
            try {
                const wlRes = await axios.get(endpoints.watchlist);
                setMissing(wlRes.data.symbols || []);
            } catch { /* ignore */ }
        } finally {
            setLoading(false);
        }
    };

    const searchSymbols = useCallback(async (query: string) => {
        if (query.length < 1) {
            setSuggestions([]);
            setShowDropdown(false);
            return;
        }
        try {
            const res = await axios.get(endpoints.watchlist_search(query));
            setSuggestions(res.data.results || []);
            setShowDropdown(true);
            setHighlightIdx(-1);
        } catch {
            setSuggestions([]);
        }
    }, []);

    const handleInputChange = (value: string) => {
        const upper = value.toUpperCase();
        setNewSymbol(upper);
        // Debounce the search API call
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => searchSymbols(upper), 150);
    };

    const selectSymbol = (sym: string) => {
        setNewSymbol(sym);
        setShowDropdown(false);
        setSuggestions([]);
        // Auto-add on selection
        addSymbolDirect(sym);
    };

    const addSymbolDirect = async (sym: string) => {
        if (!sym) return;
        setAddLoading(true);
        try {
            await axios.post(endpoints.watchlist, { symbol: sym });
            setNewSymbol('');
            await fetchWatchlistData();
        } catch (err: any) {
            console.error('Failed to add symbol', err);
        } finally {
            setAddLoading(false);
        }
    };

    const addSymbol = async () => {
        const sym = newSymbol.trim().toUpperCase();
        if (!sym) return;
        await addSymbolDirect(sym);
    };

    const removeSymbol = async (sym: string) => {
        try {
            await axios.delete(endpoints.watchlist_remove(sym));
            setStockData(prev => prev.filter(s => s.symbol !== sym));
            setMissing(prev => prev.filter(s => s !== sym));
        } catch (err) {
            console.error('Failed to remove symbol', err);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (!showDropdown || suggestions.length === 0) {
            if (e.key === 'Enter') addSymbol();
            return;
        }
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setHighlightIdx(prev => Math.min(prev + 1, suggestions.length - 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setHighlightIdx(prev => Math.max(prev - 1, 0));
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (highlightIdx >= 0 && highlightIdx < suggestions.length) {
                selectSymbol(suggestions[highlightIdx].symbol);
            } else {
                addSymbol();
            }
        } else if (e.key === 'Escape') {
            setShowDropdown(false);
        }
    };

    const getRegimeBadge = (regime: string) => {
        const r = regime.toLowerCase();
        if (r.includes('bull')) return <span className="badge badge-bullish">● Bullish</span>;
        if (r.includes('bear')) return <span className="badge badge-bearish">● Bearish</span>;
        if (r.includes('volatile')) return <span className="badge badge-volatile">● Volatile</span>;
        if (r.includes('sideways')) return <span className="badge badge-sideways">● Sideways</span>;
        return <span className="badge badge-unknown">● Unknown</span>;
    };

    const getIndexColor = (idx: string) => {
        switch (idx) {
            case 'NIFTY 50': return '#6366f1';
            case 'NIFTY Next 50': return '#8b5cf6';
            case 'MidCap 150': return '#06b6d4';
            case 'SmallCap 250': return '#f59e0b';
            default: return '#64748b';
        }
    };

    return (
        <div className="animate-fade-in">
            <div className="page-header">
                <h1>⭐ Watchlist</h1>
                <p>Track your favorite stocks with live market data</p>
            </div>

            {/* Add Stock with Autocomplete */}
            <div className="glass-card-static" style={{ padding: '20px', marginBottom: '24px' }}>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    <div ref={dropdownRef} style={{ position: 'relative', maxWidth: '300px', flex: 1 }}>
                        <div style={{ position: 'relative' }}>
                            <Search size={14} style={{
                                position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)',
                                color: 'var(--text-muted)', pointerEvents: 'none',
                            }} />
                            <input
                                ref={inputRef}
                                className="input"
                                style={{ paddingLeft: '36px', width: '100%' }}
                                placeholder="Search stocks (e.g. REL, TCS, MAR...)"
                                value={newSymbol}
                                onChange={(e) => handleInputChange(e.target.value)}
                                onKeyDown={handleKeyDown}
                                onFocus={() => { if (suggestions.length > 0) setShowDropdown(true); }}
                            />
                        </div>

                        {/* Dropdown */}
                        {showDropdown && suggestions.length > 0 && (
                            <div style={{
                                position: 'absolute', top: '100%', left: 0, right: 0,
                                marginTop: '4px', zIndex: 50,
                                background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)',
                                borderRadius: '10px', overflow: 'hidden',
                                boxShadow: '0 8px 30px rgba(0,0,0,0.3)',
                            }}>
                                {suggestions.map((s, i) => (
                                    <div
                                        key={s.symbol}
                                        onClick={() => selectSymbol(s.symbol)}
                                        style={{
                                            padding: '10px 14px',
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            cursor: 'pointer',
                                            background: i === highlightIdx ? 'rgba(99,102,241,0.15)' : 'transparent',
                                            borderBottom: i < suggestions.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                                            transition: 'background 0.1s',
                                        }}
                                        onMouseEnter={() => setHighlightIdx(i)}
                                    >
                                        <span style={{ fontWeight: 700, fontSize: '0.88rem', letterSpacing: '0.02em' }}>
                                            {s.symbol}
                                        </span>
                                        <span style={{
                                            fontSize: '0.62rem', fontWeight: 600,
                                            padding: '2px 8px', borderRadius: '6px',
                                            color: getIndexColor(s.index),
                                            background: `${getIndexColor(s.index)}15`,
                                        }}>
                                            {s.index}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <button className="btn btn-primary" onClick={addSymbol} disabled={addLoading}>
                        <Plus size={16} /> {addLoading ? 'Fetching...' : 'Add'}
                    </button>
                    <button className="btn btn-ghost" onClick={fetchWatchlistData} disabled={loading}>
                        <RefreshCw size={14} /> Refresh
                    </button>
                </div>
            </div>

            {/* Watchlist Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
                {stockData.map((stock, i) => (
                    <div
                        key={stock.symbol}
                        className="glass-card animate-fade-in"
                        style={{ padding: '20px', cursor: 'pointer', animationDelay: `${i * 60}ms` }}
                        onClick={() => navigate(`/analysis/${stock.symbol}`)}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                            <div>
                                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>{stock.symbol}</h3>
                                <p style={{ margin: '2px 0 0', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                                    {stock.name || stock.symbol}
                                </p>
                            </div>
                            <button
                                className="btn btn-ghost"
                                style={{ padding: '6px', border: 'none' }}
                                onClick={(e) => { e.stopPropagation(); removeSymbol(stock.symbol); }}
                                title="Remove from watchlist"
                            >
                                <Trash2 size={16} style={{ color: 'var(--accent-red)' }} />
                            </button>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px', marginBottom: '12px' }}>
                            <span style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                                ₹{stock.price?.toFixed(2) || '—'}
                            </span>
                            {stock.change_pct !== undefined && (
                                <span style={{
                                    fontSize: '0.85rem', fontWeight: 600,
                                    color: stock.change_pct >= 0 ? 'var(--accent-green)' : 'var(--accent-red)',
                                }}>
                                    {stock.change_pct >= 0 ? '▲' : '▼'} {Math.abs(stock.change_pct).toFixed(2)}%
                                </span>
                            )}
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            {getRegimeBadge(stock.regime)}
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                Vol: {stock.volume ? stock.volume.toLocaleString() : '—'}
                            </div>
                        </div>

                        {stock.sma_200 && (
                            <div style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                SMA 200: ₹{stock.sma_200.toFixed(2)}
                                <span style={{ marginLeft: '8px', color: stock.price > stock.sma_200 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                                    ({stock.price > stock.sma_200 ? 'Above' : 'Below'})
                                </span>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Auto-removed symbols (invalid tickers cleaned up) */}
            {missing.length > 0 && (
                <div className="glass-card-static" style={{ padding: '16px', marginTop: '16px' }}>
                    <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        🧹 Auto-removed invalid symbols: {missing.join(', ')} — these don't have valid NSE tickers. Refresh to clear this message.
                    </p>
                </div>
            )}

            {/* Empty State */}
            {stockData.length === 0 && !loading && missing.length === 0 && (
                <div className="glass-card-static" style={{ padding: '60px', textAlign: 'center' }}>
                    <Star size={48} style={{ color: 'var(--accent-amber)', opacity: 0.3, marginBottom: '16px' }} />
                    <p style={{ color: 'var(--text-secondary)' }}>Your watchlist is empty. Add stocks above to start tracking.</p>
                </div>
            )}

            {/* Loading */}
            {loading && (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                    <RefreshCw size={24} className="animate-spin" />
                    <p>Loading watchlist data...</p>
                </div>
            )}
        </div>
    );
};

export default WatchlistPage;
