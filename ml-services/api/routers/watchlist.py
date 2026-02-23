"""
Watchlist API — Server-side watchlist stored in PostgreSQL.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
import logging
import pandas as pd
from data_pipeline.db_connector import DBConnector
from data_pipeline.symbols import (
    NIFTY_50, NIFTY_NEXT_50, NIFTY_MIDCAP_150,
    NIFTY_SMALLCAP_250, OTHER_NSE, get_all_stocks
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Pre-build a lookup for symbol → index category (done once at import)
_SYMBOL_INDEX: dict[str, str] = {}
for _sym in NIFTY_50:
    _SYMBOL_INDEX[_sym] = "NIFTY 50"
for _sym in NIFTY_NEXT_50:
    if _sym not in _SYMBOL_INDEX:
        _SYMBOL_INDEX[_sym] = "NIFTY Next 50"
for _sym in NIFTY_MIDCAP_150:
    if _sym not in _SYMBOL_INDEX:
        _SYMBOL_INDEX[_sym] = "MidCap 150"
for _sym in NIFTY_SMALLCAP_250:
    if _sym not in _SYMBOL_INDEX:
        _SYMBOL_INDEX[_sym] = "SmallCap 250"
for _sym in OTHER_NSE:
    if _sym not in _SYMBOL_INDEX:
        _SYMBOL_INDEX[_sym] = "Other NSE"

_ALL_SYMBOLS = get_all_stocks()  # sorted, deduplicated


@router.get("/watchlist/search")
def search_symbols(q: str = Query("", min_length=1, max_length=20)):
    """Search stock symbols by prefix. Returns top 10 matches."""
    query = q.strip().upper()
    if not query:
        return {"results": []}

    matches = []
    for sym in _ALL_SYMBOLS:
        if sym.startswith(query):
            matches.append({
                "symbol": sym,
                "index": _SYMBOL_INDEX.get(sym, "NSE"),
            })
            if len(matches) >= 10:
                break

    return {"results": matches, "query": query}


class WatchlistItem(BaseModel):
    symbol: str


# --- Bootstrap: create table if not exists ---
def _ensure_watchlist_table():
    """Create the watchlist table if it doesn't exist."""
    query = """
        CREATE TABLE IF NOT EXISTS watchlist (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL UNIQUE,
            added_at TIMESTAMPTZ DEFAULT NOW()
        );
    """
    try:
        DBConnector.execute_query(query)
    except Exception as e:
        logger.warning(f"Could not create watchlist table (may already exist): {e}")


_ensure_watchlist_table()


@router.get("/watchlist")
def get_watchlist():
    """Get all symbols in the watchlist."""
    try:
        query = "SELECT symbol, added_at FROM watchlist ORDER BY added_at DESC"
        with DBConnector.get_connection() as conn:
            df = pd.read_sql(query, conn)
        return {
            "symbols": df["symbol"].tolist(),
            "items": df.to_dict(orient="records"),
            "count": len(df),
        }
    except Exception as e:
        logger.error(f"Failed to get watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist")
def add_to_watchlist(item: WatchlistItem):
    """Add a stock symbol to the watchlist and auto-fetch its data."""
    symbol = item.symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol cannot be empty")

    try:
        query = """
            INSERT INTO watchlist (symbol) VALUES (%s)
            ON CONFLICT (symbol) DO NOTHING
            RETURNING id;
        """
        with DBConnector.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (symbol,))
                result = cur.fetchone()
                conn.commit()

        # Check if stock data exists, if not auto-fetch it
        data_status = "exists"
        try:
            check_query = """
                SELECT COUNT(*) FROM stock_prices WHERE symbol = %s
            """
            with DBConnector.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(check_query, (symbol,))
                    count = cur.fetchone()[0]

            if count == 0:
                # Auto-fetch 1 month of data so it's immediately available
                logger.info(f"Auto-fetching data for new watchlist symbol: {symbol}")
                from data_pipeline.stock_fetcher import StockFetcher
                fetcher = StockFetcher()
                yf_symbol = f"{symbol}.NS"
                fetcher.fetch_historical(yf_symbol, period="1mo")
                data_status = "fetched"
                logger.info(f"Auto-fetch complete for {symbol}")
        except Exception as fetch_err:
            logger.warning(f"Auto-fetch failed for {symbol}: {fetch_err}")
            data_status = "fetch_failed"

        if result:
            return {"message": f"{symbol} added to watchlist", "id": result[0], "data_status": data_status}
        else:
            return {"message": f"{symbol} is already in watchlist", "data_status": data_status}
    except Exception as e:
        logger.error(f"Failed to add to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{symbol}")
def remove_from_watchlist(symbol: str):
    """Remove a stock symbol from the watchlist."""
    symbol = symbol.strip().upper()
    try:
        query = "DELETE FROM watchlist WHERE symbol = %s RETURNING symbol;"
        with DBConnector.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (symbol,))
                result = cur.fetchone()
                conn.commit()
                if result:
                    return {"message": f"{symbol} removed from watchlist"}
                else:
                    raise HTTPException(status_code=404, detail=f"{symbol} not found in watchlist")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist/data")
def get_watchlist_with_data():
    """Get watchlist symbols with live market data — fast batch download."""
    try:
        # Get watchlist symbols
        wl_query = "SELECT symbol FROM watchlist ORDER BY added_at DESC"
        with DBConnector.get_connection() as conn:
            wl_df = pd.read_sql(wl_query, conn)

        if wl_df.empty:
            return {"stocks": [], "count": 0, "missing": []}

        symbols = wl_df["symbol"].tolist()
        yf_tickers = [f"{s}.NS" for s in symbols]

        # Fast batch download — 1 HTTP call for all symbols
        import yfinance as yf
        try:
            df = yf.download(
                tickers=yf_tickers,
                period="2d",
                group_by="ticker",
                progress=False,
                threads=True,
            )
        except Exception as e:
            logger.warning(f"yf.download failed: {e}")
            return {"stocks": [], "count": 0, "missing": symbols}

        results = []
        missing = []

        for sym, yf_sym in zip(symbols, yf_tickers):
            try:
                if len(yf_tickers) == 1:
                    ticker_data = df
                else:
                    ticker_data = df[yf_sym] if yf_sym in df.columns.get_level_values(0) else None

                if ticker_data is None or ticker_data.empty:
                    missing.append(sym)
                    continue

                ticker_data = ticker_data.dropna(subset=["Close"])
                if ticker_data.empty:
                    missing.append(sym)
                    continue

                latest = ticker_data.iloc[-1]
                prev = ticker_data.iloc[-2] if len(ticker_data) >= 2 else latest

                price = float(latest["Close"])
                prev_close = float(prev["Close"])
                change = round(price - prev_close, 2)
                change_pct = round(change / prev_close * 100, 2) if prev_close else 0

                entry = {
                    "symbol": sym,
                    "price": round(price, 2),
                    "change": change,
                    "change_pct": change_pct,
                    "open": round(float(latest.get("Open", price)), 2),
                    "high": round(float(latest.get("High", price)), 2),
                    "low": round(float(latest.get("Low", price)), 2),
                    "volume": int(latest.get("Volume", 0)) if not pd.isna(latest.get("Volume", 0)) else 0,
                    "name": sym,
                    "regime": "Unknown",
                    "adx": None,
                    "sma_200": None,
                    "atr": None,
                    "timestamp": str(latest.name),
                }

                # Try getting the full name from yfinance (fast_info is quicker than info)
                try:
                    fast = yf.Ticker(yf_sym).fast_info
                    # fast_info doesn't have name, skip
                except Exception:
                    pass

                # Try regime detection from DB if data exists
                try:
                    from analysis.regime_detector import RegimeDetector
                    detector = RegimeDetector()
                    regime, metrics = detector.detect_regime(sym)
                    entry["regime"] = regime.value
                    entry["adx"] = metrics.get("adx")
                    entry["sma_200"] = metrics.get("sma_200")
                    entry["atr"] = metrics.get("atr")
                except Exception:
                    pass

                results.append(entry)
            except Exception as e:
                logger.warning(f"Failed to process {sym}: {e}")
                missing.append(sym)

        # Fallback: try individual fetch for symbols that batch download missed
        # (yfinance batch can be flaky for some valid tickers)
        if missing:
            import yfinance as yf
            for sym in list(missing):
                try:
                    yf_sym = f"{sym}.NS"
                    t = yf.Ticker(yf_sym)
                    hist = t.history(period="2d")
                    if hist is not None and not hist.empty:
                        hist = hist.dropna(subset=["Close"])
                        if not hist.empty:
                            latest = hist.iloc[-1]
                            prev = hist.iloc[-2] if len(hist) >= 2 else latest
                            price = float(latest["Close"])
                            prev_close = float(prev["Close"])
                            change = round(price - prev_close, 2)
                            change_pct = round(change / prev_close * 100, 2) if prev_close else 0
                            results.append({
                                "symbol": sym,
                                "price": round(price, 2),
                                "change": change,
                                "change_pct": change_pct,
                                "open": round(float(latest.get("Open", price)), 2),
                                "high": round(float(latest.get("High", price)), 2),
                                "low": round(float(latest.get("Low", price)), 2),
                                "volume": int(latest.get("Volume", 0)) if not pd.isna(latest.get("Volume", 0)) else 0,
                                "name": sym,
                                "regime": "Unknown",
                                "adx": None,
                                "sma_200": None,
                                "atr": None,
                                "timestamp": str(latest.name),
                            })
                            missing.remove(sym)
                except Exception:
                    pass

        return {"stocks": results, "count": len(results), "missing": []}

    except Exception as e:
        logger.error(f"Failed to get watchlist data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
