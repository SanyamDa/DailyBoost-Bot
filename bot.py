#!/usr/bin/env python3
"""
Daily Boost Bot - Main entry point
A comprehensive Telegram bot for student wellness tracking
"""

import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application

from database import Database
from handlers.commands import setup_command_handlers
from handlers.callbacks import setup_callback_handlers
from handlers.messages import setup_message_handlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the bot"""
    # Load environment variables
    load_dotenv()
    
    # Get bot token from environment variable
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("Please set BOT_TOKEN in .env file")
        return
        
    # Initialize database
    db = Database()
    
    # Create application with better connection settings
    application = (
        Application.builder()
        .token(token)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )
    
    # Setup handlers
    setup_command_handlers(application, db)
    setup_callback_handlers(application, db)
    setup_message_handlers(application, db)
    
    # Run the bot
    print("🤖 Daily Boost Bot is starting...")
    try:
        application.run_polling(
            allowed_updates=None,  # Allow all update types
            drop_pending_updates=True,
            timeout=30
        )
    except Exception as e:
        print(f"Bot encountered an error: {e}")
        print("Retrying in 5 seconds...")
        import time
        time.sleep(5)
        try:
            application.run_polling(
                allowed_updates=None,
                drop_pending_updates=True,
                timeout=30
            )
        except Exception as e2:
            print(f"Bot failed to start: {e2}")
            print("Please check your internet connection and bot token.")

if __name__ == '__main__':
    main()
