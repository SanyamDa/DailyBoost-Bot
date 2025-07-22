"""
Callback handlers for Daily Boost Bot
Handles inline keyboard button interactions
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from database import Database

logger = logging.getLogger(__name__)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback
    
    user_id = query.from_user.id
    
    # Handle habit toggle callbacks
    if query.data.startswith("habit_toggle_"):
        parts = query.data.split("_")
        if len(parts) == 4:
            habit_id = int(parts[2])
            completed = bool(int(parts[3]))
            
            # Log the habit
            success = db.log_habit(user_id, habit_id, completed)
            
            if success:
                # Refresh the habit display
                from datetime import date
                today = date.today().isoformat()
                habit_logs = db.get_habit_logs_for_date(user_id, today)
                
                # Create updated inline keyboard
                keyboard = []
                progress_text = "📊 **Today's Habit Progress**\n\n"
                
                completed_count = 0
                for habit in habit_logs:
                    status = "✅" if habit['completed'] else "❌"
                    progress_text += f"{status} {habit['habit_name']}\n"
                    
                    if habit['completed']:
                        completed_count += 1
                        # Button to mark as incomplete
                        keyboard.append([
                            InlineKeyboardButton(
                                f"❌ {habit['habit_name']}", 
                                callback_data=f"habit_toggle_{habit['habit_id']}_0"
                            )
                        ])
                    else:
                        # Button to mark as complete
                        keyboard.append([
                            InlineKeyboardButton(
                                f"✅ {habit['habit_name']}", 
                                callback_data=f"habit_toggle_{habit['habit_id']}_1"
                            )
                        ])
                
                progress_text += f"\n📈 Progress: {completed_count}/{len(habit_logs)} habits completed"
                
                if completed_count == len(habit_logs):
                    progress_text += "\n\n🎉 All habits completed today! Great job! 🌟"
                    
                    # Check if this completes a streak
                    streak = db.get_habit_streak(user_id)
                    if streak > 1:
                        progress_text += f"\n🔥 Current streak: {streak} days!"
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    progress_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                logger.info(f"Habit {habit_id} toggled to {completed} for user {user_id}")
            else:
                await query.edit_message_text("Sorry, there was an error updating your habit.")
        else:
            logger.warning(f"Invalid habit callback format: {query.data}")
    else:
        await query.edit_message_text("Unknown action")
        logger.warning(f"Unknown callback: {query.data}")

def setup_callback_handlers(application, db: Database):
    """Setup all callback handlers"""
    
    # Wrapper function to pass db to handler
    async def callback_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await handle_callback_query(update, context, db)
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(callback_wrapper))
    
    logger.info("Callback handlers setup complete")
