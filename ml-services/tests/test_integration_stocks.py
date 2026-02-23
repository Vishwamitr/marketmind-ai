from fastapi.testclient import TestClient
from api.main import app
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

client = TestClient(app)

@patch("api.routers.stocks.pd.read_sql")
@patch("api.routers.stocks.regime_detector")
@patch("api.routers.stocks.DBConnector")
def test_get_latest_market_data(mock_db_connector, mock_regime_detector, mock_read_sql):
    # Mock DB Context Manager
    mock_conn = MagicMock()
    mock_db_connector.get_connection.return_value.__enter__.return_value = mock_conn
    
    # Mock DataFrame result for price
    mock_df = pd.DataFrame([{
        "timestamp": "2023-10-27T10:00:00",
        "open": 100.0,
        "high": 105.0,
        "low": 99.0,
        "close": 102.5,
        "volume": 1000
    }])
    mock_read_sql.return_value = mock_df
    
    # Mock Regime Detector — returns (MarketRegime, metrics_dict) tuple
    mock_regime = MagicMock(value="Bullish")
    mock_metrics = {"close": 102.5, "sma_200": 90, "adx": 25, "atr": 1.5, "reason": "Test"}
    mock_regime_detector.detect_regime.return_value = (mock_regime, mock_metrics)
    
    response = client.get("/api/market/latest/AAPL")
    
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["price"] == 102.5
    assert data["regime"] == "Bullish"
    assert data["adx"] == 25

@patch("api.routers.stocks.pd.read_sql")
@patch("api.routers.stocks.DBConnector")
def test_get_market_history(mock_db_connector, mock_read_sql):
    mock_conn = MagicMock()
    mock_db_connector.get_connection.return_value.__enter__.return_value = mock_conn
    
    # Mock DataFrame result
    mock_df = pd.DataFrame([
        {"timestamp": "2023-10-26", "close": 100.0, "volume": 500},
        {"timestamp": "2023-10-27", "close": 102.5, "volume": 1000}
    ])
    mock_read_sql.return_value = mock_df
    
    response = client.get("/api/market/history/AAPL?limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["close"] == 100.0
    assert data[1]["close"] == 102.5

@patch("api.routers.stocks.pd.read_sql")
@patch("api.routers.stocks.DBConnector")
def test_get_latest_market_data_not_found(mock_db_connector, mock_read_sql):
    mock_conn = MagicMock()
    mock_db_connector.get_connection.return_value.__enter__.return_value = mock_conn
    
    # Empty DataFrame
    mock_read_sql.return_value = pd.DataFrame()
    
    response = client.get("/api/market/latest/UNKNOWN")
    assert response.status_code == 404
