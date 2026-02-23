import yfinance as yf
import pandas as pd
import logging
import json
from datetime import datetime, timedelta
from data_pipeline.db_connector import DBConnector
from analysis.indicators import TechnicalAnalysis
from analysis.patterns import PatternDetector

logger = logging.getLogger(__name__)

class StockFetcher:
    """Fetches stock data from external sources and stores it in the database."""

    def __init__(self):
        self.db = DBConnector()
        self.ta = TechnicalAnalysis()
        self.pd = PatternDetector()

    def fetch_historical(self, symbol: str, period: str = "max", interval: str = "1d"):
        """
        Fetch historical data for a given symbol using yfinance.
        
        Args:
            symbol (str): Stock symbol (e.g., 'RELIANCE.NS')
            period (str): Data period to download (default: 'max')
            interval (str): Data interval (default: '1d')
        """
        logger.info(f"Fetching historical data for {symbol}...")
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                logger.warning(f"No data found for {symbol}.")
                return

            # Calculate technical indicators
            hist = self.ta.calculate_all(hist)

            self._store_data(symbol, hist)
            logger.info(f"Successfully stored {len(hist)} records for {symbol}.")
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")

    def _store_data(self, symbol: str, data: pd.DataFrame):
        """
        Store fetched data into TimescaleDB.
        
        Args:
            symbol (str): Stock symbol
            data (pd.DataFrame): OHLCV data from yfinance
        """
        insert_query = """
            INSERT INTO stock_prices (timestamp, symbol, exchange, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """
        
        # Determine exchange from symbol suffix
        exchange = 'NSE' if symbol.endswith('.NS') else 'BSE' if symbol.endswith('.BO') else 'UNKNOWN'
        clean_symbol = symbol.replace('.NS', '').replace('.BO', '')

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                for index, row in data.iterrows():
                    # yfinance index is the timestamp
                    timestamp = index.to_pydatetime()
                    
                    cur.execute(insert_query, (
                        timestamp,
                        clean_symbol,
                        exchange,
                        float(row['Open']),
                        float(row['High']),
                        float(row['Low']),
                        float(row['Close']),
                        int(row['Volume'])
                    ))
                
                # Insert technical indicators
                if 'RSI_14' in data.columns:
                    indicators_query = """
                        INSERT INTO technical_indicators (
                            timestamp, symbol, rsi_14, macd, macd_signal, 
                            bb_upper, bb_middle, bb_lower, 
                            sma_20, sma_50, sma_200, 
                            ema_12, ema_26, adx, atr
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (timestamp, symbol) DO UPDATE SET
                            rsi_14 = EXCLUDED.rsi_14,
                            macd = EXCLUDED.macd,
                            macd_signal = EXCLUDED.macd_signal,
                            bb_upper = EXCLUDED.bb_upper,
                            bb_middle = EXCLUDED.bb_middle,
                            bb_lower = EXCLUDED.bb_lower,
                            sma_20 = EXCLUDED.sma_20,
                            sma_50 = EXCLUDED.sma_50,
                            sma_200 = EXCLUDED.sma_200,
                            ema_12 = EXCLUDED.ema_12,
                            ema_26 = EXCLUDED.ema_26,
                            adx = EXCLUDED.adx,
                            atr = EXCLUDED.atr;
                    """
                    
                    for index, row in data.iterrows():
                        timestamp = index.to_pydatetime()
                        # Helper to safely get float or None
                        def get_val(col):
                            val = row.get(col)
                            return float(val) if pd.notna(val) else None

                        cur.execute(indicators_query, (
                            timestamp,
                            clean_symbol,
                            get_val('RSI_14'),
                            get_val('MACD_12_26_9'),
                            get_val('MACDs_12_26_9'),
                            get_val('BBU_20_2.0') or get_val('BBU_20_2.0_2.0'),
                            get_val('BBM_20_2.0') or get_val('BBM_20_2.0_2.0'),
                            get_val('BBL_20_2.0') or get_val('BBL_20_2.0_2.0'),
                            get_val('SMA_20'),
                            get_val('SMA_50'),
                            get_val('SMA_200'),
                            get_val('EMA_12'),
                            get_val('EMA_26'),
                            get_val('ADX_14'),
                            get_val('ATR_14')
                        ))

                conn.commit()

                # Detect and store chart patterns
                patterns = self.pd.detect_patterns(data)
                if patterns:
                    patterns_query = """
                        INSERT INTO chart_patterns (symbol, pattern_type, confidence, start_time, end_time, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, pattern_type, start_time) DO NOTHING;
                    """
                    
                    with conn.cursor() as cur:
                        for p in patterns:
                            cur.execute(patterns_query, (
                                clean_symbol,
                                p['pattern_type'],
                                p['confidence'],
                                p['start_time'],
                                p['end_time'],
                                json.dumps(p['metadata'])
                            ))
                    conn.commit()
                    logger.info(f"Stored {len(patterns)} patterns for {symbol}.")

    def fetch_batch(self, symbols: list[str], period: str = "1mo",
                    max_workers: int = 5, delay: float = 0.3):
        """
        Fetch data for multiple symbols concurrently.

        Args:
            symbols: List of yfinance symbols (e.g. ['RELIANCE.NS', 'TCS.NS'])
            period: yfinance period string
            max_workers: Concurrent threads
            delay: Seconds between batch launches (rate limiting)
        """
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed

        total = len(symbols)
        success = 0
        failed = []

        logger.info(f"Starting batch fetch: {total} symbols, period={period}, workers={max_workers}")

        def _fetch_one(sym):
            try:
                self.fetch_historical(sym, period=period)
                return sym, True
            except Exception as e:
                logger.error(f"Batch fetch failed for {sym}: {e}")
                return sym, False

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for i, sym in enumerate(symbols):
                future = executor.submit(_fetch_one, sym)
                futures[future] = sym
                # Rate limit: pause every batch of workers
                if (i + 1) % max_workers == 0:
                    time.sleep(delay)

            for future in as_completed(futures):
                sym, ok = future.result()
                if ok:
                    success += 1
                else:
                    failed.append(sym)

                if (success + len(failed)) % 50 == 0:
                    logger.info(f"Progress: {success + len(failed)}/{total} "
                                f"(success={success}, failed={len(failed)})")

        logger.info(f"Batch fetch complete: {success}/{total} succeeded, "
                    f"{len(failed)} failed")
        if failed:
            logger.warning(f"Failed symbols: {failed[:20]}{'...' if len(failed) > 20 else ''}")
        return {"total": total, "success": success, "failed": failed}

    def fetch_all_stocks(self, period: str = "1mo", max_workers: int = 5):
        """Fetch data for the entire stock universe."""
        from data_pipeline.symbols import get_all_stocks, get_nse_suffix

        all_stocks = get_all_stocks()
        nse_symbols = [get_nse_suffix(s) for s in all_stocks]
        logger.info(f"Fetching all {len(nse_symbols)} stocks...")
        return self.fetch_batch(nse_symbols, period=period, max_workers=max_workers)


if __name__ == "__main__":
    import sys
    fetcher = StockFetcher()

    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        period = sys.argv[2] if len(sys.argv) > 2 else "1mo"
        fetcher.fetch_all_stocks(period=period)
    else:
        # Default: test single stock
        fetcher.fetch_historical("TCS.NS", period="1mo")

