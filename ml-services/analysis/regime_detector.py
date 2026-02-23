import logging
import pandas as pd
from data_pipeline.db_connector import DBConnector
from enum import Enum

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    BULLISH_TREND = "BULLISH_TREND"
    BEARISH_TREND = "BEARISH_TREND"
    SIDEWAYS = "SIDEWAYS"
    VOLATILE = "VOLATILE"
    UNKNOWN = "UNKNOWN"

class RegimeDetector:
    def __init__(self, symbol='INFY'):
        self.symbol = symbol
        self.db = DBConnector()

    def detect_regime(self, symbol=None, date=None):
        """
        Detect the market regime for the given date (default: today/latest).
        Returns: MarketRegime enum and a dictionary of metrics.
        """
        # 1. Fetch Data (Prices + Indicators)
        # We need SMA_50, SMA_200, ADX, ATR, and Close Price.
        # We need a small history to calculate "Moving Avg ATR" if not pre-calculated.
        # Let's fetch last 30 days to be safe for ATR avg, though DB might have it.
        # Assuming we just use the discrete values at 'date'.
        
        # Use provided symbol or fall back to instance default
        sym = symbol or self.symbol
        
        date_clause = f"<= '{date}'" if date else "<= NOW()"
        
        query = f"""
            SELECT 
                p.timestamp, p.close,
                i.sma_50, i.sma_200, i.adx, i.atr
            FROM stock_prices p
            LEFT JOIN technical_indicators i ON p.timestamp = i.timestamp
            WHERE p.symbol = '{sym}' 
            AND p.timestamp {date_clause}
            ORDER BY p.timestamp DESC
            LIMIT 20
        """
        
        with self.db.get_connection() as conn:
            df = pd.read_sql(query, conn)
            
        if df.empty:
            logger.warning("No data found for regime detection.")
            return MarketRegime.UNKNOWN, {}

        # Latest Data
        current = df.iloc[0]
        
        # Metrics
        close = current['close']
        sma_50 = current['sma_50'] if current['sma_50'] else 0
        sma_200 = current['sma_200'] if current['sma_200'] else 0
        adx = current['adx'] if current['adx'] else 0
        atr = current['atr'] if current['atr'] else 0
        
        # Calculate ATR Moving Average (Historical Volatility Baseline)
        avg_atr = df['atr'].mean() if 'atr' in df else 0
        
        regime = MarketRegime.SIDEWAYS # Default
        reasons = []

        # Logic
        # 1. Volatile Check (Override or Tag?) 
        # Let's make it a primary state if volatility is extreme, effectively 'Unsafe'.
        if atr > 1.5 * avg_atr and avg_atr > 0:
            regime = MarketRegime.VOLATILE
            reasons.append(f"ATR ({atr:.2f}) > 1.5x Avg ({avg_atr:.2f})")
        
        # 2. Trend Check
        elif adx > 25:
            # Strong Trend
            if close > sma_200:
                 regime = MarketRegime.BULLISH_TREND
                 reasons.append(f"Price > SMA200 & ADX ({adx:.2f}) > 25")
            elif close < sma_200:
                 regime = MarketRegime.BEARISH_TREND
                 reasons.append(f"Price < SMA200 & ADX ({adx:.2f}) > 25")
        
        else:
            # Sideways / Weak Trend
            regime = MarketRegime.SIDEWAYS
            reasons.append(f"ADX ({adx:.2f}) < 25 or Indeterminate")
            
        metrics = {
            "close": close,
            "sma_200": sma_200,
            "adx": adx,
            "atr": atr,
            "avg_atr": avg_atr,
            "reason": "; ".join(reasons)
        }
        
        logger.info(f"Detected Regime: {regime.value} | {metrics['reason']}")
        return regime, metrics
