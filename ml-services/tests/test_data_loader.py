import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import torch
from models.data_loader import TimeSeriesDataset

class TestDataLoader(unittest.TestCase):
    
    @patch('models.data_loader.pd.read_sql')
    @patch('models.data_loader.DBConnector')
    def test_load_data(self, mock_db_connector, mock_read_sql):
        # Mock DB
        mock_conn = MagicMock()
        mock_db_connector.return_value.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Mock DataFrames
        # Create enough data for seq_len=3 (just for test)
        dates = pd.date_range(start='2024-01-01', periods=10)
        df_prices = pd.DataFrame({
            'timestamp': dates,
            'close': np.linspace(100, 110, 10),
            'volume': np.random.rand(10) * 1000,
            'symbol': ['TEST'] * 10
        })
        # Empty indicators and sentiment for simplicity or mock them too
        df_indicators = pd.DataFrame({
             'timestamp': dates,
             'rsi_14': [50]*10, 'macd': [0]*10, 'macd_signal': [0]*10, 'adx': [20]*10, 
             'bb_upper': [110]*10, 'bb_lower': [90]*10
        })
        # Sentiment with timestamp but no rows (or some rows to test merge)
        df_sentiment = pd.DataFrame({
            'timestamp': dates,
            'sentiment_score': [0.5]*10
        })
        
        # read_sql is called 3 times. We need side_effect.
        mock_read_sql.side_effect = [df_prices, df_indicators, df_sentiment]
        
        # Initialize Dataset
        dataset = TimeSeriesDataset(symbol='TEST', seq_len=3, lookback_days=10)
        
        # Verify Length
        # 10 data points. seq_len=3. 
        # Sequences: [0,1,2] -> Target 3. [1,2,3] -> Target 4...
        # Last sequence: [6,7,8] -> Target 9. 
        # Index 9 is the last available data.
        # So we can create sequences up to index 6.
        # Total sequences = 10 - 3 = 7.
        self.assertEqual(len(dataset), 7)
        
        # Verify Item Shape
        X, y = dataset[0]
        # X shape should be (seq_len, num_features)
        # Features: close, volume, rsi, macd, sentiment_score (defaults to 0)
        # 5 features
        self.assertEqual(X.shape, (3, 5))
        self.assertEqual(y.shape, torch.Size([])) # Scalar target

if __name__ == '__main__':
    unittest.main()
