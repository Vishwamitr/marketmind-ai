import logging
import pandas as pd
import hashlib
from datetime import datetime, timedelta
from data_pipeline.db_connector import DBConnector
from utils.config import Config

logger = logging.getLogger(__name__)

class ImpactAnalyzer:
    """
    Analyzes the impact of sentiment events on stock prices.
    """

    def __init__(self):
        self.db = DBConnector()

    def analyze_impact(self, symbol: str, lookback_days: int = 30):
        """
        Identify significant sentiment events and calculate subsequent price change.
        """
        logger.info(f"Analyzing impact for {symbol} over last {lookback_days} days...")
        
        # 1. Fetch High Sentiment Events
        events_query = """
            SELECT timestamp, sentiment_score 
            FROM market_sentiment 
            WHERE symbol = %s 
              AND timestamp > NOW() - INTERVAL '%s days'
              AND (sentiment_score > 0.5 OR sentiment_score < -0.5)
        """
        
        try:
            with self.db.get_connection() as conn:
                events_df = pd.read_sql(events_query, conn, params=(symbol, lookback_days))
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return

        if events_df.empty:
            logger.info("No significant sentiment events found.")
            return

        logger.info(f"Found {len(events_df)} significant events.")

        # 2. For each event, fetch price data
        for _, row in events_df.iterrows():
            event_date = row['timestamp']
            sentiment = row['sentiment_score']
            self._process_event(symbol, event_date, sentiment)

    def _process_event(self, symbol, event_date, sentiment):
        """
        Calculate price change for a single event.
        """
        # Define window: Price at event (Close of that day) vs Price 24h later (Close of next day)
        # Note: If event is today, we might not have 'next day' data.
        
        start_date = event_date
        end_date = event_date + timedelta(days=1)
        
        # Fetch prices
        prices_query = """
            SELECT timestamp, close 
            FROM stock_prices 
            WHERE symbol = %s 
              AND timestamp >= %s 
              AND timestamp <= %s + INTERVAL '2 days'
            ORDER BY timestamp ASC
        """
        
        try:
            with self.db.get_connection() as conn:
                prices_df = pd.read_sql(prices_query, conn, params=(symbol, start_date, start_date))
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            return

        # We need finding the closest price to event_date and event_date + 1 day
        if prices_df.empty:
            logger.warning(f"No price data found near {event_date}")
            return

        # T0: Price closest to event (or first available in window)
        # In this query, we fetched prices starting from event_date. 
        # So prices_df.iloc[0] is the first price AFTER or AT event_date.
        t0_row = prices_df.iloc[0]
        price_t0 = t0_row['close']
        t0_time = t0_row['timestamp']
        
        # T1: Next available price record (representing "next day" or "later")
        # We ensure T1 is strictly after T0
        future_prices = prices_df[prices_df['timestamp'] > t0_time]
        
        if future_prices.empty:
            logger.info(f"Not enough future data to calculate impact for event on {event_date}")
            return
            
        price_t1 = future_prices.iloc[0]['close']
        
        # Calculate Return
        pct_change = (price_t1 - price_t0) / price_t0
        
        # Determine Impact Label
        # If sentiment positive and price up -> Correlation
        # If sentiment positive and price down -> Divergence
        label = "NEUTRAL"
        if sentiment > 0 and pct_change > 0:
            label = "POSITIVE_CORRELATION"
        elif sentiment < 0 and pct_change < 0:
            label = "POSITIVE_CORRELATION"
        elif sentiment > 0 and pct_change < 0:
            label = "DIVERGENCE"
        elif sentiment < 0 and pct_change > 0:
            label = "DIVERGENCE"
            
        # Store Result
        self._store_impact(symbol, event_date, sentiment, price_t0, price_t1, pct_change, label)

    def _store_impact(self, symbol, event_date, sentiment, p0, p1, change, label):
        event_id = hashlib.sha256(f"{symbol}_{event_date}".encode()).hexdigest()
        
        query = """
            INSERT INTO event_impact (event_id, symbol, event_date, sentiment_score, price_at_event, price_after_24h, price_change_24h, impact_label)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO UPDATE SET
                price_change_24h = EXCLUDED.price_change_24h,
                impact_label = EXCLUDED.impact_label;
        """
        
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (
                        event_id, 
                        symbol, 
                        event_date, 
                        float(sentiment), 
                        float(p0), 
                        float(p1), 
                        float(change), 
                        label
                    ))
                conn.commit()
            logger.info(f"Stored impact for {symbol} on {event_date}: {label} ({change:.2%})")
        except Exception as e:
            logger.error(f"Error storing impact: {e}")

if __name__ == "__main__":
    analyzer = ImpactAnalyzer()
    # Test on persistent dummy data or INFY if available
    # For now, we likely don't have overlapping high sentiment AND price data for the same historical day for INFY
    # But we can try running it.
    analyzer.analyze_impact('INFY')
    analyzer.analyze_impact('MARKET') # Our dummy symbol
