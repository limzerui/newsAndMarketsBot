"""
Subscriber Manager

This module manages subscribers to the bot. It handles:
- Adding new subscribers
- Removing subscribers
- Storing subscriber data
- Retrieving the list of subscribers
"""

import os
import json
from datetime import datetime
from loguru import logger
from pathlib import Path

class SubscriberManager:
    """Manages subscribers to the financial news bot."""
    
    def __init__(self, db_file=None):
        """
        Initialize the subscriber manager.
        
        Args:
            db_file (str, optional): Path to the subscriber database file
        """
        self.db_file = db_file or Path("subscribers.json").absolute()
        self.subscribers = self._load_subscribers()
    
    def _load_subscribers(self):
        """Load subscribers from the file."""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("Invalid subscriber file format")
                return {}
        return {}
    
    def _save_subscribers(self):
        """Save subscribers to the file."""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.subscribers, f, indent=2)
            logger.debug(f"Subscribers saved to {self.db_file}")
        except Exception as e:
            logger.error(f"Error saving subscribers: {str(e)}")
    
    def add_subscriber(self, user_id, username=None, first_name=None):
        """
        Add a new subscriber.
        
        Args:
            user_id (int): Telegram user ID
            username (str, optional): Telegram username
            first_name (str, optional): User's first name
            
        Returns:
            bool: True if added, False if already exists
        """
        user_id = str(user_id)  # Convert to string for JSON keys
        
        if user_id in self.subscribers:
            logger.info(f"User {user_id} already subscribed")
            return False
        
        self.subscribers[user_id] = {
            "username": username,
            "first_name": first_name,
            "subscribed_at": datetime.now().isoformat(),
            "active": True
        }
        
        self._save_subscribers()
        logger.info(f"Added new subscriber: {user_id}")
        return True
    
    def remove_subscriber(self, user_id):
        """
        Remove a subscriber.
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            bool: True if removed, False if not found
        """
        user_id = str(user_id)
        
        if user_id not in self.subscribers:
            logger.info(f"User {user_id} not found in subscribers")
            return False
        
        self.subscribers[user_id]["active"] = False
        self.subscribers[user_id]["unsubscribed_at"] = datetime.now().isoformat()
        
        self._save_subscribers()
        logger.info(f"Removed subscriber: {user_id}")
        return True
    
    def get_active_subscribers(self):
        """
        Get all active subscribers.
        
        Returns:
            list: List of active subscriber IDs
        """
        return [int(user_id) for user_id, data in self.subscribers.items() 
                if data.get("active", True)]
    
    def total_subscribers(self):
        """
        Get total number of active subscribers.
        
        Returns:
            int: Number of active subscribers
        """
        return len(self.get_active_subscribers()) 