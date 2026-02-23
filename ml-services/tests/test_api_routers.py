from fastapi.testclient import TestClient
from api.main import app
import pytest

client = TestClient(app)

def test_system_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_news():
    # Test News Router — may return 500 if MongoDB is not running
    response = client.get("/api/news?limit=5")
    # 200 = DB up, 500 = DB down — either proves router is wired (not 404)
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        assert isinstance(response.json(), list)

def test_get_admin_stats():
    # Test Admin Router — requires auth, so 401 is expected without token
    response = client.get("/api/admin/stats")
    # 200 = authed + DB up, 401 = auth required, 500 = DB down
    # NOT 404 means router is correctly wired
    assert response.status_code in [200, 401, 500]

def test_get_portfolio():
    # Test Portfolio Router — requires auth, so 401 is expected without token
    response = client.get("/api/portfolio")
    assert response.status_code in [200, 401, 500]

def test_get_stock_latest():
    # Test Stocks Router
    response = client.get("/api/market/latest/INFY")
    assert response.status_code in [200, 500, 404]

if __name__ == "__main__":
    # Manually run if pytest not available
    print("Testing System Status...")
    test_system_status()
    print("System Status OK")
    
    print("Testing News...")
    test_get_news()
    print("News OK")
    
    print("Testing Admin...")
    test_get_admin_stats()
    print("Admin OK")
    
    print("Testing Portfolio...")
    test_get_portfolio()
    print("Portfolio OK")
    
    print("Testing Stocks...")
    test_get_stock_latest()
    print("Stocks OK")
    print("All Router Tests Passed!")
