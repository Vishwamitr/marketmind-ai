from fastapi.testclient import TestClient
from api.main import app, limiter
from unittest.mock import patch, MagicMock
import pytest

# We need to mock the limiter storage or ensure it works with TestClient
# slowapi usually works fine with TestClient if remote_address is mocked or provided

client = TestClient(app)

def test_security_headers():
    response = client.get("/api/status")
    assert response.status_code == 200
    headers = response.headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    # assert headers["Strict-Transport-Security"] # Might only trigger on HTTPS or we check existence
    assert "Strict-Transport-Security" in headers

def test_rate_limiting():
    # Reset limiter state to avoid cross-test pollution
    limiter.reset()
    
    # Use a unique IP so we get a fresh rate limit bucket
    headers = {"X-Forwarded-For": "10.0.0.99"}
    
    # Mock DB to avoid errors when we pass rate limit check
    with patch("api.routers.auth.DBConnector") as mock_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None # User doesn't exist
        
        # Send 6 requests — first 5 should pass, 6th should be rate limited
        for i in range(6):
            response = client.post(
                "/api/auth/register",
                data={"username": f"ratelimit_user{i}", "password": "password"},
                headers=headers
            )
            if i < 5:
                assert response.status_code != 429, f"Request {i+1} was rate limited unexpectedly"
            else:
                assert response.status_code == 429, f"Request {i+1} should have been rate limited"

if __name__ == "__main__":
    test_security_headers()
    print("Headers OK")
    # Limiter state might persist, so run this second
    # Note: TestClient resets app per test session usually? 
    # slowapi has global state in limiter.
    test_rate_limiting()
    print("Rate Limiting OK")
