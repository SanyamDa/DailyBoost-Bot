"""
Command handlers for Daily Boost Bot
Handles all /command interactions
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CommandHandler, ContextTypes
from telegram.constants import ParseMode
from database import Database

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /start command - onboarding flow"""
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    
    # Check if user already exists
    existing_user = db.get_user(user_id)
    
    if existing_user:
        await update.message.reply_text(
            "Welcome back! 🌟\n\n"
            "Your Daily Boost Bot is ready to help you track your wellness journey.\n"
            "Use /help to see all available commands or /settings to update your preferences."
        )
        return
        
    # Start onboarding
    await update.message.reply_text(
        "Welcome to Daily Boost Bot! 🚀\n\n"
        "I'm here to help you track your daily wellness activities and build healthy habits.\n\n"
        "Let's get you set up! First, what would you like me to call you? "
        "(Just your preferred name or nickname)"
    )
    
    # Create user in database
    db.create_user(user_id, username, "")
    
    # Set onboarding state
    context.user_data['onboarding_step'] = 'name'
    logger.info(f"Started onboarding for user {user_id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /help command - show commands cheat sheet"""
    help_text = """
🤖 **Daily Boost Bot Commands**

**🏠 Setup & Settings**
/start - Begin or reset profile
/preferences - Update your onboarding preferences
/settings - Edit timezone, targets, prompt times

**😊 Mood & Habits**
/mood <1-5> [note] - Log mood manually
/habits - Manage habit list
/checkin - Resend today's habit buttons

**💧 Water & Activity**
/water <ml> - Add water intake
/activity <text> <min> - Log exercise

**📚 Reading & Spiritual**
/read <min> [book] - Log reading time
/faithsetup - Set spiritual labels

**📊 Reports & Data**
/summary [7|30] - Charts for last n days
/export - Download CSV data
/delete - Wipe all data

**ℹ️ Help**
/help - Show this command list

**Daily Prompts (default times):**
• 14:00 - Hydration check
• 18:00 - Activity prompt  
• 20:00 - Second hydration nudge
• 21:00 - Spiritual check (if enabled)
• 21:30 - Habits + mood journal
• 22:00 - Reading reminder (if enabled)
• 22:05 - Daily digest

Use /settings to customize prompt times! 🕐
    """
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def preferences_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /preferences command - update user preferences"""
    user_id = update.effective_user.id
    
    # Check if user exists
    existing_user = db.get_user(user_id)
    
    if not existing_user:
        await update.message.reply_text(
            "You haven't completed onboarding yet! Use /start to set up your profile first."
        )
        return
    
    # Show current preferences and options to change
    keyboard = [
        [KeyboardButton("👤 Change Name"), KeyboardButton("🛏️ Change Sleep Times")],
        [KeyboardButton("💧 Change Water Goal"), KeyboardButton("⚙️ Toggle Modules")],
        [KeyboardButton("❌ Cancel")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    # Get current settings
    name = existing_user.get('preferred_name', 'Not set')
    bedtime = existing_user.get('bedtime', '22:00')
    waketime = existing_user.get('waketime', '07:00')
    water_target = existing_user.get('water_target', 2500)
    spiritual = "✅" if existing_user.get('spiritual_enabled') else "❌"
    reading = "✅" if existing_user.get('reading_enabled') else "❌"
    habits = "✅" if existing_user.get('habits_enabled') else "❌"
    
    preferences_text = (
        "**Your Current Preferences:**\n\n"
        f"👤 **Name**: {name}\n"
        f"🛏️ **Sleep**: {bedtime} - {waketime}\n"
        f"💧 **Water Goal**: {water_target}ml\n\n"
        "**Optional Modules:**\n"
        f"📿 Spiritual Check: {spiritual}\n"
        f"📚 Reading Tracker: {reading}\n"
        f"🎯 Custom Habits: {habits}\n\n"
        "What would you like to change?"
    )
    
    await update.message.reply_text(
        preferences_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Set preferences mode
    context.user_data['preferences_mode'] = 'main_menu'
    logger.info(f"User {user_id} opened preferences menu")

def setup_command_handlers(application, db: Database):
    """Setup all command handlers"""
    
    # Wrapper functions to pass db to handlers
    async def start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await start_command(update, context, db)
        
    async def help_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await help_command(update, context, db)
        
    async def preferences_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await preferences_command(update, context, db)
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_wrapper))
    application.add_handler(CommandHandler("help", help_wrapper))
    application.add_handler(CommandHandler("preferences", preferences_wrapper))
    
    logger.info("Command handlers setup complete")
