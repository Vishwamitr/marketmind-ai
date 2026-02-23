from fastapi.testclient import TestClient
from api.main import app
from unittest.mock import patch, MagicMock
import pytest

client = TestClient(app)

@patch("api.routers.news.MongoConnector")
def test_get_news(mock_mongo):
    # Mock DB and Collection
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_mongo.get_db.return_value = mock_db
    mock_db.news_articles = mock_collection
    
    # Mock Find Cursor
    mock_cursor = MagicMock()
    mock_collection.find.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    
    # Mock Data
    mock_articles = [
        {"title": "News 1", "summary": "Summary 1", "published_at": "2023-10-27"},
        {"title": "News 2", "summary": "Summary 2", "published_at": "2023-10-26"}
    ]
    mock_cursor.__iter__.return_value = iter(mock_articles)
    
    response = client.get("/api/news?symbol=AAPL")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "News 1"

@patch("api.routers.news.MongoConnector")
def test_get_sentiment_trend(mock_mongo):
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_mongo.get_db.return_value = mock_db
    mock_db.news_articles = mock_collection
    
    # Mock Aggregate Result
    mock_trend = [
        {"_id": "2023-10-27", "avg_score": 0.8, "count": 10, "positive_count": 8, "negative_count": 2},
        {"_id": "2023-10-26", "avg_score": -0.2, "count": 5, "positive_count": 1, "negative_count": 4}
    ]
    mock_collection.aggregate.return_value = mock_trend
    
    response = client.get("/api/news/sentiment_trend?symbol=AAPL")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["avg_score"] == 0.8
