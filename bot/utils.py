"""
Utility Functions

This module provides utility functions for the bot.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

def setup_logging(log_path=None):
    """
    Set up logging configuration.
    
    Args:
        log_path (str, optional): Path to log directory
    """
    # Remove default logger
    logger.remove()
    
    # Create logs directory if it doesn't exist
    if not log_path:
        log_path = Path("logs")
        
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    
    # Set up file logging with rotation
    log_file = os.path.join(log_path, "bot_{time:YYYY-MM-DD}.log")
    logger.add(
        log_file,
        rotation="00:00",  # New file daily at midnight
        retention="7 days",  # Keep logs for 7 days
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO"
    )
    
    # Console logging
    logger.add(
        sys.stdout, 
        format="{time:HH:mm:ss} | {level: <8} | {message}",
        level="INFO"
    )
    
    logger.info("Logging initialized")

def format_time_difference(timestamp):
    """
    Format a timestamp as a human-readable time difference.
    
    Args:
        timestamp (datetime): The timestamp to format
        
    Returns:
        str: Formatted string like "5 minutes ago"
    """
    now = datetime.now()
    diff = now - timestamp
    
    seconds = diff.total_seconds()
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days > 1 else ''} ago" 