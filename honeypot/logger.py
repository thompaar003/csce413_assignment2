"""Logging helpers for the honeypot."""

import logging
import json
import os
import time

LOG_FILE = "/app/logs/honeypot.log"

class JsonFormatter(logging.Formatter):
    """Custom formatter to output JSON logs."""
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)
        return json.dumps(log_entry)

def setup_logger():
    """Sets up the structured logger."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    logger = logging.getLogger("HoneyPot")
    logger.setLevel(logging.INFO)
    
    # File handler with JSON formatting
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)
    
    # Console handler for debugging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()

def log_event(event_type, src_ip, src_port, **kwargs):
    """Log specific honeypot events."""
    extra = {
        "event_type": event_type,
        "src_ip": src_ip,
        "src_port": src_port
    }
    extra.update(kwargs)
    logger.info(f"{event_type} from {src_ip}:{src_port}", extra={"extra_data": extra})

def log_alert(message, src_ip, **kwargs):
    """Log an alert for suspicious activity."""
    extra = {
        "event_type": "ALERT",
        "src_ip": src_ip,
        "alert_message": message
    }
    extra.update(kwargs)
    logger.warning(f"ALERT: {message} from {src_ip}", extra={"extra_data": extra})
