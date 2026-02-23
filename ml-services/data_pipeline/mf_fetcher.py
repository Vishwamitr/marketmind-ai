"""
Mutual Fund NAV Fetcher
Fetches NAV history for Indian mutual funds via yfinance.
"""
import yfinance as yf
import pandas as pd
import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from data_pipeline.db_connector import DBConnector
from data_pipeline.symbols import get_all_mf, get_mf_symbols

logger = logging.getLogger(__name__)


class MFNavFetcher:
    """Fetches and stores mutual fund NAV data."""

    def __init__(self):
        self.db = DBConnector()
        self._ensure_table()

    def _ensure_table(self):
        """Create mutual_fund_nav table if it doesn't exist."""
        query = """
            CREATE TABLE IF NOT EXISTS mutual_fund_nav (
                timestamp TIMESTAMPTZ NOT NULL,
                symbol VARCHAR(30) NOT NULL,
                fund_name VARCHAR(200),
                nav FLOAT NOT NULL,
                category VARCHAR(50),
                PRIMARY KEY (timestamp, symbol)
            );
            CREATE INDEX IF NOT EXISTS idx_mf_symbol ON mutual_fund_nav (symbol);
            CREATE INDEX IF NOT EXISTS idx_mf_category ON mutual_fund_nav (category);
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                conn.commit()
            logger.info("mutual_fund_nav table ready.")
        except Exception as e:
            logger.error(f"Failed to create MF table: {e}")

    def fetch_mf_nav(self, mf_info: dict, period: str = "1y"):
        """
        Fetch NAV history for a single mutual fund.

        Args:
            mf_info: dict with 'symbol', 'name', 'category'
            period: yfinance period string
        """
        symbol = mf_info["symbol"]
        name = mf_info.get("name", symbol)
        category = mf_info.get("category", "Unknown")

        logger.info(f"Fetching MF NAV for {name} ({symbol})...")
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if hist.empty:
                logger.warning(f"No NAV data for {symbol}")
                return False

            insert_query = """
                INSERT INTO mutual_fund_nav (timestamp, symbol, fund_name, nav, category)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (timestamp, symbol) DO UPDATE SET
                    nav = EXCLUDED.nav,
                    fund_name = EXCLUDED.fund_name,
                    category = EXCLUDED.category;
            """

            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    for index, row in hist.iterrows():
                        ts = index.to_pydatetime()
                        nav = float(row["Close"])
                        cur.execute(insert_query, (ts, symbol, name, nav, category))
                conn.commit()

            logger.info(f"Stored {len(hist)} NAV records for {name}")
            return True

        except Exception as e:
            logger.error(f"Error fetching MF {symbol}: {e}")
            return False

    def fetch_all_mf(self, period: str = "1y", max_workers: int = 3):
        """Fetch NAV data for all mutual funds in the universe."""
        all_mf = get_all_mf()
        total = len(all_mf)
        success = 0
        failed = []

        logger.info(f"Fetching {total} mutual funds, period={period}...")

        def _fetch_one(mf):
            ok = self.fetch_mf_nav(mf, period=period)
            return mf["symbol"], ok

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for i, mf in enumerate(all_mf):
                future = executor.submit(_fetch_one, mf)
                futures[future] = mf["symbol"]
                if (i + 1) % max_workers == 0:
                    time.sleep(0.5)

            for future in as_completed(futures):
                sym, ok = future.result()
                if ok:
                    success += 1
                else:
                    failed.append(sym)

        logger.info(f"MF fetch complete: {success}/{total} succeeded")
        if failed:
            logger.warning(f"Failed MFs: {failed}")
        return {"total": total, "success": success, "failed": failed}

    def get_latest_navs(self) -> list[dict]:
        """Get the latest NAV for all tracked mutual funds."""
        query = """
            SELECT DISTINCT ON (symbol) symbol, fund_name, nav, category, timestamp
            FROM mutual_fund_nav
            ORDER BY symbol, timestamp DESC;
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                return [
                    {
                        "symbol": r[0], "fund_name": r[1], "nav": r[2],
                        "category": r[3], "timestamp": r[4].isoformat()
                    }
                    for r in rows
                ]

    def get_nav_history(self, symbol: str, limit: int = 365) -> list[dict]:
        """Get NAV history for a specific fund."""
        query = """
            SELECT timestamp, nav FROM mutual_fund_nav
            WHERE symbol = %s ORDER BY timestamp DESC LIMIT %s;
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (symbol, limit))
                rows = cur.fetchall()
                return [
                    {"timestamp": r[0].isoformat(), "nav": r[1]}
                    for r in reversed(rows)
                ]


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    fetcher = MFNavFetcher()
    period = sys.argv[1] if len(sys.argv) > 1 else "6mo"
    fetcher.fetch_all_mf(period=period)
