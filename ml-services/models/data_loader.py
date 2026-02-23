import logging
import torch
import pandas as pd
import numpy as np
from torch.utils.data import Dataset
from sklearn.preprocessing import MinMaxScaler
from data_pipeline.db_connector import DBConnector

logger = logging.getLogger(__name__)

class TimeSeriesDataset(Dataset):
    def __init__(self, symbol, seq_len=60, lookback_days=365*2):
        self.symbol = symbol
        self.seq_len = seq_len
        self.db = DBConnector()
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        
        self.data, self.targets = self._load_data(lookback_days)

    def _load_data(self, lookback_days):
        logger.info(f"Loading data for {self.symbol}...")
        
        # 1. Fetch Price Data
        query_prices = f"""
            SELECT timestamp, close, volume 
            FROM stock_prices 
            WHERE symbol = '{self.symbol}' 
            AND timestamp > NOW() - INTERVAL '{lookback_days} days'
            ORDER BY timestamp ASC
        """
        
        # 2. Fetch Indicators (joined later or fetched separately? merged in pandas is easier)
        query_indicators = f"""
            SELECT timestamp, rsi_14, macd, macd_signal, adx, bb_upper, bb_lower
            FROM technical_indicators
            WHERE symbol = '{self.symbol}'
            AND timestamp > NOW() - INTERVAL '{lookback_days} days'
            ORDER BY timestamp ASC
        """
        
        # 3. Fetch Sentiment
        query_sentiment = f"""
            SELECT timestamp, sentiment_score
            FROM market_sentiment
            WHERE symbol = '{self.symbol}'
            AND timestamp > NOW() - INTERVAL '{lookback_days} days'
            ORDER BY timestamp ASC
        """
        
        with self.db.get_connection() as conn:
            df_prices = pd.read_sql(query_prices, conn)
            df_indicators = pd.read_sql(query_indicators, conn)
            df_sentiment = pd.read_sql(query_sentiment, conn)
            
        if df_prices.empty:
            logger.warning("No price data found.")
            return np.array([]), np.array([])
            
        # Merge DataFrames
        # Ensure timestamps are stripped of timezone or normalized if needed for merge
        # Timescale returns tz-aware. 
        
        df = pd.merge(df_prices, df_indicators, on='timestamp', how='left')
        df = pd.merge(df, df_sentiment, on='timestamp', how='left')
        
        # Fill NaNs
        df = df.fillna(method='ffill').fillna(0)
        
        # Set features
        # We want to predict Close price. 
        # Features: Close, Volume, RSI, MACD, etc.
        feature_cols = ['close', 'volume', 'rsi_14', 'macd', 'sentiment_score']
        
        # Check if columns exist (sentiment might be empty/missing if no news)
        existing_cols = [c for c in feature_cols if c in df.columns]
        
        data = df[existing_cols].values
        
        # Scale Data
        self.data_scaled = self.scaler.fit_transform(data)
        
        # Create Sequences
        X, y = [], []
        
        # Check if we have enough data
        if len(self.data_scaled) <= self.seq_len:
            logger.warning("Not enough data for sequence length.")
            return np.array([]), np.array([])
            
        for i in range(len(self.data_scaled) - self.seq_len):
            # Sequence of length seq_len
            X.append(self.data_scaled[i : i + self.seq_len])
            
            # Target: Close price (index 0) of the Next Day (i + seq_len)
            # We are predicting the 0-th column (Close)
            X_seq = self.data_scaled[i : i + self.seq_len]
            y_val = self.data_scaled[i + self.seq_len, 0] # 0 is Close
            
            y.append(y_val)
            
        return np.array(X), np.array(y)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return torch.tensor(self.data[idx], dtype=torch.float32), torch.tensor(self.targets[idx], dtype=torch.float32)

    def inverse_transform(self, y_scaled):
        # Helper to unscale predictions. 
        # y_scaled matches the 'feature_range' of scaler.
        # But scaler was fitted on N features. 
        # We need a dummy array to inverse transform if we only pass 1 column.
        
        # Create dummy array with same shape as input features
        n_features = self.scaler.n_features_in_
        dummy = np.zeros((len(y_scaled), n_features))
        
        # Fill 0-th column (Close) with predictions
        dummy[:, 0] = y_scaled.flatten()
        
        unscaled = self.scaler.inverse_transform(dummy)
        return unscaled[:, 0]
