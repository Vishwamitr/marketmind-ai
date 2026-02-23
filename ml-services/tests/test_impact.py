import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime
from analysis.impact_analyzer import ImpactAnalyzer

class TestImpactAnalyzer(unittest.TestCase):
    
    @patch('analysis.impact_analyzer.DBConnector')
    def test_process_event(self, mock_db_connector):
        analyzer = ImpactAnalyzer()
        
        # Mock DB Connection
        mock_conn = MagicMock()
        mock_db_connector.return_value.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Mock Price Data Return
        # T0: 100, T1: 105 (5% increase)
        mock_prices = pd.DataFrame({
            'timestamp': [datetime(2026, 2, 10, 12, 0), datetime(2026, 2, 11, 12, 0)],
            'close': [100.0, 105.0]
        })
        
        # Mock read_sql to return prices
        # First call is logic in _process_event which calls read_sql query for prices
        # We need to ensure we are mocking the right call if analyze_impact calls read_sql twice
        # But here we are testing _process_event directly or mocking the second call
        
        with patch('pandas.read_sql', return_value=mock_prices):
            # Test Input
            symbol = "TEST"
            event_date = datetime(2026, 2, 10, 12, 0)
            sentiment = 0.8 # Positive
            
            # We want to spy on _store_impact to see if it's called with correct calculation
            with patch.object(analyzer, '_store_impact') as mock_store:
                analyzer._process_event(symbol, event_date, sentiment)
                
                # Verification
                mock_store.assert_called_once()
                args = mock_store.call_args[0]
                # args: symbol, event_date, sentiment, p0, p1, change, label
                self.assertEqual(args[0], "TEST")
                self.assertEqual(args[3], 100.0) # p0
                self.assertEqual(args[4], 105.0) # p1
                self.assertAlmostEqual(args[5], 0.05) # 5% change
                self.assertEqual(args[6], "POSITIVE_CORRELATION")

if __name__ == '__main__':
    unittest.main()
