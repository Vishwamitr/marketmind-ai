from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Lazy-init to prevent module crash when DB is down
_regime_detector = None

def _get_regime_detector():
    global _regime_detector
    if _regime_detector is None:
        try:
            from analysis.regime_detector import RegimeDetector
            _regime_detector = RegimeDetector()
        except Exception:
            pass
    return _regime_detector

def _get_db_connection():
    from data_pipeline.db_connector import DBConnector
    return DBConnector.get_connection()


@router.get("/market/overview")
def get_market_overview():
    """
    Get an overview of ALL tracked stocks — latest price, daily change, and regime.
    Falls back to live yfinance data if the database is empty.
    """
    try:
        query = """
            WITH latest AS (
                SELECT DISTINCT ON (symbol) 
                    symbol, timestamp, open, high, low, close, volume
                FROM stock_prices
                ORDER BY symbol, timestamp DESC
            ),
            previous AS (
                SELECT DISTINCT ON (symbol)
                    symbol, close as prev_close
                FROM stock_prices
                WHERE timestamp < (SELECT MAX(timestamp) FROM stock_prices)
                ORDER BY symbol, timestamp DESC
            )
            SELECT 
                l.symbol, l.timestamp, l.open, l.high, l.low, l.close, l.volume,
                p.prev_close,
                CASE WHEN p.prev_close > 0 
                    THEN ROUND(((l.close - p.prev_close) / p.prev_close * 100)::numeric, 2) 
                    ELSE 0 
                END as change_pct
            FROM latest l
            LEFT JOIN previous p ON l.symbol = p.symbol
            ORDER BY l.symbol
        """
        with _get_db_connection() as conn:
            df = pd.read_sql(query, conn)

        if df.empty:
            # Fallback: fetch live data from yfinance for top stocks
            return _fetch_live_overview()

        # Add regime for each stock
        results = []
        for _, row in df.iterrows():
            try:
                detector = _get_regime_detector()
                if detector:
                    regime, metrics = detector.detect_regime(row['symbol'])
                    regime_value = regime.value
                else:
                    regime_value = "UNKNOWN"
            except Exception:
                regime_value = "UNKNOWN"

            results.append({
                "symbol": row['symbol'],
                "timestamp": row['timestamp'],
                "price": row['close'],
                "open": row['open'],
                "high": row['high'],
                "low": row['low'],
                "volume": int(row['volume']),
                "prev_close": row.get('prev_close'),
                "change_pct": float(row.get('change_pct', 0)),
                "regime": regime_value
            })

        return {"stocks": results, "count": len(results)}

    except Exception:
        # DB connection failed — use yfinance fallback
        try:
            return _fetch_live_overview()
        except Exception as e2:
            raise HTTPException(status_code=500, detail=str(e2))


def _fetch_live_overview():
    """Fetch live market data from yfinance for top NIFTY 50 stocks — fast batch download."""
    import yfinance as yf

    # Hardcoded top 15 NIFTY 50 by market cap (avoids import failures)
    TOP_STOCKS = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "HINDUNILVR", "BHARTIARTL", "SBIN", "ITC", "KOTAKBANK",
        "LT", "AXISBANK", "BAJFINANCE", "MARUTI", "TITAN",
    ]

    yf_tickers = [f"{s}.NS" for s in TOP_STOCKS]

    try:
        # Single batch download — much faster than per-ticker .info calls
        df = yf.download(
            tickers=yf_tickers,
            period="2d",
            group_by="ticker",
            progress=False,
            threads=True,
        )
    except Exception:
        return {"stocks": [], "count": 0, "live": True}

    results = []
    for sym, yf_sym in zip(TOP_STOCKS, yf_tickers):
        try:
            if len(yf_tickers) == 1:
                ticker_data = df
            else:
                ticker_data = df[yf_sym] if yf_sym in df.columns.get_level_values(0) else None
            if ticker_data is None or ticker_data.empty:
                continue

            # Drop NaN rows
            ticker_data = ticker_data.dropna(subset=["Close"])
            if ticker_data.empty:
                continue

            latest = ticker_data.iloc[-1]
            prev = ticker_data.iloc[-2] if len(ticker_data) >= 2 else latest

            price = float(latest["Close"])
            prev_close = float(prev["Close"])
            change_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0

            results.append({
                "symbol": sym,
                "timestamp": str(latest.name),
                "price": round(price, 2),
                "open": round(float(latest.get("Open", price)), 2),
                "high": round(float(latest.get("High", price)), 2),
                "low": round(float(latest.get("Low", price)), 2),
                "volume": int(latest.get("Volume", 0)) if not pd.isna(latest.get("Volume", 0)) else 0,
                "prev_close": round(prev_close, 2),
                "change_pct": change_pct,
                "regime": "UNKNOWN",
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["change_pct"], reverse=True)
    return {"stocks": results, "count": len(results), "live": True}


@router.get("/market/bulk")
def get_bulk_market_data(symbols: str = Query(..., description="Comma-separated symbols, e.g. INFY,TCS,RELIANCE")):
    """
    Get latest data for multiple stocks at once.
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if not symbol_list:
            raise HTTPException(status_code=400, detail="No symbols provided")
        if len(symbol_list) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 symbols per request")

        placeholders = ",".join(f"'{s}'" for s in symbol_list)
        query = f"""
            WITH latest AS (
                SELECT DISTINCT ON (symbol) 
                    symbol, timestamp, open, high, low, close, volume
                FROM stock_prices
                WHERE symbol IN ({placeholders})
                ORDER BY symbol, timestamp DESC
            )
            SELECT * FROM latest ORDER BY symbol
        """
        with _get_db_connection() as conn:
            df = pd.read_sql(query, conn)

        results = []
        found_symbols = set()
        for _, row in df.iterrows():
            found_symbols.add(row['symbol'])
            try:
                detector = _get_regime_detector()
                if detector:
                    regime, metrics = detector.detect_regime(row['symbol'])
                    regime_value = regime.value
                    adx = metrics.get('adx')
                    sma_200 = metrics.get('sma_200')
                else:
                    regime_value = "UNKNOWN"
                    adx = None
                    sma_200 = None
            except Exception:
                regime_value = "UNKNOWN"
                adx = None
                sma_200 = None

            results.append({
                "symbol": row['symbol'],
                "timestamp": row['timestamp'],
                "price": row['close'],
                "open": row['open'],
                "high": row['high'],
                "low": row['low'],
                "volume": int(row['volume']),
                "regime": regime_value,
                "adx": adx,
                "sma_200": sma_200
            })

        missing = [s for s in symbol_list if s not in found_symbols]

        return {
            "stocks": results,
            "count": len(results),
            "missing": missing
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/movers")
def get_top_movers(limit: int = 10):
    """
    Get top gainers and losers by daily percentage change.
    """
    try:
        query = f"""
            WITH latest AS (
                SELECT DISTINCT ON (symbol) 
                    symbol, timestamp, close, volume
                FROM stock_prices
                ORDER BY symbol, timestamp DESC
            ),
            previous AS (
                SELECT DISTINCT ON (symbol)
                    symbol, close as prev_close
                FROM stock_prices
                WHERE timestamp < (SELECT MAX(timestamp) FROM stock_prices)
                ORDER BY symbol, timestamp DESC
            )
            SELECT 
                l.symbol, l.close as price, l.volume, p.prev_close,
                CASE WHEN p.prev_close > 0 
                    THEN ((l.close - p.prev_close) / p.prev_close * 100) 
                    ELSE 0 
                END as change_pct
            FROM latest l
            JOIN previous p ON l.symbol = p.symbol
            WHERE p.prev_close > 0
            ORDER BY change_pct DESC
        """
        with _get_db_connection() as conn:
            df = pd.read_sql(query, conn)

        if df.empty:
            # Fallback: derive from live overview
            overview = _fetch_live_overview()
            stocks = overview.get("stocks", [])
            sorted_stocks = sorted(stocks, key=lambda x: x.get("change_pct", 0), reverse=True)
            gainers = [{"symbol": s["symbol"], "price": s["price"], "volume": s["volume"], "prev_close": s["prev_close"], "change_pct": s["change_pct"]} for s in sorted_stocks[:limit]]
            losers = [{"symbol": s["symbol"], "price": s["price"], "volume": s["volume"], "prev_close": s["prev_close"], "change_pct": s["change_pct"]} for s in sorted_stocks[-limit:]]
            losers.sort(key=lambda x: x["change_pct"])
            return {"gainers": gainers, "losers": losers, "total_stocks": len(stocks)}

        df['change_pct'] = df['change_pct'].round(2)

        gainers = df.head(limit).to_dict(orient='records')
        losers = df.tail(limit).sort_values('change_pct').to_dict(orient='records')

        return {
            "gainers": gainers,
            "losers": losers,
            "total_stocks": len(df)
        }

    except Exception:
        try:
            overview = _fetch_live_overview()
            stocks = overview.get("stocks", [])
            sorted_stocks = sorted(stocks, key=lambda x: x.get("change_pct", 0), reverse=True)
            gainers = [{"symbol": s["symbol"], "price": s["price"], "volume": s["volume"], "prev_close": s["prev_close"], "change_pct": s["change_pct"]} for s in sorted_stocks[:limit]]
            losers = [{"symbol": s["symbol"], "price": s["price"], "volume": s["volume"], "prev_close": s["prev_close"], "change_pct": s["change_pct"]} for s in sorted_stocks[-limit:]]
            losers.sort(key=lambda x: x["change_pct"])
            return {"gainers": gainers, "losers": losers, "total_stocks": len(stocks)}
        except Exception as e2:
            raise HTTPException(status_code=500, detail=str(e2))

@router.get("/market/latest/{symbol}")
def get_latest_market_data(symbol: str):
    """
    Get the latest price, indicators, and regime for a symbol.
    """
    try:
        # 1. Get Latest Price
        query_price = f"""
            SELECT timestamp, open, high, low, close, volume 
            FROM stock_prices 
            WHERE symbol = '{symbol}' 
            ORDER BY timestamp DESC LIMIT 1
        """
        with _get_db_connection() as conn:
            df_price = pd.read_sql(query_price, conn)
        
        if df_price.empty:
            raise HTTPException(status_code=404, detail="Symbol not found")
            
        latest_price = df_price.iloc[0].to_dict()
        
        # 2. Get Regime
        detector = _get_regime_detector()
        if detector:
            regime, metrics = detector.detect_regime(symbol)
        else:
            from types import SimpleNamespace
            regime = SimpleNamespace(value="UNKNOWN")
            metrics = {}
        
        # 3. Combine
        return {
            "symbol": symbol,
            "timestamp": latest_price['timestamp'],
            "price": latest_price['close'],
            "open": latest_price['open'],
            "high": latest_price['high'],
            "low": latest_price['low'],
            "volume": latest_price['volume'],
            "regime": regime.value,
            "adx": metrics.get('adx'),
            "sma_50": metrics.get('sma_50'),
            "sma_200": metrics.get('sma_200'),
            "atr": metrics.get('atr'),
            "reason": metrics.get('reason')
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/history/{symbol}")
def get_market_history(symbol: str, limit: int = 100):
    """
    Get historical price data for charting.
    """
    try:
        query = f"""
            SELECT sp.timestamp, sp.close, sp.volume, 
                   ti.sma_50, ti.sma_200, ti.rsi_14 as rsi, ti.macd, ti.macd_signal, 
                   (ti.macd - ti.macd_signal) as macd_hist, ti.adx, ti.atr
            FROM stock_prices sp
            LEFT JOIN technical_indicators ti ON sp.timestamp = ti.timestamp AND sp.symbol = ti.symbol
            WHERE sp.symbol = '{symbol}'
            ORDER BY sp.timestamp DESC
            LIMIT {limit}
        """
        
        with _get_db_connection() as conn:
            df = pd.read_sql(query, conn)
        
        # Sort by timestamp ascending for chart
        df = df.sort_values('timestamp')
        
        # Handle NaN
        df = df.fillna(0)
        
        return df.to_dict(orient='records')
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/anomalies")
def get_market_anomalies(symbol: Optional[str] = None, lookback: int = 60, limit: int = 50):
    """
    Detect market anomalies: volume spikes, price gaps, unusual range, sudden moves.
    Optionally filter by symbol.
    """
    try:
        from analysis.anomaly_detector import AnomalyDetector, detect_all_anomalies

        if symbol:
            detector = AnomalyDetector()
            anomalies = detector.detect_anomalies(symbol.strip().upper(), lookback)
        else:
            anomalies = detect_all_anomalies(lookback)

        # Limit results
        anomalies = anomalies[:limit]

        # Summary stats
        types = {}
        for a in anomalies:
            t = a["type"]
            types[t] = types.get(t, 0) + 1

        return {
            "anomalies": anomalies,
            "count": len(anomalies),
            "type_summary": types,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/candles/{symbol}")
def get_candles(
    symbol: str,
    interval: str = Query("1d", description="1d, 1wk, 1mo"),
    period: str = Query("1y", description="1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
):
    """
    Get OHLCV candlestick data with technical indicators for charting.
    Uses yfinance for live data — works for any NSE symbol.
    """
    import yfinance as yf
    import numpy as np

    valid_intervals = ["1d", "1wk", "1mo"]
    valid_periods = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]

    if interval not in valid_intervals:
        raise HTTPException(status_code=400, detail=f"Invalid interval. Use: {valid_intervals}")
    if period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Invalid period. Use: {valid_periods}")

    try:
        ticker = yf.Ticker(f"{symbol.upper()}.NS")
        df = ticker.history(period=period, interval=interval)

        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        df = df.reset_index()
        df = df.rename(columns={"Date": "timestamp", "Datetime": "timestamp"})

        # --- Technical Indicators ---
        close = df["Close"]

        # SMA 50 / 200
        df["sma_50"] = close.rolling(window=50).mean()
        df["sma_200"] = close.rolling(window=200).mean()

        # Bollinger Bands (20, 2)
        bb_sma = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        df["bb_upper"] = bb_sma + 2 * bb_std
        df["bb_lower"] = bb_sma - 2 * bb_std

        # RSI (14)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(window=14).mean()
        loss = (-delta.clip(upper=0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))

        # MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # ADX (14)
        try:
            high = df["High"]
            low = df["Low"]
            plus_dm = high.diff().clip(lower=0)
            minus_dm = (-low.diff()).clip(lower=0)
            tr = pd.concat([
                high - low,
                (high - close.shift()).abs(),
                (low - close.shift()).abs()
            ], axis=1).max(axis=1)
            atr14 = tr.rolling(14).mean()
            plus_di = 100 * (plus_dm.rolling(14).mean() / atr14)
            minus_di = 100 * (minus_dm.rolling(14).mean() / atr14)
            dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
            df["adx"] = dx.rolling(14).mean()
            df["atr"] = atr14
        except Exception:
            df["adx"] = 0
            df["atr"] = 0

        # Build response
        df = df.fillna(0)
        result = []
        for _, row in df.iterrows():
            result.append({
                "timestamp": str(row["timestamp"]),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row.get("Volume", 0)),
                "sma_50": round(float(row["sma_50"]), 2),
                "sma_200": round(float(row["sma_200"]), 2),
                "bb_upper": round(float(row["bb_upper"]), 2),
                "bb_lower": round(float(row["bb_lower"]), 2),
                "rsi": round(float(row["rsi"]), 2),
                "macd": round(float(row["macd"]), 2),
                "macd_signal": round(float(row["macd_signal"]), 2),
                "macd_hist": round(float(row["macd_hist"]), 2),
                "adx": round(float(row["adx"]), 2),
                "atr": round(float(row["atr"]), 2),
            })

        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "period": period,
            "count": len(result),
            "candles": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Stock Screener ──────────────────────────────────────────────────

SCREENER_UNIVERSE = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "BHARTIARTL", "SBIN", "KOTAKBANK",
    "LT", "AXISBANK", "BAJFINANCE", "MARUTI", "HCLTECH",
    "TITAN", "SUNPHARMA", "ASIANPAINT", "WIPRO", "ULTRACEMCO",
    "NESTLEIND", "TATAMOTORS", "TATASTEEL", "POWERGRID", "NTPC",
    "M&M", "JSWSTEEL", "ADANIENT", "TECHM", "DRREDDY",
]


def _calc_rsi(close_series, period: int = 14):
    """Calculate RSI from a close price series. O(n) time, O(n) space."""
    import numpy as np
    delta = close_series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    rsi_series = 100 - (100 / (1 + rs))
    val = rsi_series.iloc[-1] if not rsi_series.empty else 50
    return round(float(val), 1) if not np.isnan(val) else 50.0


@router.get("/market/screener")
def screen_stocks(
    min_price: float = Query(0, description="Minimum price"),
    max_price: float = Query(999999, description="Maximum price"),
    min_rsi: float = Query(0, description="Minimum RSI"),
    max_rsi: float = Query(100, description="Maximum RSI"),
    min_change: float = Query(-100, description="Minimum change %"),
    max_change: float = Query(100, description="Maximum change %"),
    sort_by: str = Query("change_pct", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc/desc"),
    limit: int = Query(30, description="Max results"),
):
    """Screen stocks — optimized with batch download. O(1) HTTP call instead of O(N)."""
    import yfinance as yf
    import numpy as np

    # Batch download: 1 HTTP call for all 30 stocks instead of 30 separate calls
    tickers = [f"{s}.NS" for s in SCREENER_UNIVERSE]
    try:
        data = yf.download(tickers, period="3mo", group_by="ticker", progress=False, threads=True)
    except Exception as e:
        logger.error(f"Batch screener download failed: {e}")
        return {"stocks": [], "total": 0, "universe_size": len(SCREENER_UNIVERSE)}

    results = []
    for symbol in SCREENER_UNIVERSE:
        try:
            ticker_sym = f"{symbol}.NS"
            # Extract per-ticker data from batch result
            if len(tickers) > 1:
                hist = data[ticker_sym] if ticker_sym in data.columns.get_level_values(0) else None
            else:
                hist = data

            if hist is None or hist.empty or len(hist) < 2:
                continue

            # Drop NaN rows for this ticker
            hist = hist.dropna(subset=["Close"])
            if len(hist) < 2:
                continue

            close = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2])
            change_pct = round(((close - prev_close) / prev_close) * 100, 2)

            rsi = _calc_rsi(hist["Close"])

            high_52w = round(float(hist["High"].max()), 2)
            low_52w = round(float(hist["Low"].min()), 2)
            volume = int(hist["Volume"].iloc[-1])
            avg_volume = int(hist["Volume"].mean())

            # Apply filters early to avoid unnecessary processing
            if close < min_price or close > max_price:
                continue
            if rsi < min_rsi or rsi > max_rsi:
                continue
            if change_pct < min_change or change_pct > max_change:
                continue

            results.append({
                "symbol": symbol,
                "price": round(close, 2),
                "change_pct": change_pct,
                "volume": volume,
                "avg_volume": avg_volume,
                "volume_ratio": round(volume / avg_volume, 2) if avg_volume > 0 else 0,
                "rsi": rsi,
                "high_52w": high_52w,
                "low_52w": low_52w,
                "from_52w_high": round(((close - high_52w) / high_52w) * 100, 1),
                "market_cap": 0,
                "market_cap_cr": 0,
            })

        except Exception as e:
            logger.debug(f"Screener skipped {symbol}: {e}")
            continue

    # Sort — O(n log n) where n is filtered results
    reverse = sort_order.lower() == "desc"
    results.sort(key=lambda x: x.get(sort_by, 0) or 0, reverse=reverse)

    return {
        "stocks": results[:limit],
        "total": len(results),
        "universe_size": len(SCREENER_UNIVERSE),
    }


# ── Market Hours & Global Indices (with TTL cache) ───────────────────

_market_hours_cache: dict = {"data": None, "ts": 0}
_MARKET_HOURS_TTL = 60  # seconds — avoid redundant yfinance calls

GLOBAL_INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "FTSE 100": "^FTSE",
    "DAX": "^GDAXI",
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
}


@router.get("/market/hours")
def get_market_hours():
    """Get NSE market status, global indices, and current IST time. TTL-cached for 60s."""
    from datetime import datetime, timezone, timedelta
    import time as _time
    import yfinance as yf

    # TTL cache: avoid 8 yfinance calls within 60s
    if _market_hours_cache["data"] and (_time.time() - _market_hours_cache["ts"]) < _MARKET_HOURS_TTL:
        return _market_hours_cache["data"]

    # IST = UTC+5:30
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    hour, minute = now.hour, now.minute
    weekday = now.weekday()  # 0=Mon, 6=Sun

    # NSE Market hours
    if weekday >= 5:
        status = "closed"
        status_label = "Weekend — Market Closed"
    elif hour < 9 or (hour == 9 and minute < 0):
        status = "closed"
        status_label = "Pre-Open Session at 9:00 AM IST"
    elif hour == 9 and minute < 15:
        status = "pre_market"
        status_label = "Pre-Open Session (9:00–9:15 AM IST)"
    elif (hour == 9 and minute >= 15) or (hour > 9 and hour < 15) or (hour == 15 and minute <= 30):
        status = "open"
        status_label = "Market Open (9:15 AM – 3:30 PM IST)"
    else:
        status = "closed"
        status_label = "Market Closed — Opens 9:15 AM IST"

    # Fetch global indices
    indices = []
    for name, ticker in GLOBAL_INDICES.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if hist is not None and len(hist) >= 2:
                current = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2])
                change = current - prev
                change_pct = (change / prev) * 100
                indices.append({
                    "name": name,
                    "ticker": ticker,
                    "value": round(current, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                })
            elif hist is not None and len(hist) == 1:
                indices.append({
                    "name": name, "ticker": ticker,
                    "value": round(float(hist["Close"].iloc[-1]), 2),
                    "change": 0, "change_pct": 0,
                })
        except Exception:
            continue

    result = {
        "status": status,
        "status_label": status_label,
        "ist_time": now.strftime("%Y-%m-%d %H:%M:%S IST"),
        "weekday": now.strftime("%A"),
        "indices": indices,
    }
    _market_hours_cache["data"] = result
    _market_hours_cache["ts"] = _time.time()
    return result
