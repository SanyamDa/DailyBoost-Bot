"""
Callback handlers for Daily Boost Bot
Handles inline keyboard button callbacks
"""

import logging
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from database import Database

logger = logging.getLogger(__name__)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    await query.answer()
    
    # Handle different callback types here
    # For now, just acknowledge the callback
    logger.info(f"Callback query received: {query.data}")

def setup_callback_handlers(application, db: Database):
    """Setup all callback handlers"""
    
    # Wrapper function to pass db to handler
    async def callback_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await handle_callback_query(update, context, db)
    
    # Add callback handler
    application.add_handler(CallbackQueryHandler(callback_wrapper))
    
    logger.info("Callback handlers setup complete")
