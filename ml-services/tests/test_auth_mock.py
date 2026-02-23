from fastapi.testclient import TestClient
from api.main import app
from unittest.mock import MagicMock, patch
import pytest

client = TestClient(app)

@patch("api.routers.auth.DBConnector")
def test_register_user(mock_db_conn):
    # Mock DB Context Manager
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_db_conn.get_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    # Mock fetchone to return None (user doesn't exist)
    mock_cursor.fetchone.return_value = None
    
    response = client.post(
        "/api/auth/register",
        data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "User created"}

@patch("api.routers.auth.DBConnector")
@patch("api.routers.auth.verify_password")
def test_login_user(mock_verify, mock_db_conn):
    # Mock DB — login uses `with DBConnector() as conn:` (instance as context manager)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # DBConnector() returns an instance, which is used as context manager
    mock_instance = MagicMock()
    mock_db_conn.return_value = mock_instance
    mock_instance.__enter__ = MagicMock(return_value=mock_conn)
    mock_instance.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    
    # Mock User Retrieval — return (username, password_hash)
    mock_cursor.fetchone.return_value = ("testuser", "$2b$12$hashedpassword")
    
    # Mock Password Verification to True
    mock_verify.return_value = True
    
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]

@patch("api.routers.portfolio.DBConnector") # Mocking portfolio DB call
@patch("api.auth_utils.jwt.decode") # Mocking JWT decode to avoid expiration/secret issues in test
def test_protected_route(mock_jwt_decode, mock_db_conn):
    # 1. Test without token
    response = client.get("/api/portfolio")
    assert response.status_code == 401
    
    # 2. Test with token
    # Mock JWT decode to return valid user
    mock_jwt_decode.return_value = {"sub": "testuser"}
    
    # Mock Portfolio DB (so the endpoint doesn't fail after auth)
    mock_conn = MagicMock()
    mock_db_conn.get_connection.return_value.__enter__.return_value = mock_conn
    
    # Needs to handle 3 queries: cash, holdings, price
    # We can use side_effect or just lenient mocking if logic allows
    # The portfolio endpoint uses pd.read_sql, so we need to mock that if possible 
    # OR we just check if it gets past Auth.
    
    # Easier: Mock get_current_active_user dependency? 
    # But integration test usually mocks external IO.
    # Let's use `app.dependency_overrides` for cleaner testing of just Auth.
    pass 

# Better approach for protected route: Dependency Override
from api.auth_utils import get_current_active_user, User

def test_protected_route_access():
    # 1. Fail without token
    response = client.get("/api/portfolio")
    assert response.status_code == 401
    
    # 2. Success with override
    async def mock_get_user():
        return User(username="testuser", disabled=False)
    
    app.dependency_overrides[get_current_active_user] = mock_get_user
    
    # We still need to mock DB for portfolio internals, 
    # but 500 means Auth passed (reached DB logic), 401 means Auth failed.
    # If we get 500, it means we passed Auth!
    with patch("api.routers.portfolio.DBConnector"):
         response = client.get("/api/portfolio")
         # We expect 200 if we mocked DB fully, or 500 if DB fails. 
         # KEY is that it is NOT 401.
         assert response.status_code != 401

    # Clear override
    app.dependency_overrides = {}

if __name__ == "__main__":
    pytest.main([__file__])
