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

**⚙️ Setup & Settings**
/preferences - Update your preferences and settings

**😊 Mood Tracking**
/mood - Track your daily mood (1-5 rating + note)
/moodstats - View monthly mood analytics with charts

**🎯 Habit Tracking**
/habits - Create, edit, or delete your habits
/habittracker - Weekly habit completion report
/habitstreak - Current streak of all habits completed
/habitstats - Overall completion percentage badge

**ℹ️ Help**
/help - Show this command list

**📅 Daily Reminders:**
• 21:30 - Daily habit check-in with interactive buttons

Start building better habits today! 🌟
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

async def mood_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /mood command - track daily mood"""
    user_id = update.effective_user.id
    
    # Check if user exists, create if not
    existing_user = db.get_user(user_id)
    if not existing_user:
        username = update.effective_user.username or ""
        preferred_name = update.effective_user.first_name or ""
        db.create_user(user_id, username, preferred_name)
    
    # Check if mood already logged today
    from datetime import date
    today = date.today().isoformat()
    today_entry = db.get_mood_entry(user_id, today)
    
    if today_entry:
        note_text = f"Note: {today_entry['note']}" if today_entry['note'] else "No note"
        await update.message.reply_text(
            f"You've already logged your mood today! 📝\n\n"
            f"Rating: {today_entry['mood_score']}/5\n"
            f"{note_text}\n\n"
            "Would you like to update it? Rate your day from 1-5:",
            reply_markup=ReplyKeyboardMarkup([['1', '2', '3', '4', '5']], one_time_keyboard=True, resize_keyboard=True)
        )
    else:
        await update.message.reply_text(
            "How are you feeling today? 😊\n\n"
            "Rate your day from 1-5:\n"
            "1 = Very Bad 😞\n"
            "2 = Bad 😕\n"
            "3 = Okay 😐\n"
            "4 = Good 😊\n"
            "5 = Excellent 😄",
            reply_markup=ReplyKeyboardMarkup([['1', '2', '3', '4', '5']], one_time_keyboard=True, resize_keyboard=True)
        )
    
    context.user_data['mood_step'] = 'rating'
    logger.info(f"User {user_id} started mood tracking")

async def moodstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /moodstats command - show monthly mood analytics"""
    user_id = update.effective_user.id
    
    # Check if user exists
    if not db.get_user(user_id):
        await update.message.reply_text("Please use /start first to set up your account!")
        return
    
    # Get current month data
    from datetime import datetime
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import io
    
    now = datetime.now()
    entries = db.get_mood_entries_for_month(user_id, now.year, now.month)
    
    if not entries:
        await update.message.reply_text(
            f"No mood entries found for {now.strftime('%B %Y')} 📊\n\n"
            "Start tracking your mood with /mood!"
        )
        return
    
    # Generate statistics
    stats = db.get_mood_stats(user_id, now.year, now.month)
    
    # Create line chart
    dates = [datetime.strptime(entry['date'], '%Y-%m-%d').date() for entry in entries]
    ratings = [entry['mood_score'] for entry in entries]
    
    plt.figure(figsize=(10, 6))
    plt.plot(dates, ratings, marker='o', linewidth=2, markersize=8, color='#4CAF50')
    plt.title(f'Mood Tracker - {now.strftime("%B %Y")}', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Mood Rating', fontsize=12)
    plt.ylim(0.5, 5.5)
    plt.yticks([1, 2, 3, 4, 5], ['😞\nVery Bad', '😕\nBad', '😐\nOkay', '😊\nGood', '😄\nExcellent'])
    plt.grid(True, alpha=0.3)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save chart to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    # Send chart and stats
    stats_text = (
        f"📊 **Mood Statistics for {now.strftime('%B %Y')}**\n\n"
        f"📝 Total entries: {stats['total_entries']}\n"
        f"📈 Average rating: {stats['average_rating']:.1f}/5\n"
        f"🔝 Highest rating: {stats['highest_rating']}/5\n"
        f"🔻 Lowest rating: {stats['lowest_rating']}/5\n\n"
        f"Keep tracking your mood daily! 🌟"
    )
    
    await update.message.reply_photo(
        photo=buf,
        caption=stats_text,
        parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"Sent mood statistics to user {user_id}")

async def habits_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /habits command - manage habit list"""
    user_id = update.effective_user.id
    
    # Check if user exists, create if not
    if not db.get_user(user_id):
        username = update.effective_user.username or ""
        preferred_name = update.effective_user.first_name or ""
        db.create_user(user_id, username, preferred_name)
    
    # Get current habits
    habits = db.get_user_habits(user_id)
    
    if not habits:
        await update.message.reply_text(
            "You don't have any habits yet! 🎯\n\n"
            "Let's create your first habit. What would you like to track?\n"
            "(e.g., 'Exercise', 'Read 30 min', 'Drink water')\n\n"
            "Type your habit name or 'cancel' to exit:",
            reply_markup=ReplyKeyboardMarkup([['cancel']], one_time_keyboard=True, resize_keyboard=True)
        )
        context.user_data['habit_step'] = 'add_first'
    else:
        # Show current habits with management options
        habit_list = "\n".join([f"• {habit['habit_name']}" for habit in habits])
        
        keyboard = [
            [KeyboardButton("➕ Add Habit"), KeyboardButton("🗑️ Delete Habit")],
            [KeyboardButton("📊 Today's Progress"), KeyboardButton("❌ Cancel")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            f"🎯 **Your Habits:**\n\n{habit_list}\n\n"
            "What would you like to do?",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['habit_step'] = 'manage'
    
    logger.info(f"User {user_id} opened habits management")

async def habittracker_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /habittracker command - weekly stacked bar report"""
    user_id = update.effective_user.id
    
    if not db.get_user(user_id):
        await update.message.reply_text("Please use /start first to set up your account!")
        return
    
    # Get weekly stats
    stats = db.get_habit_stats_weekly(user_id)
    
    if not stats:
        await update.message.reply_text(
            "No habit data found for this week! 📊\n\n"
            "Start tracking habits with /habits!"
        )
        return
    
    # Create stacked bar chart
    import matplotlib.pyplot as plt
    import numpy as np
    import io
    
    habits = list(stats.keys())
    percentages = [stats[habit]['percentage'] for habit in habits]
    completed = [stats[habit]['completed'] for habit in habits]
    total = [stats[habit]['total'] for habit in habits]
    
    # Create horizontal bar chart
    fig, ax = plt.subplots(figsize=(10, max(6, len(habits) * 0.8)))
    
    y_pos = np.arange(len(habits))
    bars = ax.barh(y_pos, percentages, color='#4CAF50', alpha=0.8)
    
    # Add percentage labels on bars
    for i, (bar, pct, comp, tot) in enumerate(zip(bars, percentages, completed, total)):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                f'{pct:.0f}% ({comp}/{tot})', 
                ha='left', va='center', fontweight='bold')
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(habits)
    ax.set_xlabel('Completion Percentage')
    ax.set_title('Weekly Habit Tracker (Last 7 Days)', fontsize=16, fontweight='bold')
    ax.set_xlim(0, 110)
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    # Save chart to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    # Calculate overall weekly completion
    if total:
        overall_completion = sum(completed) / sum(total) * 100
    else:
        overall_completion = 0
    
    stats_text = (
        f"📊 **Weekly Habit Report**\n\n"
        f"📈 Overall completion: {overall_completion:.1f}%\n"
        f"🎯 Habits tracked: {len(habits)}\n\n"
        f"Keep up the great work! 🌟"
    )
    
    await update.message.reply_photo(
        photo=buf,
        caption=stats_text,
        parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"Sent weekly habit tracker to user {user_id}")

async def habitstreak_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /habitstreak command - longest current streak"""
    user_id = update.effective_user.id
    
    if not db.get_user(user_id):
        await update.message.reply_text("Please use /start first to set up your account!")
        return
    
    habits = db.get_user_habits(user_id)
    if not habits:
        await update.message.reply_text(
            "You don't have any habits yet! 🎯\n\n"
            "Create habits with /habits first!"
        )
        return
    
    streak = db.get_habit_streak(user_id)
    
    if streak == 0:
        await update.message.reply_text(
            "🔥 **Current Streak: 0 days**\n\n"
            "Complete all your habits today to start a new streak! 💪\n\n"
            "Use /habits to check today's progress."
        )
    elif streak == 1:
        await update.message.reply_text(
            "🔥 **Current Streak: 1 day**\n\n"
            "Great start! Keep it up to build a longer streak! 🌟\n\n"
            "Complete all habits today to reach 2 days! 💪"
        )
    else:
        # Add streak milestone emojis
        if streak >= 30:
            emoji = "🏆"
            message = "Incredible! You're a habit master!"
        elif streak >= 21:
            emoji = "🥇"
            message = "Amazing! You've built a solid habit!"
        elif streak >= 14:
            emoji = "🥈"
            message = "Fantastic! Two weeks strong!"
        elif streak >= 7:
            emoji = "🥉"
            message = "Great job! One week streak!"
        else:
            emoji = "🔥"
            message = "Keep going strong!"
        
        await update.message.reply_text(
            f"{emoji} **Current Streak: {streak} days**\n\n"
            f"{message}\n\n"
            f"Don't break the chain! Complete all habits today! 💪"
        )
    
    logger.info(f"Sent habit streak to user {user_id}: {streak} days")

async def habitstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle /habitstats command - overall completion badge"""
    user_id = update.effective_user.id
    
    if not db.get_user(user_id):
        await update.message.reply_text("Please use /start first to set up your account!")
        return
    
    habits = db.get_user_habits(user_id)
    if not habits:
        await update.message.reply_text(
            "You don't have any habits yet! 🎯\n\n"
            "Create habits with /habits first!"
        )
        return
    
    stats = db.get_habit_overall_stats(user_id)
    completion_pct = stats['completion_percentage']
    
    # Determine badge based on completion percentage
    if completion_pct >= 90:
        badge = "🏆 LEGEND"
        color = "🟢"
        message = "You're absolutely crushing it!"
    elif completion_pct >= 80:
        badge = "🥇 CHAMPION"
        color = "🟡"
        message = "Outstanding consistency!"
    elif completion_pct >= 70:
        badge = "🥈 ACHIEVER"
        color = "🟠"
        message = "Great progress, keep it up!"
    elif completion_pct >= 60:
        badge = "🥉 BUILDER"
        color = "🔵"
        message = "You're building good habits!"
    elif completion_pct >= 40:
        badge = "🌱 STARTER"
        color = "🟣"
        message = "Good start, aim higher!"
    else:
        badge = "🔰 BEGINNER"
        color = "⚪"
        message = "Every journey starts with a step!"
    
    await update.message.reply_text(
        f"{color} **HABIT COMPLETION BADGE** {color}\n\n"
        f"{badge}\n"
        f"**{completion_pct:.1f}% Overall Completion**\n\n"
        f"📊 Total habit checks: {stats['total_logs']}\n"
        f"✅ Completed: {stats['completed_logs']}\n"
        f"❌ Missed: {stats['total_logs'] - stats['completed_logs']}\n\n"
        f"{message} 🌟",
        parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"Sent habit stats to user {user_id}: {completion_pct:.1f}%")

def setup_command_handlers(application, db: Database):
    """Setup all command handlers"""
    
    # Wrapper functions to pass db to handlers
    async def start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await start_command(update, context, db)
        
    async def help_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await help_command(update, context, db)
        
    async def preferences_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await preferences_command(update, context, db)
    
    async def mood_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await mood_command(update, context, db)
    
    async def moodstats_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await moodstats_command(update, context, db)
    
    async def habits_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await habits_command(update, context, db)
    
    async def habittracker_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await habittracker_command(update, context, db)
    
    async def habitstreak_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await habitstreak_command(update, context, db)
    
    async def habitstats_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await habitstats_command(update, context, db)
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_wrapper))
    application.add_handler(CommandHandler("help", help_wrapper))
    application.add_handler(CommandHandler("preferences", preferences_wrapper))
    application.add_handler(CommandHandler("mood", mood_wrapper))
    application.add_handler(CommandHandler("moodstats", moodstats_wrapper))
    application.add_handler(CommandHandler("habits", habits_wrapper))
    application.add_handler(CommandHandler("habittracker", habittracker_wrapper))
    application.add_handler(CommandHandler("habitstreak", habitstreak_wrapper))
    application.add_handler(CommandHandler("habitstats", habitstats_wrapper))
    
    logger.info("Command handlers setup complete")
