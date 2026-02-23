from fastapi.testclient import TestClient
from api.main import app
from unittest.mock import MagicMock, patch
from api.auth_utils import get_current_active_user, User
import pandas as pd
import pytest

client = TestClient(app)

# Helper: override auth dependency for protected routes
def override_auth():
    async def mock_get_user():
        return User(username="testuser", disabled=False)
    app.dependency_overrides[get_current_active_user] = mock_get_user

def cleanup_auth():
    app.dependency_overrides.pop(get_current_active_user, None)

def test_system_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("api.routers.news.MongoConnector")
def test_get_news(mock_mongo):
    # Setup Mock
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_mongo.get_db.return_value = mock_db
    mock_db.news_articles = mock_collection
    
    # Mock find().sort().limit()
    mock_cursor = MagicMock()
    mock_collection.find.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = [
        {"title": "Test News", "summary": "Summary", "published_at": "2023-01-01"}
    ]

    # Test
    response = client.get("/api/news?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test News"

@patch("api.routers.admin.psutil")
@patch("api.routers.admin.DBConnector")
@patch("api.routers.admin.MongoConnector")
def test_get_admin_stats(mock_mongo, mock_db_conn, mock_psutil):
    override_auth()
    try:
        # Mock System Stats
        mock_psutil.cpu_percent.return_value = 10.0
        mock_psutil.virtual_memory().percent = 20.0
        
        # Mock Postgres
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_conn.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [100] # Count return
        
        # Mock Mongo
        mock_mongo_db = MagicMock()
        mock_mongo.get_db.return_value = mock_mongo_db
        mock_mongo_db.news_articles.count_documents.return_value = 50
        mock_mongo_db.model_predictions.count_documents.return_value = 10
        mock_mongo_db.list_collection_names.return_value = []
        
        # Test
        response = client.get("/api/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["system"]["cpu"] == 10.0
        assert data["counts"]["news_articles"] == 50
    finally:
        cleanup_auth()

@patch("api.routers.portfolio.pd.read_sql")
@patch("api.routers.portfolio.DBConnector")
def test_get_portfolio(mock_db_conn, mock_read_sql):
    override_auth()
    try:
        # Mock Context Manager
        mock_conn = MagicMock()
        mock_db_conn.get_connection.return_value.__enter__.return_value = mock_conn
        
        df_cash = pd.DataFrame([{"id": 1, "cash": 50000.0}])
        df_holdings = pd.DataFrame([{"symbol": "INFY", "quantity": 10, "avg_price": 1000.0}])
        df_price = pd.DataFrame([{"close": 1200.0}])
        
        def side_effect(query, conn):
            if "portfolio_balance" in query:
                return df_cash
            if "holdings" in query:
                return df_holdings
            if "stock_prices" in query:
                return df_price
            return pd.DataFrame()
            
        mock_read_sql.side_effect = side_effect

        # Test
        response = client.get("/api/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert data["cash"] == 50000.0
        assert len(data["holdings"]) == 1
        assert data["holdings"][0]["current_price"] == 1200.0
    finally:
        cleanup_auth()

if __name__ == "__main__":
    pytest.main([__file__])
