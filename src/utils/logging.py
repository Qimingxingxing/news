"""Logging utilities for the application."""

import sys
from loguru import logger

from ..config import Config


def setup_logging():
    """Setup application logging configuration."""
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=Config.LOG_FORMAT,
        level=Config.LOG_LEVEL,
        colorize=True
    )
    
    # Add file handler
    logger.add(
        "logs/app.log",
        format=Config.LOG_FORMAT,
        level=Config.LOG_LEVEL,
        rotation="1 day",
        retention="7 days",
        compression="zip"
    )


def get_logger(name: str = None):
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger 