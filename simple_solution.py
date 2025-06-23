#!/usr/bin/env python3
"""
Financial News Monitor and Summarizer

This script uses Telethon to:
1. Monitor a financial news channel
2. Summarize the news using OpenAI
3. Send summaries to a list of users

It doesn't use python-telegram-bot to avoid compatibility issues.
"""

import asyncio
import os
import json
import logging
from openai import OpenAI
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon import events
from telethon.tl.types import User, InputPeerUser

# Add timezone support
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    SGT = ZoneInfo("Asia/Singapore")
except ImportError:
    import pytz
    SGT = pytz.timezone("Asia/Singapore")

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_STRING = os.getenv('TELETHON_SESSION_STRING')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL', 'marketfeed')
SUBSCRIBERS_FILE = 'subscribers.json'

# Configure OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

class FinancialNewsMonitor:
    """Monitors financial news and sends summaries to subscribers."""
    
    def __init__(self):
        """Initialize the monitor."""
        if not all([API_ID, API_HASH, SESSION_STRING, BOT_TOKEN]):
            raise ValueError("Missing required credentials for both user and bot clients.")
        
        if not OPENAI_API_KEY:
            raise ValueError("Missing OpenAI API key")
        
        self.user_client = None  # For monitoring the channel
        self.bot_client = None   # For interacting with users
        self.target_channel = TARGET_CHANNEL
        self.subscribers = self._load_subscribers()
        self.last_processed_time = datetime.now(SGT)
    
    def _load_subscribers(self):
        """Load subscribers from file."""
        try:
            if os.path.exists(SUBSCRIBERS_FILE):
                with open(SUBSCRIBERS_FILE, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading subscribers: {str(e)}")
            return {}
    
    def _save_subscribers(self):
        """Save subscribers to file."""
        try:
            with open(SUBSCRIBERS_FILE, 'w') as f:
                json.dump(self.subscribers, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving subscribers: {str(e)}")
    
    def add_subscriber(self, user_id, username=None, first_name=None):
        """Add a new subscriber."""
        user_id = str(user_id)  # Convert to string for JSON keys
        now_sgt = datetime.now(SGT)
        if user_id in self.subscribers and self.subscribers[user_id].get("active", True):
            return False
        self.subscribers[user_id] = {
            "username": username,
            "first_name": first_name,
            "subscribed_at": now_sgt.isoformat(),
            "active": True
        }
        self._save_subscribers()
        logger.info(f"Added new subscriber: {user_id}")
        return True
    
    def remove_subscriber(self, user_id):
        """Remove a subscriber."""
        user_id = str(user_id)
        now_sgt = datetime.now(SGT)
        if user_id not in self.subscribers or not self.subscribers[user_id].get("active", True):
            return False
        self.subscribers[user_id]["active"] = False
        self.subscribers[user_id]["unsubscribed_at"] = now_sgt.isoformat()
        self._save_subscribers()
        logger.info(f"Removed subscriber: {user_id}")
        return True
    
    def get_active_subscribers(self):
        """Get all active subscribers."""
        return [int(user_id) for user_id, data in self.subscribers.items() 
                if data.get("active", True)]
    
    async def connect(self):
        """Connect both the user and bot clients to Telegram."""
        logger.info("Connecting user client for channel monitoring...")
        self.user_client = TelegramClient(
            StringSession(SESSION_STRING), int(API_ID), API_HASH
        )
        await self.user_client.connect()
        if not await self.user_client.is_user_authorized():
            raise ConnectionError("User client authentication failed. Check session string.")
        logger.info("User client connected successfully.")

        logger.info("Connecting bot client for user interaction...")
        # Using a file session for the bot to persist its state
        self.bot_client = TelegramClient(
            'bot_session.session', int(API_ID), API_HASH
        )
        await self.bot_client.start(bot_token=BOT_TOKEN)
        logger.info("Bot client connected successfully.")
    
    async def fetch_recent_messages(self, hours=4):
        """Fetch recent messages from the target channel using the user client."""
        if not self.user_client:
            await self.connect()
        
        try:
            # Try to get the channel
            try:
                entity = await self.user_client.get_entity(self.target_channel)
            except ValueError:
                try:
                    # Try with @ prefix
                    entity = await self.user_client.get_entity(f"@{self.target_channel}")
                except ValueError:
                    logger.error(f"Channel '{self.target_channel}' not found")
                    return []
            
            # Calculate time limit
            time_limit = datetime.now(SGT) - timedelta(hours=hours)
            
            # Fetch messages
            messages = []
            async for message in self.user_client.iter_messages(
                entity=entity,
                limit=50,  # Adjust based on expected volume
                offset_date=time_limit
            ):
                if not message.text:
                    continue
                messages.append({
                    "id": message.id,
                    "date": message.date,
                    "text": message.text
                })
            
            logger.info(f"Fetched {len(messages)} messages from {self.target_channel}")
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching messages with user client: {e}")
            return []
    
    def summarize(self, messages):
        """Summarize messages using OpenAI."""
        if not messages:
            logger.warning("No messages to summarize")
            return None
        
        # Compile message texts
        message_texts = [msg["text"] for msg in messages]
        combined_text = "\n\n---\n\n".join(message_texts)
        
        # Truncate combined text if it's too long
        if len(combined_text) > 15000:
            combined_text = combined_text[:15000] + "...(truncated)"
            logger.warning("Message text truncated to fit OpenAI token limits")
        
        prompt = """
You are a financial analyst assistant. Summarize the following financial news updates
and identify potentially impacted stocks or market sectors.

Format your response as a valid JSON object with the following structure exactly:
{
    "summary": "Brief 2-3 sentence summary of key points",
    "potentially_impacted_stocks": ["TICKER1", "TICKER2"],
    "market_sectors": ["Sector1", "Sector2"],
    "sentiment": "bullish/bearish/neutral",
    "key_points": ["Point 1", "Point 2", "Point 3"]
}
Make sure your response can be parsed as valid JSON.
"""
        
        try:
            # Using new OpenAI API format
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Changed to gpt-4o-mini
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"News updates to analyze:\n{combined_text}"}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                max_tokens=1000
            )
            
            result = response.choices[0].message.content
            
            try:
                # Log the raw response for debugging
                logger.debug(f"Raw OpenAI response: {result}")
                parsed = json.loads(result)
                logger.info("Successfully parsed OpenAI response as JSON")
                return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from OpenAI response: {e}")
                # Fallback structured data
                return {
                    "summary": "Summary could not be generated in the correct format. Here's the raw output: " + result[:200] + "...",
                    "potentially_impacted_stocks": [],
                    "market_sectors": [],
                    "sentiment": "neutral",
                    "key_points": ["Error: Unable to parse structured data"]
                }
        except Exception as e:
            logger.error(f"Error during summarization: {str(e)}")
            return {
                "summary": "Error generating summary",
                "potentially_impacted_stocks": [],
                "market_sectors": [],
                "sentiment": "neutral",
                "key_points": ["Failed to analyze news due to an error"]
            }
    
    async def send_summary_to_subscribers(self, summary):
        """Send a summary to all subscribers."""
        if not summary:
            logger.warning("No summary to send")
            return
        
        subscribers = self.get_active_subscribers()
        
        if not subscribers:
            logger.info("No subscribers to send summary to")
            return
        
        # Format the message
        message = f"""
📊 **Financial News Summary**

{summary['summary']}

**Key Points:**
"""
        for point in summary['key_points'][:3]:
            message += f"- {point}\n"
        
        message += f"\n**Market Sentiment:** {summary['sentiment']}\n"
        
        if summary['potentially_impacted_stocks']:
            message += "\n**Potentially Impacted Stocks:** "
            message += ", ".join(summary['potentially_impacted_stocks'])
            
        if summary['market_sectors']:
            message += f"\n\n**Affected Sectors:** {', '.join(summary['market_sectors'])}"
        
        message += f"\n\nGenerated at {datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Send to all subscribers
        logger.info(f"Sending summary to {len(subscribers)} subscribers: {subscribers}")
        for user_id in subscribers:
            try:
                try:
                    # Get the user entity
                    logger.info(f"Attempting to get entity for user {user_id}")
                    user = await self.user_client.get_entity(user_id)
                    logger.info(f"Got entity for user {user_id}: {type(user).__name__} {getattr(user, 'username', 'No username')}")
                    
                    # Add parse_mode for Markdown formatting
                    logger.info(f"Sending formatted message with parse_mode='md' to user {user_id}")
                    result = await self.user_client.send_message(user, message, parse_mode='md')
                    logger.info(f"Sent summary to user {user_id}, message ID: {getattr(result, 'id', 'unknown')}")
                except ValueError as ve:
                    logger.warning(f"Couldn't get entity for user {user_id}: {str(ve)}")
                    # Try sending by user ID directly
                    logger.info(f"Trying to send directly to user ID {user_id}")
                    result = await self.user_client.send_message(int(user_id), message, parse_mode='md')
                    logger.info(f"Direct send to {user_id} successful, message ID: {getattr(result, 'id', 'unknown')}")
                except Exception as e:
                    logger.error(f"Error getting entity for user {user_id}: {str(e)}")
                    continue
                
                # Sleep to avoid hitting rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to send message to {user_id}: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
    
    async def monitor_and_summarize(self, interval_minutes=30, test_mode=False):
        """Continuously monitor the channel and send summaries."""
        logger.info(f"Starting to monitor channel: {self.target_channel}")
        logger.info(f"Summary interval: {interval_minutes} minutes")
        
        if test_mode:
            logger.info("Running in TEST MODE with shorter intervals")
        
        last_message_id = None
        
        while True:
            try:
                # Fetch only messages from the last interval_minutes window
                messages = await self.fetch_recent_messages(hours=interval_minutes / 60)
                
                if messages and (last_message_id is None or messages[0]["id"] != last_message_id):
                    if messages:
                        last_message_id = messages[0]["id"]
                    summary = self.summarize(messages)
                    if summary:
                        await self.send_summary_with_fallback(summary)
                        self.last_processed_time = datetime.now(SGT)
                else:
                    logger.info("No new messages to summarize or same as last batch")
                logger.info(f"Sleeping for {interval_minutes} minutes until next check")
                await asyncio.sleep(interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(60)
    
    async def send_summary_with_fallback(self, summary):
        """Send summary to subscribers using the bot client."""
        if not summary:
            logger.warning("No summary to send")
            return
        
        subscribers = self.get_active_subscribers()
        
        if not subscribers:
            logger.info("No subscribers to send summary to")
            return
        
        # Format the message
        now_sgt = datetime.now(SGT)
        message = f"""
📊 **Financial News Summary** (Auto Update)

{summary['summary']}

**Key Points:**
"""
        for point in summary['key_points'][:3]:
            message += f"- {point}\n"
        
        message += f"\n**Market Sentiment:** {summary['sentiment']}\n"
        
        if summary['potentially_impacted_stocks']:
            message += "\n**Potentially Impacted Stocks:** "
            message += ", ".join(summary['potentially_impacted_stocks'])
            
        if summary['market_sectors']:
            message += f"\n\n**Affected Sectors:** {', '.join(summary['market_sectors'])}"
        
        message += f"\n\nGenerated at {now_sgt.strftime('%Y-%m-%d %H:%M:%S')} (SGT)"
        
        # Track success for each subscriber
        success_count = 0
        attempt_count = 0
        
        # Send to all subscribers using the bot client
        logger.info(f"Sending summary to {len(subscribers)} subscribers: {subscribers}")
        for user_id in subscribers:
            attempt_count += 1
            success = False
            
            try:
                # The bot client should be able to send directly to a user who has started it
                await self.bot_client.send_message(int(user_id), message, parse_mode='md')
                logger.info(f"Successfully sent summary to user {user_id} via bot client.")
                success = True
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id} with bot client: {e}")
            
            if success:
                success_count += 1
            await asyncio.sleep(1)
        
        logger.info(f"Summary delivery: {success_count}/{attempt_count} successful")
        return success_count > 0
    
    async def setup_handlers(self):
        """Set up event handlers on the bot client."""
        @self.bot_client.on(events.NewMessage(pattern='/start'))
        async def start_command(event):
            """Handle /start command."""
            sender = await event.get_sender()
            user_id = str(sender.id)
            
            logger.info(f"Start command received from user ID: {user_id}, username: {sender.username}")
            
            # Add as subscriber
            self.add_subscriber(user_id, sender.username, sender.first_name)
            
            # Send welcome message
            welcome_message = f"""
👋 Welcome {sender.first_name}! You're now subscribed to financial news summaries.

The bot will send you regular summaries of financial news with:
- Brief summary of key points
- Market sentiment analysis
- Potentially impacted stocks
- Affected market sectors

Available commands:
/test - Generate a test summary now
/status - Check bot status
/help - Show all commands
/stop - Unsubscribe
/force_update - Force an immediate update to all subscribers

You should receive summaries automatically every few minutes (in test mode) or hours (in normal mode).
"""
            
            # Send welcome message
            logger.info(f"Sending welcome message to user {user_id}")
            await event.respond(welcome_message, parse_mode='md')
            
            # Send a test message to verify communication
            logger.info(f"Sending test message to verify communication with {user_id}")
            test_message = "This is a test message to verify I can send you direct messages. If you see this, communication is working correctly!"
            await self.bot_client.send_message(sender, test_message, parse_mode='md')
        
        @self.bot_client.on(events.NewMessage(pattern='/stop'))
        async def stop_command(event):
            """Handle /stop command."""
            sender = await event.get_sender()
            self.remove_subscriber(sender.id)
            await event.respond("You've been unsubscribed from financial news summaries. Use /start to subscribe again.", parse_mode='md')
        
        @self.bot_client.on(events.NewMessage(pattern='/help'))
        async def help_command(event):
            """Handle /help command."""
            help_text = """
📈 **Financial News Bot - Commands**:

/start - Subscribe to financial news summaries
/stop - Unsubscribe from updates
/help - Show this help message
/status - Show bot status and subscriber count
/test - Send a test summary (for testing purposes)
/subscribe_me - Special command to subscribe yourself
/force_update - Force an immediate update to all subscribers

This bot monitors financial news channels and provides periodic summaries with potentially impacted stocks.
"""
            await event.respond(help_text, parse_mode='md')
        
        @self.bot_client.on(events.NewMessage(pattern='/status'))
        async def status_command(event):
            """Handle /status command."""
            subscriber_count = len(self.get_active_subscribers())
            status_text = f"""
🤖 **Bot Status**:
- Active: ✅
- Subscribers: {subscriber_count}
- Last check: {self.last_processed_time.strftime('%Y-%m-%d %H:%M:%S')}
- Target channel: {self.target_channel}
"""
            await event.respond(status_text, parse_mode='md')
        
        @self.bot_client.on(events.NewMessage(pattern='/force_update'))
        async def force_update_command(event):
            """Force an immediate update to all subscribers."""
            sender = await event.get_sender()
            sender_id = str(sender.id)
            
            logger.info(f"Force update command received from user ID: {sender_id}, username: {sender.username}")
            
            await event.respond("Forcing an immediate update to all subscribers...", parse_mode='md')
            
            # Fetch and summarize
            messages = await self.fetch_recent_messages(hours=2)
            if messages:
                summary = self.summarize(messages)
                if summary:
                    # Send to all subscribers
                    success = await self.send_summary_with_fallback(summary)
                    
                    if success:
                        await event.respond("✅ Force update sent successfully to subscribers!", parse_mode='md')
                    else:
                        await event.respond("⚠️ There were issues sending the update to some subscribers. Check logs for details.", parse_mode='md')
                else:
                    await event.respond("Error generating summary.", parse_mode='md')
            else:
                await event.respond("No messages found to summarize.", parse_mode='md')
        
        @self.bot_client.on(events.NewMessage(pattern='/test'))
        async def test_command(event):
            """Handle /test command - admin only for testing."""
            sender = await event.get_sender()
            sender_id = str(sender.id)
            
            logger.info(f"Test command received from user ID: {sender_id}, username: {sender.username}")
            
            # Add yourself as a subscriber to test
            self.add_subscriber(sender_id, sender.username, sender.first_name)
            
            await event.respond("Fetching latest news and generating a test summary...", parse_mode='md')
            
            # Fetch and summarize
            messages = await self.fetch_recent_messages(hours=2)
            if messages:
                summary = self.summarize(messages)
                if summary:
                    # Format the message directly here instead of using send_summary_to_subscribers
                    message = f"""
📊 **Financial News Summary**

{summary['summary']}

**Key Points:**
"""
                    for point in summary['key_points'][:3]:
                        message += f"- {point}\n"
                    
                    message += f"\n**Market Sentiment:** {summary['sentiment']}\n"
                    
                    if summary['potentially_impacted_stocks']:
                        message += "\n**Potentially Impacted Stocks:** "
                        message += ", ".join(summary['potentially_impacted_stocks'])
                        
                    if summary['market_sectors']:
                        message += f"\n\n**Affected Sectors:** {', '.join(summary['market_sectors'])}"
                    
                    message += f"\n\nGenerated at {datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    # Send the actual summary in the chat
                    logger.info(f"Sending test summary response directly to the chat")
                    await event.respond(message, parse_mode='md')
                    
                    # Now also demonstrate the new fallback method
                    logger.info(f"Testing the new summary delivery fallback method")
                    await event.respond("Now testing automatic delivery method, check for another message...", parse_mode='md')
                    success = await self.send_summary_with_fallback(summary)
                    
                    if success:
                        await event.respond("✅ Automatic delivery test successful! You should have received another copy.", parse_mode='md')
                    else:
                        await event.respond("⚠️ Automatic delivery test failed. Check logs for details.", parse_mode='md')
                else:
                    await event.respond("Error generating summary.", parse_mode='md')
            else:
                await event.respond("No messages found to summarize.", parse_mode='md')
        
        @self.bot_client.on(events.NewMessage(pattern='/subscribe_me'))
        async def subscribe_me_command(event):
            """Special command to subscribe the sender."""
            sender = await event.get_sender()
            success = self.add_subscriber(sender.id, sender.username, sender.first_name)
            
            if success:
                await event.respond(f"👋 Welcome {sender.first_name}! You're now subscribed to financial news summaries.", parse_mode='md')
            else:
                await event.respond("You're already subscribed to financial news summaries.", parse_mode='md')
    
    async def run(self, interval_minutes=30, test_mode=False):
        """Run the monitor, with the bot client taking the lead."""
        if not self.user_client or not self.bot_client:
            await self.connect()
        
        await self.setup_handlers()
        
        await self.send_startup_notification(test_mode)
        
        asyncio.create_task(self.monitor_and_summarize(interval_minutes, test_mode))
        
        logger.info("Bot is running! Listening for commands. Press Ctrl+C to stop.")
        await self.bot_client.run_until_disconnected()
    
    async def send_startup_notification(self, test_mode):
        """Send a startup notification to all subscribers."""
        subscribers = self.get_active_subscribers()
        
        if subscribers:
            logger.info(f"Sending startup notification to {len(subscribers)} subscribers")
            mode_text = "TEST MODE (faster updates)" if test_mode else "NORMAL MODE"
            
            message = f"""
🤖 **Financial News Bot Started**

The bot has been started in {mode_text} and is now monitoring financial news.
You will receive regular summaries of financial news.

Available commands:
- /help - Show all available commands
- /status - Show bot status
- /test - Generate a test summary now
- /stop - Unsubscribe from updates

Thank you for using Financial News Bot!
"""
            
            for user_id in subscribers:
                try:
                    user = await self.user_client.get_entity(user_id)
                    await self.user_client.send_message(user, message, parse_mode='md')
                    logger.info(f"Sent startup notification to user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to send startup notification to {user_id}: {str(e)}")
                
                await asyncio.sleep(1)  # Avoid hitting rate limits
    
    async def disconnect(self):
        """Disconnect both clients."""
        if self.user_client and self.user_client.is_connected():
            await self.user_client.disconnect()
            logger.info("User client disconnected.")
        if self.bot_client and self.bot_client.is_connected():
            await self.bot_client.disconnect()
            logger.info("Bot client disconnected.")

async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Financial News Monitor')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--admin_id', type=str, help='Admin Telegram user ID to receive summaries (optional)')
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    interval = 30  # Always 30 minutes now
    
    monitor = FinancialNewsMonitor()
    
    if args.admin_id:
        try:
            admin_id = str(args.admin_id)
            logger.info(f"Adding admin (ID: {admin_id}) as a subscriber")
            monitor.add_subscriber(admin_id, "admin", "Admin")
            logger.info(f"Admin added as subscriber successfully")
        except Exception as e:
            logger.error(f"Failed to add admin as subscriber: {str(e)}")
    
    try:
        await monitor.run(interval_minutes=interval, test_mode=False)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        await monitor.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 