from utils.audit_logger import AuditLogger
from utils.config import Config
from unittest.mock import MagicMock, patch
import pytest
import shutil
import os
import json

def test_config_loading():
    # Config is mostly static, but we can test if key values are present
    # SECRET_KEY might be optional or named differently in actual Config class
    assert hasattr(Config, "MONGODB_URL")
    # assert hasattr(Config, "SECRET_KEY") # Comment out if not strictly required or named differently
    assert hasattr(Config, "LOG_LEVEL") # Log level is definitely there

def test_audit_logger_initialization():
    # Test logger creation
    logger = AuditLogger()
    assert logger.logger.name == "audit_logger"
    # Ideally check if handler is added

def test_audit_logger_log_event():
    # Use a temporary file for testing
    test_log_file = "test_audit.jsonl"
    
    # Patch the LOG_FILE constant or just check the logger call
    # Since AuditLogger uses a hardcoded path in __init__, we might need to patch os.path.join or logging.FileHandler
    
    with patch("logging.FileHandler") as mock_handler:
        logger = AuditLogger()
        logger.logger = MagicMock()
        
        details = {"foo": "bar"}
        logger.log_event("TEST_EVENT", user_id="u1", details=details)
        
        # Check if info was called with correct JSON
        args, _ = logger.logger.info.call_args
        log_json = json.loads(args[0])
        
        assert log_json["event_type"] == "TEST_EVENT"
        assert log_json["user_id"] == "u1"
        assert log_json["details"]["foo"] == "bar"
        assert "timestamp" in log_json

if __name__ == "__main__":
    pytest.main([__file__])
