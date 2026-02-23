import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from models.data_loader_tabular import TabularDataLoader

class TestTabularLoader(unittest.TestCase):
    
    @patch('models.data_loader_tabular.pd.read_sql')
    @patch('models.data_loader_tabular.DBConnector')
    def test_load_data_lags(self, mock_db_connector, mock_read_sql):
        # Mock DB
        mock_conn = MagicMock()
        mock_db_connector.return_value.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Create Dummy Data (10 days)
        dates = pd.date_range(start='2024-01-01', periods=10)
        df_prices = pd.DataFrame({
            'timestamp': dates,
            'close': np.linspace(100, 110, 10), # 100, 101.11, ... 110
            'volume': [1000]*10,
            'symbol': ['TEST'] * 10
        })
        # Empty indicators/sentiment
        df_indicators = pd.DataFrame({'timestamp': dates})
        df_sentiment = pd.DataFrame({'timestamp': dates})
        
        mock_read_sql.side_effect = [df_prices, df_indicators, df_sentiment]
        
        # Test Loader with Lags=2
        loader = TabularDataLoader(symbol='TEST', lags=2, lookback_days=10)
        X, y = loader.load_data()
        
        # Verify Shape
        # Original: 10 rows.
        # Lags=2: First 2 rows become NaNs (dropped). Last row's target is NaN (shifted -1). 
        # Total drops = max(lags, 1) if shift(-1) is used?
        # shift(1) -> 0 is NaN. shift(2) -> 0,1 is NaN.
        # shift(-1) -> last is NaN.
        # dropna() removes rows with ANY NaN.
        # So index 0, 1 are dropped (due to lags). Index 9 is dropped (due to target).
        # Remaining: indices 2 to 8. (7 rows).
        self.assertEqual(len(X), 7)
        self.assertEqual(len(y), 7)
        
        # Verify Columns
        # Base: close, volume (2)
        # Lags: 2 features * 2 lags = 4 columns.
        # Total features = 2 + 4 = 6.
        # Columns: close, volume, close_lag_1, volume_lag_1, close_lag_2, volume_lag_2
        self.assertEqual(X.shape[1], 6)
        
        # Verify Lag Logic
        # Row 2 (Date 2024-01-03):
        # close_lag_1 should be Row 1 Close
        # close_lag_2 should be Row 0 Close
        row_2 = X.iloc[0] # The first available row
        self.assertEqual(row_2['close_lag_1'], df_prices.iloc[1]['close'])
        self.assertEqual(row_2['close_lag_2'], df_prices.iloc[0]['close'])

if __name__ == '__main__':
    unittest.main()
