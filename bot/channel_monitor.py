"""
Channel Monitor

This module is responsible for connecting to Telegram and monitoring target channels
for new messages. It uses Telethon and handles authentication in non-interactive 
environments using session strings.
"""

import asyncio
from datetime import datetime, timedelta
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.errors import FloodWaitError, ChannelPrivateError
from loguru import logger

from config.settings import API_ID, API_HASH, SESSION_STRING, TARGET_CHANNEL

class ChannelMonitor:
    """Monitors Telegram channels for new financial news messages."""
    
    def __init__(self):
        """Initialize the channel monitor."""
        if not all([API_ID, API_HASH, SESSION_STRING]):
            raise ValueError("Missing required Telegram API credentials or session string")
        
        self.client = None
        self.target_channel = TARGET_CHANNEL
        self.message_buffer = []
        self.last_processed_time = datetime.now()
    
    async def connect(self):
        """Connect to Telegram using session string authentication."""
        logger.info("Connecting to Telegram...")
        
        # Create client with session string
        self.client = TelegramClient(
            StringSession(SESSION_STRING),
            int(API_ID),
            API_HASH
        )
        
        # Connect to Telegram
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            logger.error("Session string authentication failed")
            raise ConnectionError("Failed to authenticate with Telegram using session string")
        
        logger.success("Successfully connected to Telegram")
    
    async def fetch_recent_messages(self, hours=4):
        """
        Fetch recent messages from the target channel.
        
        Args:
            hours (int): How many hours of messages to fetch
            
        Returns:
            list: List of message objects
        """
        if not self.client:
            await self.connect()
        
        try:
            # Get entity for target channel
            try:
                entity = await self.client.get_entity(self.target_channel)
            except ValueError as e:
                # Try with @ prefix if not found
                try:
                    entity = await self.client.get_entity(f"@{self.target_channel}")
                except ValueError:
                    logger.error(f"Channel '{self.target_channel}' not found. Make sure it exists and you can access it.")
                    return []
            except ChannelPrivateError:
                logger.error(f"Channel '{self.target_channel}' is private and you don't have access to it.")
                return []
            
            # Calculate time limit
            time_limit = datetime.now() - timedelta(hours=hours)
            
            # Fetch messages
            messages = []
            try:
                async for message in self.client.iter_messages(
                    entity=entity,
                    limit=100,  # Adjust based on expected volume
                    offset_date=time_limit
                ):
                    if not message.text:
                        continue
                    messages.append({
                        "id": message.id,
                        "date": message.date,
                        "text": message.text
                    })
            except FloodWaitError as e:
                logger.warning(f"Rate limited by Telegram. Need to wait {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
                return []
                
            logger.info(f"Fetched {len(messages)} messages from {self.target_channel}")
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}")
            return []
    
    def clear_buffer(self):
        """Clear the message buffer."""
        self.message_buffer = []
        self.last_processed_time = datetime.now()
    
    async def disconnect(self):
        """Disconnect from Telegram."""
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected from Telegram") 