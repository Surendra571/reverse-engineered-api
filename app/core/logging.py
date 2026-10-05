"""Structured logging configuration."""

import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_payload.update(record.extra)

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configures root logger with JSON formatting."""
    level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger("mf_api")
    logger.setLevel(level)

    # Avoid duplicate handlers on reloads
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()
