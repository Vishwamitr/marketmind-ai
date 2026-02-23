import logging
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
from data_pipeline.db_connector import DBConnector
from analysis.regime_detector import RegimeDetector, MarketRegime

logger = logging.getLogger(__name__)

@dataclass
class MarketEvent:
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    indicators: dict
    sentiment: float
    regime: MarketRegime

class MarketSimulator:
    def __init__(self):
        self.db = DBConnector()
        self.regime_detector = RegimeDetector()

    def run_simulation(self, symbol: str, start_date: str, end_date: str):
        """
        Generator that yields MarketEvents for each timestep in the simulation period.
        """
        logger.info(f"Starting simulation for {symbol} from {start_date} to {end_date}...")
        
        # 1. Fetch Aligned Data
        # We need to join prices, indicators, and sentiment.
        # We perform a LEFT JOIN to ensure we have price data even if others are missing.
        
        query = f"""
            SELECT 
                p.timestamp, p.open, p.high, p.low, p.close, p.volume,
                i.rsi_14 as rsi, i.macd, i.macd_signal, i.bb_upper, i.bb_lower, i.sma_50, i.sma_200, i.adx, i.atr,
                s.sentiment_score as sentiment
            FROM stock_prices p
            LEFT JOIN technical_indicators i ON p.timestamp = i.timestamp AND p.symbol = i.symbol
            LEFT JOIN market_sentiment s ON p.timestamp = s.timestamp AND p.symbol = s.symbol
            WHERE p.symbol = '{symbol}'
            AND p.timestamp >= '{start_date}'
            AND p.timestamp <= '{end_date}'
            ORDER BY p.timestamp ASC
        """
        
        with self.db.get_connection() as conn:
            df = pd.read_sql(query, conn)
            
        if df.empty:
            logger.warning("No data found for simulation period.")
            return

        logger.info(f"Loaded {len(df)} records for simulation.")
        
        # 2. Iterate and Yield
        for index, row in df.iterrows():
            timestamp = row['timestamp']
            
            # Construct Indicator Dict
            # Handle None values gracefully
            indicators = {
                'rsi': row['rsi'] if pd.notna(row['rsi']) else 0,
                'macd': row['macd'] if pd.notna(row['macd']) else 0,
                'macd_signal': row['macd_signal'] if pd.notna(row['macd_signal']) else 0,
                'bb_upper': row['bb_upper'] if pd.notna(row['bb_upper']) else 0,
                'bb_lower': row['bb_lower'] if pd.notna(row['bb_lower']) else 0,
                'sma_50': row['sma_50'] if pd.notna(row['sma_50']) else 0,
                'sma_200': row['sma_200'] if pd.notna(row['sma_200']) else 0,
                'adx': row['adx'] if pd.notna(row['adx']) else 0,
                'atr': row['atr'] if pd.notna(row['atr']) else 0,
            }
            
            # Detect Regime
            # Ideally RegimeDetector should accept the current row data to avoid re-fetching, 
            # but our current implementation fetches history from DB.
            # To be efficient, we might want to refactor RegimeDetector later.
            # For now, let's call it as is (it will fetch 20 rows history from DB).
            regime, _ = self.regime_detector.detect_regime(date=timestamp)
            
            event = MarketEvent(
                timestamp=timestamp,
                symbol=symbol,
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
                indicators=indicators,
                sentiment=row['sentiment'] if pd.notna(row['sentiment']) else 0,
                regime=regime
            )
            
            yield event
