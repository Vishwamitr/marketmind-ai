"""
Options Chain Fetcher
Fetches NSE options chain data (calls/puts) via yfinance.
"""
import yfinance as yf
import pandas as pd
import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from data_pipeline.db_connector import DBConnector
from data_pipeline.symbols import get_fno_stocks, get_nse_suffix

logger = logging.getLogger(__name__)


class OptionsFetcher:
    """Fetches and stores options chain data."""

    def __init__(self):
        self.db = DBConnector()
        self._ensure_table()

    def _ensure_table(self):
        """Create options_chain table if it doesn't exist."""
        query = """
            CREATE TABLE IF NOT EXISTS options_chain (
                fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                symbol VARCHAR(20) NOT NULL,
                expiry DATE NOT NULL,
                strike FLOAT NOT NULL,
                option_type VARCHAR(4) NOT NULL,
                last_price FLOAT,
                bid FLOAT,
                ask FLOAT,
                change_pct FLOAT,
                volume INT,
                open_interest INT,
                implied_volatility FLOAT,
                in_the_money BOOLEAN,
                PRIMARY KEY (fetched_at, symbol, expiry, strike, option_type)
            );
            CREATE INDEX IF NOT EXISTS idx_options_symbol ON options_chain (symbol);
            CREATE INDEX IF NOT EXISTS idx_options_expiry ON options_chain (symbol, expiry);
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                conn.commit()
            logger.info("options_chain table ready.")
        except Exception as e:
            logger.error(f"Failed to create options table: {e}")

    def fetch_options_chain(self, symbol: str) -> dict:
        """
        Fetch full options chain for a symbol.

        Args:
            symbol: Clean stock symbol (e.g. 'RELIANCE')
        Returns:
            dict with expiries, calls, puts counts
        """
        yf_symbol = get_nse_suffix(symbol)
        logger.info(f"Fetching options chain for {symbol} ({yf_symbol})...")

        try:
            ticker = yf.Ticker(yf_symbol)
            expiries = ticker.options  # Tuple of expiry date strings

            if not expiries:
                logger.warning(f"No options data for {symbol}")
                return {"symbol": symbol, "expiries": 0, "total_contracts": 0}

            now = datetime.utcnow()
            total_contracts = 0

            insert_query = """
                INSERT INTO options_chain (
                    fetched_at, symbol, expiry, strike, option_type,
                    last_price, bid, ask, change_pct, volume,
                    open_interest, implied_volatility, in_the_money
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (fetched_at, symbol, expiry, strike, option_type)
                DO UPDATE SET
                    last_price = EXCLUDED.last_price,
                    bid = EXCLUDED.bid,
                    ask = EXCLUDED.ask,
                    volume = EXCLUDED.volume,
                    open_interest = EXCLUDED.open_interest,
                    implied_volatility = EXCLUDED.implied_volatility;
            """

            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    for exp_str in expiries[:4]:  # Limit to nearest 4 expiries
                        try:
                            chain = ticker.option_chain(exp_str)
                            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()

                            # Process calls
                            for _, row in chain.calls.iterrows():
                                cur.execute(insert_query, (
                                    now, symbol, exp_date, float(row["strike"]), "CALL",
                                    _safe_float(row.get("lastPrice")),
                                    _safe_float(row.get("bid")),
                                    _safe_float(row.get("ask")),
                                    _safe_float(row.get("percentChange")),
                                    _safe_int(row.get("volume")),
                                    _safe_int(row.get("openInterest")),
                                    _safe_float(row.get("impliedVolatility")),
                                    bool(row.get("inTheMoney", False)),
                                ))
                                total_contracts += 1

                            # Process puts
                            for _, row in chain.puts.iterrows():
                                cur.execute(insert_query, (
                                    now, symbol, exp_date, float(row["strike"]), "PUT",
                                    _safe_float(row.get("lastPrice")),
                                    _safe_float(row.get("bid")),
                                    _safe_float(row.get("ask")),
                                    _safe_float(row.get("percentChange")),
                                    _safe_int(row.get("volume")),
                                    _safe_int(row.get("openInterest")),
                                    _safe_float(row.get("impliedVolatility")),
                                    bool(row.get("inTheMoney", False)),
                                ))
                                total_contracts += 1

                        except Exception as e:
                            logger.warning(f"Error processing expiry {exp_str} for {symbol}: {e}")
                            continue

                conn.commit()

            logger.info(f"Stored {total_contracts} option contracts for {symbol}")
            return {
                "symbol": symbol,
                "expiries": len(expiries),
                "total_contracts": total_contracts
            }

        except Exception as e:
            logger.error(f"Error fetching options for {symbol}: {e}")
            return {"symbol": symbol, "expiries": 0, "total_contracts": 0, "error": str(e)}

    def fetch_all_options(self, max_workers: int = 3):
        """Fetch options for all F&O eligible stocks."""
        fno_stocks = get_fno_stocks()
        total = len(fno_stocks)
        success = 0
        failed = []

        logger.info(f"Fetching options for {total} F&O stocks...")

        def _fetch_one(sym):
            result = self.fetch_options_chain(sym)
            return sym, result.get("total_contracts", 0) > 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for i, sym in enumerate(fno_stocks):
                future = executor.submit(_fetch_one, sym)
                futures[future] = sym
                if (i + 1) % max_workers == 0:
                    time.sleep(1.0)  # Heavier rate limit for options

            for future in as_completed(futures):
                sym, ok = future.result()
                if ok:
                    success += 1
                else:
                    failed.append(sym)

        logger.info(f"Options fetch complete: {success}/{total} succeeded")
        if failed:
            logger.warning(f"Failed F&O stocks: {failed}")
        return {"total": total, "success": success, "failed": failed}

    def get_chain(self, symbol: str, expiry: str = None) -> dict:
        """Get stored options chain for a symbol."""
        if expiry:
            query = """
                SELECT strike, option_type, last_price, bid, ask, volume,
                       open_interest, implied_volatility, in_the_money, change_pct
                FROM options_chain
                WHERE symbol = %s AND expiry = %s
                ORDER BY strike;
            """
            params = (symbol.upper(), expiry)
        else:
            # Get the nearest expiry
            query = """
                SELECT strike, option_type, last_price, bid, ask, volume,
                       open_interest, implied_volatility, in_the_money, change_pct
                FROM options_chain
                WHERE symbol = %s AND expiry = (
                    SELECT MIN(expiry) FROM options_chain
                    WHERE symbol = %s AND expiry >= CURRENT_DATE
                )
                ORDER BY strike;
            """
            params = (symbol.upper(), symbol.upper())

        calls = []
        puts = []

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                for r in cur.fetchall():
                    entry = {
                        "strike": r[0], "last_price": r[2], "bid": r[3],
                        "ask": r[4], "volume": r[5] or 0,
                        "open_interest": r[6] or 0,
                        "implied_volatility": round(r[7] * 100, 2) if r[7] else 0,
                        "in_the_money": r[8], "change_pct": r[9] or 0,
                    }
                    if r[1] == "CALL":
                        calls.append(entry)
                    else:
                        puts.append(entry)

        # Calculate put-call ratio
        total_call_oi = sum(c["open_interest"] for c in calls)
        total_put_oi = sum(p["open_interest"] for p in puts)
        pcr = round(total_put_oi / total_call_oi, 3) if total_call_oi > 0 else 0

        return {
            "symbol": symbol.upper(),
            "calls": calls,
            "puts": puts,
            "total_calls": len(calls),
            "total_puts": len(puts),
            "put_call_ratio": pcr,
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
        }

    def get_expiries(self, symbol: str) -> list[str]:
        """Get available expiry dates for a symbol."""
        query = """
            SELECT DISTINCT expiry FROM options_chain
            WHERE symbol = %s AND expiry >= CURRENT_DATE
            ORDER BY expiry;
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (symbol.upper(),))
                return [r[0].isoformat() for r in cur.fetchall()]


def _safe_float(val):
    """Safely convert to float, returning None for NaN/None."""
    if val is None:
        return None
    try:
        f = float(val)
        return f if pd.notna(f) else None
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    """Safely convert to int, returning None for NaN/None."""
    if val is None:
        return None
    try:
        f = float(val)
        return int(f) if pd.notna(f) else None
    except (ValueError, TypeError):
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetcher = OptionsFetcher()
    fetcher.fetch_all_options()
