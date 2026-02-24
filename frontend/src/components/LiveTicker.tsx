import React, { useEffect, useRef, useState } from 'react';
import API_BASE_URL from '../config';

interface TickItem {
    symbol: string;
    price: number;
    change_pct: number;
}

const WS_URL = API_BASE_URL.replace('http', 'ws') + '/ws/ticker';

const LiveTicker: React.FC = () => {
    const [ticks, setTicks] = useState<TickItem[]>([]);
    const wsRef = useRef<WebSocket | null>(null);

    const connect = () => {
        try {
            const ws = new WebSocket(WS_URL);
            wsRef.current = ws;

            ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'ticker_update' && Array.isArray(msg.data)) {
                        setTicks(msg.data);
                    }
                } catch { /* ignore */ }
            };

            ws.onclose = () => {
                // Reconnect after 3s
                setTimeout(connect, 3000);
            };

            ws.onerror = () => ws.close();

            // Ping keep-alive every 30s
            const ping = setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) ws.send('ping');
            }, 30000);

            ws.addEventListener('close', () => clearInterval(ping));
        } catch { /* ignore */ }
    };

    useEffect(() => {
        connect();
        return () => wsRef.current?.close();
    }, []);

    if (ticks.length === 0) return null;

    return (
        <div style={{
            height: 36,
            background: 'rgba(10, 14, 26, 0.98)',
            borderBottom: '1px solid var(--border-subtle)',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            position: 'sticky',
            top: 0,
            zIndex: 100,
        }}>
            <div style={{
                display: 'flex',
                animation: 'tickerScroll 30s linear infinite',
                gap: 0,
                whiteSpace: 'nowrap',
                willChange: 'transform',
            }}>
                {/* Duplicate for seamless loop */}
                {[...ticks, ...ticks].map((t, i) => (
                    <span key={i} style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 6,
                        padding: '0 20px',
                        fontSize: '0.78rem',
                        borderRight: '1px solid rgba(255,255,255,0.06)',
                    }}>
                        <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{t.symbol}</span>
                        <span style={{ color: 'var(--text-secondary)' }}>₹{t.price.toLocaleString()}</span>
                        <span style={{
                            fontWeight: 600,
                            color: t.change_pct >= 0 ? '#10b981' : '#ef4444',
                        }}>
                            {t.change_pct >= 0 ? '▲' : '▼'} {Math.abs(t.change_pct)}%
                        </span>
                    </span>
                ))}
            </div>
        </div>
    );
};

export default LiveTicker;
