"""Logging configuration and utilities"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def setup_logging(
    name: str = "crawly",
    level: str = "INFO",
    log_file: Optional[str] = None,
    use_json: bool = False
) -> logging.Logger:
    """
    Setup logging with both console and file handlers.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        use_json: Whether to use JSON formatting
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        log_file = LOGS_DIR / f"{name}.log"
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    if use_json:
        try:
            from pythonjsonlogger import jsonlogger
            json_format = jsonlogger.JsonFormatter(
                '%(asctime)s %(name)s %(levelname)s %(message)s'
            )
            file_handler.setFormatter(json_format)
        except ImportError:
            file_handler.setFormatter(console_format)
    else:
        file_handler.setFormatter(console_format)
    
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "crawly") -> logging.Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        log_level = os.getenv("LOG_LEVEL", "INFO")
        setup_logging(name=name, level=log_level)
    
    return logger
