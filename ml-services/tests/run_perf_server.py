import uvicorn
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock DB and Mongo before importing app components that might use them at module level (if any)
# But mostly used in functions.

from api.main import app
from api.routers import stocks, news, auth
import pandas as pd
from api.auth_utils import get_password_hash

def start_mock_server():
    print("Starting Mock Server for Performance Testing...")

    # 1. Mock DBConnector for Auth (Login)
    # We need a mock connection that returns a user for 'testuser'
    mock_conn = MagicMock()
    # Mock Logic for Cursor
    class MockCursor:
        def __init__(self):
            self.result = None
            
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        
        def execute(self, query, params=None):
            if "SELECT username, password_hash" in query:
                pwd_hash = get_password_hash("testpassword")
                self.result = ("testuser", pwd_hash)
            elif "SELECT * FROM users" in query:
                self.result = None
            else:
                self.result = None
                
        def fetchone(self):
            return self.result

    mock_cursor_instance = MockCursor()
    mock_conn.cursor.return_value = mock_cursor_instance
    
    # Patch Auth DBConnector
    auth.DBConnector.get_connection = MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=mock_conn)))
    # Also patch the class itself if instantiated directly
    auth.DBConnector.__enter__ = MagicMock(return_value=mock_conn) # if used as context manager instance

    # Patch Auth DBConnector instantiated as class
    # In auth.py: with DBConnector() as conn:
    # So we need to mock the class constructor
    auth.DBConnector = MagicMock()
    auth.DBConnector.return_value.__enter__.return_value = mock_conn
    
    # 2. Mock Stocks DBConnector
    stocks_mock_conn = MagicMock()
    stocks.DBConnector.get_connection = MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=stocks_mock_conn)))
    
    # Mock pd.read_sql
    # Return dummy data for latest and history
    dummy_latest = pd.DataFrame([{
        "timestamp": "2023-10-27T10:00:00", "open": 150.0, "high": 155.0, "low": 149.0, "close": 153.0, "volume": 10000
    }])
    dummy_history = pd.DataFrame([{"timestamp": "2023-10-27", "close": 153.0}] * 50)
    
    def read_sql_side_effect(query, conn):
        if "LIMIT 1" in query: return dummy_latest
        return dummy_history
        
    stocks.pd.read_sql = MagicMock(side_effect=read_sql_side_effect)
    
    # Patch RegimeDetector to avoid calculation overhead/errors
    stocks.regime_detector.detect_regime = MagicMock(return_value={
        "regime": MagicMock(value="Bullish"), "confidence": 0.9, "details": {}
    })
    
    # 3. Mock News MongoConnector
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.news_articles = mock_collection
    news.MongoConnector.get_db = MagicMock(return_value=mock_db)
    
    # Mock Find
    mock_cursor = MagicMock()
    mock_collection.find.return_value.sort.return_value.limit.return_value = [{"title": "Mock News"}] * 10
    
    # Run Server
    # Disable Rate Limiter
    app.state.limiter.enabled = False

    # 4. Mock Portfolio DBConnector
    from api.routers import portfolio
    
    # Patch Portfolio DBConnector
    portfolio_mock_conn = MagicMock()
    # Mock context manager
    portfolio.DBConnector.get_connection = MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=portfolio_mock_conn)))
    
    # Mock pd.read_sql for Portfolio
    # We need to handle queries for portfolio_balance, holdings, and stock_prices
    dummy_balance = pd.DataFrame([{"id": 1, "cash": 10000.0}])
    dummy_holdings = pd.DataFrame([{"symbol": "AAPL", "quantity": 10, "avg_price": 150.0}])
    dummy_price = pd.DataFrame([{"close": 155.0}])
    
    # Re-define read_sql side effect to handle all
    original_stocks_read_sql = stocks.pd.read_sql # It was already a mock
    
    def unified_read_sql_side_effect(query, conn):
        if "portfolio_balance" in query: return dummy_balance
        if "holdings" in query: return dummy_holdings
        if "stock_prices" in query:
             if "LIMIT 1" in query: return dummy_latest # Includes close, open, high, low, volume, timestamp for both routers
             return dummy_history
        if "LIMIT 1" in query and "stock_prices" in query: return dummy_latest # Fallback for stocks router
        
        # Default fallback
        if "LIMIT 1" in query: return dummy_latest
        return dummy_history

    stocks.pd.read_sql.side_effect = unified_read_sql_side_effect
    portfolio.pd.read_sql = MagicMock(side_effect=unified_read_sql_side_effect)

    uvicorn.run(app, host="127.0.0.1", port=8005, log_level="warning")

if __name__ == "__main__":
    start_mock_server()
