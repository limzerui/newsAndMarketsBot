"""
Telegram Bot

This module implements the user-facing Telegram bot using python-telegram-bot v13.15.
It handles commands from users and sending summaries.
"""

import asyncio
from datetime import datetime
import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.error import TelegramError
from loguru import logger

from config.settings import BOT_TOKEN
from bot.subscriber import SubscriberManager
from bot.channel_monitor import ChannelMonitor
from bot.summarizer import Summarizer

class FinancialNewsBot:
    """Financial news monitoring and summarization bot."""
    
    def __init__(self):
        """Initialize the bot."""
        if not BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        
        self.token = BOT_TOKEN
        self.channel_monitor = None  # Initialize in start method
        self.summarizer = None  # Initialize in start method
        self.subscriber_manager = None  # Initialize in start method
        self.updater = None  # Initialize in start method
        self.periodic_task = None  # For the background task
        
    def start_command(self, update: Update, context: CallbackContext):
        """Handle /start command - subscribe user to updates."""
        user = update.effective_user
        
        if self.subscriber_manager.add_subscriber(
            user.id, 
            username=user.username,
            first_name=user.first_name
        ):
            update.message.reply_text(
                f"👋 Welcome {user.first_name}! You're now subscribed to financial news summaries."
            )
        else:
            update.message.reply_text(
                f"You're already subscribed to financial news summaries."
            )
    
    def stop_command(self, update: Update, context: CallbackContext):
        """Handle /stop command - unsubscribe user from updates."""
        user = update.effective_user
        
        if self.subscriber_manager.remove_subscriber(user.id):
            update.message.reply_text(
                "You've been unsubscribed from financial news summaries. "
                "Use /start to subscribe again."
            )
        else:
            update.message.reply_text(
                "You aren't currently subscribed to financial news summaries."
            )
    
    def help_command(self, update: Update, context: CallbackContext):
        """Handle /help command - show available commands."""
        help_text = """
📈 Financial News Bot - Commands:

/start - Subscribe to financial news summaries
/stop - Unsubscribe from updates
/help - Show this help message
/status - Show bot status and subscriber count

This bot monitors financial news channels and provides periodic summaries with potentially impacted stocks.
        """
        update.message.reply_text(help_text)
    
    def status_command(self, update: Update, context: CallbackContext):
        """Handle /status command - show bot status."""
        subscriber_count = self.subscriber_manager.total_subscribers()
        status_text = f"""
🤖 Bot Status:
- Active: ✅
- Subscribers: {subscriber_count}
- Last check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        update.message.reply_text(status_text)
    
    async def send_summary_to_subscribers(self, summary):
        """
        Send a summary to all subscribers.
        
        Args:
            summary (dict): Summary data from the summarizer
        """
        if not summary:
            logger.warning("No summary to send")
            return
        
        subscribers = self.subscriber_manager.get_active_subscribers()
        
        if not subscribers:
            logger.info("No subscribers to send summary to")
            return
        
        # Format the message
        message = f"""
📊 *Financial News Summary*

{summary['summary']}

*Key Points:*
"""
        for point in summary['key_points'][:3]:  # Limit to 3 key points
            message += f"- {point}\n"
        
        message += f"\n*Market Sentiment:* {summary['sentiment']}\n"
        
        if summary['potentially_impacted_stocks']:
            message += "\n*Potentially Impacted Stocks:* "
            message += ", ".join(summary['potentially_impacted_stocks'])
            
        if summary['market_sectors']:
            message += f"\n\n*Affected Sectors:* {', '.join(summary['market_sectors'])}"
        
        message += f"\n\n_Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        
        # Send to all subscribers
        bot = self.updater.bot
        for user_id in subscribers:
            try:
                bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="Markdown"
                )
                logger.info(f"Sent summary to user {user_id}")
                
                # Sleep to avoid hitting rate limits
                await asyncio.sleep(0.1)
                
            except TelegramError as e:
                logger.error(f"Failed to send message to {user_id}: {str(e)}")
    
    async def run_periodic_task(self, interval_minutes):
        """
        Run periodic tasks like fetching messages and generating summaries.
        
        Args:
            interval_minutes (int): Interval between summaries in minutes
        """
        logger.info(f"Starting periodic task with {interval_minutes} minute interval")
        
        while True:
            try:
                # Fetch recent messages
                messages = await self.channel_monitor.fetch_recent_messages(hours=4)
                
                if messages:
                    # Generate summary
                    summary = self.summarizer.summarize(messages)
                    
                    # Send to subscribers
                    if summary:
                        await self.send_summary_to_subscribers(summary)
                        
                        # Clear buffer after processing
                        self.channel_monitor.clear_buffer()
                else:
                    logger.info("No new messages to summarize")
                
                # Wait for next interval
                logger.info(f"Sleeping for {interval_minutes} minutes until next check")
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in periodic task: {str(e)}")
                # Sleep a shorter time if there was an error
                await asyncio.sleep(60)
    
    async def start(self, test_mode=False):
        """
        Start the bot.
        
        Args:
            test_mode (bool): If True, use shorter intervals for testing
        """
        # Initialize components
        self.channel_monitor = ChannelMonitor()
        self.summarizer = Summarizer()
        self.subscriber_manager = SubscriberManager()
        
        # Create the updater
        self.updater = Updater(self.token)
        
        # Register command handlers
        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", self.start_command))
        dispatcher.add_handler(CommandHandler("stop", self.stop_command))
        dispatcher.add_handler(CommandHandler("help", self.help_command))
        dispatcher.add_handler(CommandHandler("status", self.status_command))
        
        # Set up telethon client
        await self.channel_monitor.connect()
        
        # Start the periodic task in the background
        from config.settings import TESTING_INTERVAL, SUMMARY_INTERVAL
        interval = TESTING_INTERVAL if test_mode else SUMMARY_INTERVAL
        
        # Create background task for periodic summaries
        self.periodic_task = asyncio.create_task(self.run_periodic_task(interval))
        
        # Start the bot in a non-blocking way
        logger.info("Starting bot polling...")
        self.updater.start_polling()
        logger.info("Bot is running!")
        
    async def stop(self):
        """Stop the bot and clean up resources."""
        logger.info("Stopping bot...")
        
        # Cancel the periodic task if running
        if self.periodic_task and not self.periodic_task.done():
            self.periodic_task.cancel()
            logger.info("Periodic task cancelled")
            
        # Disconnect channel monitor
        if self.channel_monitor:
            await self.channel_monitor.disconnect()
            logger.info("Channel monitor disconnected")
            
        # Stop the updater
        if self.updater:
            logger.info("Stopping updater...")
            self.updater.stop()
            logger.info("Updater stopped")
            
        logger.info("Bot stopped successfully") 