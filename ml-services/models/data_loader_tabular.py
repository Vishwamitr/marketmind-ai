import logging
import pandas as pd
import numpy as np
from data_pipeline.db_connector import DBConnector
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

class TabularDataLoader:
    def __init__(self, symbol, lookback_days=365*2, lags=5):
        self.symbol = symbol
        self.lags = lags
        self.db = DBConnector()
        self.lookback_days = lookback_days

    def load_data(self):
        logger.info(f"Loading tabular data for {self.symbol}...")
        
        # 1. Fetch Price Data
        query_prices = f"""
            SELECT timestamp, close, volume 
            FROM stock_prices 
            WHERE symbol = '{self.symbol}' 
            AND timestamp > NOW() - INTERVAL '{self.lookback_days} days'
            ORDER BY timestamp ASC
        """
        
        # 2. Fetch Indicators
        query_indicators = f"""
            SELECT timestamp, rsi_14, macd, macd_signal, adx, bb_upper, bb_lower
            FROM technical_indicators
            WHERE symbol = '{self.symbol}'
            AND timestamp > NOW() - INTERVAL '{self.lookback_days} days'
            ORDER BY timestamp ASC
        """
        
        # 3. Fetch Sentiment
        query_sentiment = f"""
            SELECT timestamp, sentiment_score
            FROM market_sentiment
            WHERE symbol = '{self.symbol}'
            AND timestamp > NOW() - INTERVAL '{self.lookback_days} days'
            ORDER BY timestamp ASC
        """
        
        with self.db.get_connection() as conn:
            df_prices = pd.read_sql(query_prices, conn)
            df_indicators = pd.read_sql(query_indicators, conn)
            df_sentiment = pd.read_sql(query_sentiment, conn)
            
        if df_prices.empty:
            logger.warning("No price data found.")
            return None, None
            
        # Merge
        df = pd.merge(df_prices, df_indicators, on='timestamp', how='left')
        df = pd.merge(df, df_sentiment, on='timestamp', how='left')
        
        # Fill NaNs
        df = df.fillna(method='ffill').fillna(0)
        
        # Feature Engineering: Create Lags
        feature_cols = ['close', 'volume', 'rsi_14', 'macd', 'sentiment_score']
        available_features = [c for c in feature_cols if c in df.columns]
        
        df_lagged = df.copy()
        
        for col in available_features:
            for lag in range(1, self.lags + 1):
                df_lagged[f'{col}_lag_{lag}'] = df[col].shift(lag)
        
        # Target: Next Day Close
        df_lagged['target'] = df['close'].shift(-1)
        
        # Drop NaNs created by shifting
        df_lagged = df_lagged.dropna()
        
        # Set Timestamp as Index for alignment
        if 'timestamp' in df_lagged.columns:
            df_lagged.set_index('timestamp', inplace=True)
        
        # Select Features (Only lags + maybe current day features if we assume we have them at prediction time)
        # Usually for next day prediction, we use features up to T0 (current day). 
        # So we use 'close' (T0) and 'close_lag_1' (T-1), etc.
        # But 'close' is T0. 'target' is T+1. 
        # So X should include available_features + their lags.
        
        X_cols = available_features + [f'{c}_lag_{l}' for c in available_features for l in range(1, self.lags + 1)]
        
        X = df_lagged[X_cols]
        y = df_lagged['target']
        
        logger.info(f"Prepared data with {X.shape[1]} features and {len(X)} samples.")
        return X, y

    def get_train_val_split(self, test_size=0.2):
        X, y = self.load_data()
        if X is None:
            return None, None, None, None
            
        # Time-based split (no shuffling for time-series!)
        split_idx = int(len(X) * (1 - test_size))
        
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        
        return X_train, y_train, X_val, y_val
