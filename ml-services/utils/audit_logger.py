import logging
import json
import os
from datetime import datetime
from typing import Any, Dict

# Ensure logs directory exists
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "audit.jsonl")

class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("audit_logger")
        self.logger.setLevel(logging.INFO)
        # Create handler if not exists
        if not self.logger.handlers:
            handler = logging.FileHandler(LOG_FILE)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_event(self, event_type: str, user_id: str = "anonymous", details: Dict[str, Any] = None, status: str = "SUCCESS", ip_address: str = "unknown"):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "status": status,
            "details": details or {}
        }
        self.logger.info(json.dumps(entry))

audit_logger = AuditLogger()
