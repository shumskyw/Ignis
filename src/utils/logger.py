"""
Logging utilities for Ignis AI.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Set log level from environment
    log_level = os.getenv('IGNIS_LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if os.getenv('IGNIS_DEBUG') == 'true' else logging.INFO)
    console_handler.setFormatter(simple_formatter)
    # Ensure UTF-8 encoding for console output
    if hasattr(console_handler.stream, 'reconfigure'):
        try:
            console_handler.stream.reconfigure(encoding='utf-8')
        except Exception:
            pass  # Fallback to default encoding
    logger.addHandler(console_handler)

    # File handlers (if logs directory exists)
    logs_dir = Path('./logs')
    if logs_dir.exists():
        # Ensure application subdirectory exists
        app_logs_dir = logs_dir / 'application'
        app_logs_dir.mkdir(exist_ok=True)
        
        # Main application log
        app_handler = logging.handlers.RotatingFileHandler(
            app_logs_dir / 'ignis.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        app_handler.setLevel(logging.DEBUG)
        app_handler.setFormatter(detailed_formatter)
        logger.addHandler(app_handler)

        # Error log
        error_handler = logging.handlers.RotatingFileHandler(
            app_logs_dir / 'error.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)

        # Performance log
        perf_handler = logging.handlers.RotatingFileHandler(
            app_logs_dir / 'performance.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(detailed_formatter)
        # Only add performance messages
        perf_handler.addFilter(lambda record: hasattr(record, 'performance') or 'performance' in record.getMessage().lower())
        logger.addHandler(perf_handler)

    return logger


def log_performance(logger: logging.Logger, operation: str, duration: float, **kwargs):
    """
    Log performance metrics.

    Args:
        logger: Logger instance
        operation: Operation name
        duration: Duration in seconds
        **kwargs: Additional metrics
    """
    message = f"PERFORMANCE: {operation} took {duration:.3f}s"
    if kwargs:
        extras = ', '.join(f"{k}={v}" for k, v in kwargs.items())
        message += f" ({extras})"

    logger.info(message, extra={'performance': True})


class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.kwargs = kwargs
        self.start_time = None

    def __enter__(self):
        self.start_time = __import__('time').time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = __import__('time').time() - self.start_time
            log_performance(self.logger, self.operation, duration, **self.kwargs)