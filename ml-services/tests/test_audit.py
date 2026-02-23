from fastapi.testclient import TestClient
from api.main import app
from unittest.mock import patch, MagicMock
import os
import json
import time

client = TestClient(app)

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "audit.jsonl")

def test_audit_login_success():
    # Clear log file if exists to start fresh
    if os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()

    with patch("api.routers.auth.DBConnector") as mock_db:
        with patch("api.routers.auth.verify_password") as mock_verify:
            # Mock DB Success
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_cursor.fetchone.return_value = ("testuser", "hashed")
            mock_verify.return_value = True
            
            response = client.post(
                "/api/auth/login",
                data={"username": "testuser", "password": "password"}
            )
            assert response.status_code == 200
            
            # Check Log
            time.sleep(0.1) # Yield to file writer
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()
                # We expect at least one LOGIN_ATTEMPT and maybe one HTTP_REQUEST (middleware)
                found_login = False
                found_http = False
                for line in lines:
                    log = json.loads(line)
                    if log["event_type"] == "LOGIN_ATTEMPT" and log["status"] == "SUCCESS":
                        found_login = True
                        assert log["user_id"] == "testuser"
                    if log["event_type"] == "HTTP_REQUEST":
                        found_http = True
                
                assert found_login, "Login success log not found"
                # Middleware logs POST requests
                assert found_http, "Middleware HTTP log not found"

def test_audit_login_failure():
    # Clear log
    open(LOG_FILE, 'w').close()
    
    with patch("api.routers.auth.DBConnector") as mock_db:
        # User not found
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None 
        
        response = client.post(
            "/api/auth/login",
            data={"username": "baduser", "password": "password"}
        )
        assert response.status_code == 401
        
        # Check Log
        time.sleep(0.1)
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
            found_failure = False
            for line in lines:
                log = json.loads(line)
                if log["event_type"] == "LOGIN_ATTEMPT" and log["status"] == "FAILURE":
                    found_failure = True
                    assert log["user_id"] == "baduser"
            
            assert found_failure, "Login failure log not found"

if __name__ == "__main__":
    test_audit_login_success()
    print("Audit Login Success OK")
    test_audit_login_failure()
    print("Audit Login Failure OK")
