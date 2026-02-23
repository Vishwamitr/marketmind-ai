import React, { useEffect, useRef, useState } from 'react';
import {
    createChart,
    ColorType,
    CrosshairMode,
    CandlestickSeries,
    HistogramSeries,
    LineSeries,
} from 'lightweight-charts';
import type { IChartApi, Time } from 'lightweight-charts';

interface ChartDataPoint {
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    sma_50?: number;
    sma_200?: number;
    rsi?: number;
    macd?: number;
    macd_signal?: number;
    macd_hist?: number;
    adx?: number;
    atr?: number;
    bb_upper?: number;
    bb_lower?: number;
}

interface AdvancedChartProps {
    data: ChartDataPoint[];
    symbol: string;
    height?: number;
    showVolume?: boolean;
    showSMA?: boolean;
    showBollinger?: boolean;
    showRSI?: boolean;
    showMACD?: boolean;
}

const AdvancedChart: React.FC<AdvancedChartProps> = ({
    data,
    height = 500,
    showVolume = true,
    showSMA = true,
    showBollinger = false,
    showRSI = false,
    showMACD = false,
}) => {
    const mainChartRef = useRef<HTMLDivElement>(null);
    const rsiChartRef = useRef<HTMLDivElement>(null);
    const macdChartRef = useRef<HTMLDivElement>(null);
    const [activeOverlays, setActiveOverlays] = useState({
        sma: showSMA,
        bollinger: showBollinger,
        volume: showVolume,
    });
    const [showRSIPanel, setShowRSIPanel] = useState(showRSI);
    const [showMACDPanel, setShowMACDPanel] = useState(showMACD);
    const chartsRef = useRef<IChartApi[]>([]);

    const parseTime = (ts: string): Time => {
        const d = new Date(ts);
        return (d.getTime() / 1000) as Time;
    };

    useEffect(() => {
        if (!mainChartRef.current || data.length === 0) return;

        // Cleanup previous charts
        chartsRef.current.forEach(c => { try { c.remove(); } catch { /* ignore */ } });
        chartsRef.current = [];

        const chartOptions = {
            layout: {
                background: { type: ColorType.Solid as const, color: 'transparent' },
                textColor: 'rgba(255,255,255,0.6)',
                fontFamily: "'Inter', sans-serif",
                fontSize: 11,
            },
            grid: {
                vertLines: { color: 'rgba(255,255,255,0.04)' },
                horzLines: { color: 'rgba(255,255,255,0.04)' },
            },
            crosshair: {
                mode: CrosshairMode.Normal,
            },
            timeScale: {
                borderColor: 'rgba(255,255,255,0.08)',
                timeVisible: false,
                secondsVisible: false,
            },
            rightPriceScale: {
                borderColor: 'rgba(255,255,255,0.08)',
                scaleMargins: { top: 0.1, bottom: activeOverlays.volume ? 0.25 : 0.05 },
            },
            handleScroll: { vertTouchDrag: false },
        };

        // --- MAIN CHART ---
        const mainChart = createChart(mainChartRef.current, {
            ...chartOptions,
            width: mainChartRef.current.clientWidth,
            height: height,
        });
        chartsRef.current.push(mainChart);

        // Candlestick series (v5 API)
        const candleSeries = mainChart.addSeries(CandlestickSeries, {
            upColor: '#22c55e',
            downColor: '#ef4444',
            borderUpColor: '#22c55e',
            borderDownColor: '#ef4444',
            wickUpColor: '#22c55e',
            wickDownColor: '#ef4444',
        });

        const candleData = data.map(d => ({
            time: parseTime(d.timestamp),
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
        }));
        candleSeries.setData(candleData);

        // Volume histogram (overlaid at bottom)
        if (activeOverlays.volume) {
            const volumeSeries = mainChart.addSeries(HistogramSeries, {
                priceFormat: { type: 'volume' as const },
                priceScaleId: 'volume',
            });
            mainChart.priceScale('volume').applyOptions({
                scaleMargins: { top: 0.8, bottom: 0 },
            });
            const volData = data.map(d => ({
                time: parseTime(d.timestamp),
                value: d.volume || 0,
                color: d.close >= d.open ? 'rgba(34,197,94,0.25)' : 'rgba(239,68,68,0.25)',
            }));
            volumeSeries.setData(volData);
        }

        // SMA overlays
        if (activeOverlays.sma) {
            const sma50Data = data
                .filter(d => d.sma_50 && d.sma_50 > 0)
                .map(d => ({ time: parseTime(d.timestamp), value: d.sma_50! }));
            const sma200Data = data
                .filter(d => d.sma_200 && d.sma_200 > 0)
                .map(d => ({ time: parseTime(d.timestamp), value: d.sma_200! }));

            if (sma50Data.length > 0) {
                const sma50 = mainChart.addSeries(LineSeries, {
                    color: '#10b981',
                    lineWidth: 1,
                    title: 'SMA 50',
                    priceLineVisible: false,
                    lastValueVisible: false,
                });
                sma50.setData(sma50Data);
            }
            if (sma200Data.length > 0) {
                const sma200 = mainChart.addSeries(LineSeries, {
                    color: '#f59e0b',
                    lineWidth: 1,
                    lineStyle: 2,
                    title: 'SMA 200',
                    priceLineVisible: false,
                    lastValueVisible: false,
                });
                sma200.setData(sma200Data);
            }
        }

        // Bollinger Bands
        if (activeOverlays.bollinger) {
            const bbUpper = data
                .filter(d => d.bb_upper && d.bb_upper > 0)
                .map(d => ({ time: parseTime(d.timestamp), value: d.bb_upper! }));
            const bbLower = data
                .filter(d => d.bb_lower && d.bb_lower > 0)
                .map(d => ({ time: parseTime(d.timestamp), value: d.bb_lower! }));

            if (bbUpper.length > 0) {
                const upper = mainChart.addSeries(LineSeries, {
                    color: 'rgba(99,102,241,0.4)',
                    lineWidth: 1,
                    title: 'BB Upper',
                    priceLineVisible: false,
                    lastValueVisible: false,
                });
                upper.setData(bbUpper);
            }
            if (bbLower.length > 0) {
                const lower = mainChart.addSeries(LineSeries, {
                    color: 'rgba(99,102,241,0.4)',
                    lineWidth: 1,
                    title: 'BB Lower',
                    priceLineVisible: false,
                    lastValueVisible: false,
                });
                lower.setData(bbLower);
            }
        }

        mainChart.timeScale().fitContent();

        // --- RSI CHART ---
        if (showRSIPanel && rsiChartRef.current) {
            const rsiChart = createChart(rsiChartRef.current, {
                ...chartOptions,
                width: rsiChartRef.current.clientWidth,
                height: 150,
                rightPriceScale: {
                    borderColor: 'rgba(255,255,255,0.08)',
                    scaleMargins: { top: 0.1, bottom: 0.1 },
                },
            });
            chartsRef.current.push(rsiChart);

            const rsiSeries = rsiChart.addSeries(LineSeries, {
                color: '#8b5cf6',
                lineWidth: 2,
                title: 'RSI (14)',
                priceLineVisible: false,
            });

            const rsiData = data
                .filter(d => d.rsi !== undefined && d.rsi > 0)
                .map(d => ({ time: parseTime(d.timestamp), value: d.rsi! }));
            rsiSeries.setData(rsiData);

            // Overbought line
            const obLine = rsiChart.addSeries(LineSeries, {
                color: 'rgba(239,68,68,0.3)',
                lineWidth: 1,
                lineStyle: 2,
                priceLineVisible: false,
                lastValueVisible: false,
                title: '',
            });
            obLine.setData(rsiData.map(d => ({ ...d, value: 70 })));

            // Oversold line
            const osLine = rsiChart.addSeries(LineSeries, {
                color: 'rgba(34,197,94,0.3)',
                lineWidth: 1,
                lineStyle: 2,
                priceLineVisible: false,
                lastValueVisible: false,
                title: '',
            });
            osLine.setData(rsiData.map(d => ({ ...d, value: 30 })));

            rsiChart.timeScale().fitContent();

            // Sync time scales
            mainChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
                if (range) rsiChart.timeScale().setVisibleLogicalRange(range);
            });
            rsiChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
                if (range) mainChart.timeScale().setVisibleLogicalRange(range);
            });
        }

        // --- MACD CHART ---
        if (showMACDPanel && macdChartRef.current) {
            const macdChart = createChart(macdChartRef.current, {
                ...chartOptions,
                width: macdChartRef.current.clientWidth,
                height: 150,
                rightPriceScale: {
                    borderColor: 'rgba(255,255,255,0.08)',
                    scaleMargins: { top: 0.1, bottom: 0.1 },
                },
            });
            chartsRef.current.push(macdChart);

            // MACD Histogram
            const histSeries = macdChart.addSeries(HistogramSeries, {
                title: 'MACD Hist',
                priceLineVisible: false,
                lastValueVisible: false,
            });
            const histData = data
                .filter(d => d.macd_hist !== undefined)
                .map(d => ({
                    time: parseTime(d.timestamp),
                    value: d.macd_hist!,
                    color: d.macd_hist! >= 0 ? 'rgba(34,197,94,0.6)' : 'rgba(239,68,68,0.6)',
                }));
            histSeries.setData(histData);

            // MACD Line
            const macdLine = macdChart.addSeries(LineSeries, {
                color: '#06b6d4',
                lineWidth: 2,
                title: 'MACD',
                priceLineVisible: false,
                lastValueVisible: false,
            });
            const macdData = data
                .filter(d => d.macd !== undefined)
                .map(d => ({ time: parseTime(d.timestamp), value: d.macd! }));
            macdLine.setData(macdData);

            // Signal Line
            const signalLine = macdChart.addSeries(LineSeries, {
                color: '#f97316',
                lineWidth: 1,
                lineStyle: 2,
                title: 'Signal',
                priceLineVisible: false,
                lastValueVisible: false,
            });
            const sigData = data
                .filter(d => d.macd_signal !== undefined)
                .map(d => ({ time: parseTime(d.timestamp), value: d.macd_signal! }));
            signalLine.setData(sigData);

            macdChart.timeScale().fitContent();

            // Sync with main
            mainChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
                if (range) macdChart.timeScale().setVisibleLogicalRange(range);
            });
        }

        // Resize handler
        const handleResize = () => {
            chartsRef.current.forEach((chart, idx) => {
                const container = idx === 0 ? mainChartRef.current : idx === 1 ? rsiChartRef.current : macdChartRef.current;
                if (container) {
                    chart.applyOptions({ width: container.clientWidth });
                }
            });
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chartsRef.current.forEach(c => { try { c.remove(); } catch { /* ignore */ } });
            chartsRef.current = [];
        };
    }, [data, activeOverlays, showRSIPanel, showMACDPanel, height]);

    const btnStyle = (active: boolean, color = 'var(--accent-indigo)') => ({
        padding: '4px 10px',
        fontSize: '0.7rem',
        fontWeight: 500 as const,
        borderRadius: '6px',
        border: `1px solid ${active ? color : 'var(--border-subtle)'}`,
        background: active ? `${color}22` : 'transparent',
        color: active ? color : 'var(--text-muted)',
        cursor: 'pointer' as const,
        transition: 'all 0.15s',
    });

    return (
        <div>
            {/* Toolbar */}
            <div style={{
                display: 'flex',
                gap: '6px',
                marginBottom: '12px',
                flexWrap: 'wrap',
                alignItems: 'center',
            }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginRight: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Overlays:</span>
                <button style={btnStyle(activeOverlays.volume)} onClick={() => setActiveOverlays(p => ({ ...p, volume: !p.volume }))}>Volume</button>
                <button style={btnStyle(activeOverlays.sma)} onClick={() => setActiveOverlays(p => ({ ...p, sma: !p.sma }))}>SMA 50/200</button>
                <button style={btnStyle(activeOverlays.bollinger)} onClick={() => setActiveOverlays(p => ({ ...p, bollinger: !p.bollinger }))}>Bollinger</button>
                <div style={{ width: '1px', height: '16px', background: 'var(--border-subtle)', margin: '0 4px' }} />
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginRight: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Panels:</span>
                <button style={btnStyle(showRSIPanel, '#8b5cf6')} onClick={() => setShowRSIPanel(!showRSIPanel)}>RSI</button>
                <button style={btnStyle(showMACDPanel, '#06b6d4')} onClick={() => setShowMACDPanel(!showMACDPanel)}>MACD</button>
            </div>

            {/* Main Candlestick Chart */}
            <div
                ref={mainChartRef}
                style={{
                    borderRadius: '12px',
                    overflow: 'hidden',
                    border: '1px solid var(--border-subtle)',
                    background: 'rgba(0,0,0,0.15)',
                }}
            />

            {/* RSI Panel */}
            {showRSIPanel && (
                <div style={{ marginTop: '4px' }}>
                    <div
                        ref={rsiChartRef}
                        style={{
                            borderRadius: '8px',
                            overflow: 'hidden',
                            border: '1px solid var(--border-subtle)',
                            background: 'rgba(0,0,0,0.15)',
                        }}
                    />
                </div>
            )}

            {/* MACD Panel */}
            {showMACDPanel && (
                <div style={{ marginTop: '4px' }}>
                    <div
                        ref={macdChartRef}
                        style={{
                            borderRadius: '8px',
                            overflow: 'hidden',
                            border: '1px solid var(--border-subtle)',
                            background: 'rgba(0,0,0,0.15)',
                        }}
                    />
                </div>
            )}
        </div>
    );
};

export default AdvancedChart;
