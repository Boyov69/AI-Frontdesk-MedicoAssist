"""MedicoAssist.it — Structured Logger"""

import logging
import json
from datetime import datetime
import sys


class StructuredLogger:
    def __init__(self, name="medicoassist"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)

    def log_event(self, event_type: str, **kwargs):
        """Log an event in JSON format."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "app": "medicoassist",
            **kwargs
        }
        self.logger.info(json.dumps(log_entry))


# Global logger instance
logger = StructuredLogger()
