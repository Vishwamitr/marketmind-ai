import pandas as pd
import pandas_ta as ta
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class PatternDetector:
    """
    Detects candlestick and geometric chart patterns.
    """
    
    def detect_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect patterns in the provided OHLCV data.
        
        Args:
            data (pd.DataFrame): Dataframe with Open, High, Low, Close.
            
        Returns:
            List[Dict]: List of detected patterns.
        """
        if data.empty or len(data) < 5:
            return []
            
        patterns = []
        df = data.copy()

        # Calculate candle features
        df['body'] = abs(df['Close'] - df['Open'])
        df['upper_shadow'] = df['High'] - df[['Open', 'Close']].max(axis=1)
        df['lower_shadow'] = df[['Open', 'Close']].min(axis=1) - df['Low']
        df['range'] = df['High'] - df['Low']
        
        # Avoid division by zero
        df['range'] = df['range'].replace(0, 0.0001)

        # 1. Hammer / Hanging Man (Simple heuristic)
        # Small body, long lower shadow, small upper shadow
        # Condition: Lower shadow > 2 * body, Upper shadow < body
        is_hammer = (df['lower_shadow'] > 2 * df['body']) & \
                    (df['upper_shadow'] < df['body'])
        
        self._extract_custom_patterns(is_hammer, 'HAMMER', patterns, df)

        # 2. Bullish Engulfing
        # Previous candle red, current green
        # Current open < prev close, Current close > prev open
        prev_close = df['Close'].shift(1)
        prev_open = df['Open'].shift(1)
        
        is_bullish_engulfing = (prev_close < prev_open) & \
                               (df['Close'] > df['Open']) & \
                               (df['Open'] < prev_close) & \
                               (df['Close'] > prev_open)

        self._extract_custom_patterns(is_bullish_engulfing, 'BULLISH_ENGULFING', patterns, df)

        # 3. Bearish Engulfing
        is_bearish_engulfing = (prev_close > prev_open) & \
                               (df['Close'] < df['Open']) & \
                               (df['Open'] > prev_close) & \
                               (df['Close'] < prev_open)

        self._extract_custom_patterns(is_bearish_engulfing, 'BEARISH_ENGULFING', patterns, df)

        # 4. Doji (using pandas-ta if available, else custom)
        # Very small body relative to range
        is_doji = (df['body'] <= 0.1 * df['range'])
        self._extract_custom_patterns(is_doji, 'DOJI', patterns, df)

        return patterns

    def _extract_custom_patterns(self, mask: pd.Series, pattern_name: str, patterns_list: List, data: pd.DataFrame):
        """
        Helper to extract patterns from boolean mask.
        """
        if mask is None or mask.empty:
            return

        # Find true indices
        hits = mask[mask]
        
        for timestamp, _ in hits.items():
            confidence = 0.7 # heuristic for custom rules
            
            patterns_list.append({
                'pattern_type': pattern_name,
                'confidence': confidence,
                'start_time': timestamp,
                'end_time': timestamp,
                'metadata': {}
            })

if __name__ == "__main__":
    # Test stub
    pass
