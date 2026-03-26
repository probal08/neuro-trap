"""
Neuro-Trap Logger
Handles centralized logging of honeypot events to JSON files.
Crucial for Phase 5 (Dashboard).
"""
import logging
import json
import os
from datetime import datetime, timezone, timedelta

# Indian Standard Time (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    """Return current time in IST."""
    return datetime.now(IST)

# Setup log directory
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, 'honeypot.json')

class JsonFormatter(logging.Formatter):
    """Format log records as JSON objects"""
    def format(self, record):
        log_record = {
            "timestamp": now_ist().isoformat(),
            "level": record.levelname,
            "event_type": getattr(record, "event_type", "SYSTEM"),
            "ip": getattr(record, "ip", "local"),
            "message": record.getMessage(),
            "details": getattr(record, "details", {})
        }
        return json.dumps(log_record)

# Configure User Logger (for attack data)
logger = logging.getLogger('neuro_trap')
logger.setLevel(logging.INFO)

# File Handler (JSON)
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(JsonFormatter())
logger.addHandler(file_handler)

# Console Handler (Pretty Print)
console_handler = logging.StreamHandler()
class ConsoleFormatter(logging.Formatter):
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    
    def format(self, record):
        timestamp = now_ist().strftime('%H:%M:%S')
        level_color = {
            'INFO': self.GREEN,
            'WARNING': self.YELLOW,
            'ERROR': self.RED
        }.get(record.levelname, self.RESET)
        
        event_type = getattr(record, "event_type", "SYS")
        ip = getattr(record, "ip", "")
        ip_str = f"[{ip}] " if ip else ""
        
        return f"{level_color}[{timestamp}] [{event_type}] {ip_str}{record.getMessage()}{self.RESET}"

console_handler.setFormatter(ConsoleFormatter())
logger.addHandler(console_handler)

def log_event(level, event_type, message, ip=None, details=None):
    """
    Main logging function
    level: 'INFO', 'WARNING', 'ERROR'
    event_type: 'CONNECTION', 'AUTH', 'COMMAND', etc.
    """
    extra = {"event_type": event_type, "ip": ip, "details": details or {}}
    if level == 'INFO':
        logger.info(message, extra=extra)
    elif level == 'WARNING':
        logger.warning(message, extra=extra)
    elif level == 'ERROR':
        logger.error(message, extra=extra)

    # Phase 1: Dual-Write to MongoDB Atlas
    try:
        from server import mongo_client
    except ImportError:
        try:
            import mongo_client
        except ImportError:
            mongo_client = None

    if mongo_client:
        try:
            events_col = mongo_client.get_events_col()
            if events_col is not None:
                # Create a structured dict for MongoDB
                mongo_record = {
                    "timestamp": now_ist().isoformat(),
                    "level": level,
                    "event_type": event_type,
                    "ip": ip if ip else "local",
                    "message": message,
                    "details": details or {}
                }
                events_col.insert_one(mongo_record)
        except Exception:
            # Ignore MongoDB errors on write to prevent crashing the honeypot
            pass
