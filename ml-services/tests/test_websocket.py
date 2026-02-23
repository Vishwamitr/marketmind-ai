from fastapi.testclient import TestClient
from api.main import app
import pytest

client = TestClient(app)

def test_websocket_stocks():
    # Test connection to stock stream
    with client.websocket_connect("/ws/stocks/INFY") as websocket:
        # The background task might take up to 2s to send something, 
        # or we can send a "ping" and expect "pong" to verify connection immediately
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert data == "pong"
        
        # Optional: wait for a broadcast if we want to test simulation
        # data = websocket.receive_json()
        # assert data["type"] == "price_update"

def test_websocket_news():
    with client.websocket_connect("/ws/news") as websocket:
        # Just verify connection works
        assert websocket

if __name__ == "__main__":
    test_websocket_stocks()
    print("Stocks WS OK")
    test_websocket_news()
    print("News WS OK")
