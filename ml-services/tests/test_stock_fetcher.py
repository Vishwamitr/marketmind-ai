import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from data_pipeline.stock_fetcher import StockFetcher

class TestStockFetcher(unittest.TestCase):

    def setUp(self):
        self.fetcher = StockFetcher()
        self.fetcher.db = MagicMock()

    @patch('yfinance.Ticker')
    def test_fetch_historical_success(self, mock_ticker):
        # Mock yfinance response
        mock_hist = pd.DataFrame({
            'Open': [100.0],
            'High': [110.0],
            'Low': [90.0],
            'Close': [105.0],
            'Volume': [1000]
        }, index=[pd.Timestamp('2023-01-01')])
        
        mock_ticker_instance = mock_ticker.return_value
        mock_ticker_instance.history.return_value = mock_hist

        # Run fetcher
        self.fetcher.fetch_historical('RELIANCE.NS')

        # Verify DB interaction
        self.fetcher.db.get_connection.assert_called()

    @patch('yfinance.Ticker')
    def test_fetch_historical_empty(self, mock_ticker):
        # Mock empty response
        mock_ticker_instance = mock_ticker.return_value
        mock_ticker_instance.history.return_value = pd.DataFrame()

        self.fetcher.fetch_historical('INVALID.NS')

        # Verify no DB interaction
        self.fetcher.db.get_connection.assert_not_called()

if __name__ == '__main__':
    unittest.main()
