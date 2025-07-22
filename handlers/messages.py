"""
Message handlers for Daily Boost Bot
Handles text messages and onboarding flow
"""

import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode
from telegram.ext import MessageHandler, ContextTypes, filters
from database import Database

logger = logging.getLogger(__name__)

async def show_module_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show module selection interface with current status"""
    spiritual_enabled = context.user_data.get('spiritual_enabled', False)
    reading_enabled = context.user_data.get('reading_enabled', False)
    habits_enabled = context.user_data.get('habits_enabled', True)
    
    # Create status indicators
    spiritual_status = "✅" if spiritual_enabled else "⭕"
    reading_status = "✅" if reading_enabled else "⭕"
    habits_status = "✅" if habits_enabled else "⭕"
    
    # Create keyboard with current status
    keyboard = [
        [KeyboardButton("📿 Spiritual Check")],
        [KeyboardButton("📚 Reading Tracker")], 
        [KeyboardButton("🎯 Custom Habits")],
        [KeyboardButton("✅ Done")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    
    message_text = (
        "Almost done! Select which optional modules you'd like to enable:\n\n"
        f"{spiritual_status} **Spiritual Check**: Daily prayer and scripture tracking\n"
        f"{reading_status} **Reading Tracker**: Log your daily reading minutes\n"
        f"{habits_status} **Custom Habits**: Track your personal habits\n\n"
        "Tap a module to toggle it on/off, then press **✅ Done** when finished.\n"
        "You can always change these later in /settings."
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle onboarding flow messages"""
    user_id = update.effective_user.id
    step = context.user_data.get('onboarding_step')
    
    if not step:
        return  # Not in onboarding flow
    
    if step == 'name':
        preferred_name = update.message.text.strip()
        
        # Update user's preferred name
        success = db.update_user(user_id, preferred_name=preferred_name)
        if not success:
            await update.message.reply_text("Sorry, there was an error. Please try again.")
            return
        
        await update.message.reply_text(
            f"Nice to meet you, {preferred_name}! 😊\n\n"
            "Now, what's your target bedtime? (Format: HH:MM, e.g., 22:30)"
        )
        context.user_data['onboarding_step'] = 'bedtime'
        
    elif step == 'bedtime':
        bedtime = update.message.text.strip()
        
        # Validate time format
        try:
            datetime.strptime(bedtime, '%H:%M')
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid time in HH:MM format (e.g., 22:30)"
            )
            return
            
        context.user_data['bedtime'] = bedtime
        await update.message.reply_text(
            "Great! And what time do you usually wake up? (Format: HH:MM, e.g., 07:00)"
        )
        context.user_data['onboarding_step'] = 'waketime'
        
    elif step == 'waketime':
        waketime = update.message.text.strip()
        
        # Validate time format
        try:
            datetime.strptime(waketime, '%H:%M')
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid time in HH:MM format (e.g., 07:00)"
            )
            return
            
        context.user_data['waketime'] = waketime
        await update.message.reply_text(
            "Perfect! What's your daily water intake goal in ml? (e.g., 2500)"
        )
        context.user_data['onboarding_step'] = 'water_target'
        
    elif step == 'water_target':
        try:
            water_target = int(update.message.text.strip())
            if water_target <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid number for your water target (e.g., 2500)"
            )
            return
            
        context.user_data['water_target'] = water_target
        
        # Initialize module selection state
        context.user_data['spiritual_enabled'] = False
        context.user_data['reading_enabled'] = False
        context.user_data['habits_enabled'] = True  # Default enabled
        context.user_data['onboarding_step'] = 'modules'
        
        # Show initial module selection
        await show_module_selection(update, context)
        
    elif step == 'modules':
        text = update.message.text.strip()
        
        if text == "📿 Spiritual Check":
            # Toggle spiritual check
            context.user_data['spiritual_enabled'] = not context.user_data.get('spiritual_enabled', False)
            status = "enabled" if context.user_data['spiritual_enabled'] else "disabled"
            await update.message.reply_text(f"📿 Spiritual Check {status}!")
            await show_module_selection(update, context)
            
        elif text == "📚 Reading Tracker":
            # Toggle reading tracker
            context.user_data['reading_enabled'] = not context.user_data.get('reading_enabled', False)
            status = "enabled" if context.user_data['reading_enabled'] else "disabled"
            await update.message.reply_text(f"📚 Reading Tracker {status}!")
            await show_module_selection(update, context)
            
        elif text == "🎯 Custom Habits":
            # Toggle custom habits
            context.user_data['habits_enabled'] = not context.user_data.get('habits_enabled', True)
            status = "enabled" if context.user_data['habits_enabled'] else "disabled"
            await update.message.reply_text(f"🎯 Custom Habits {status}!")
            await show_module_selection(update, context)
            
        elif text == "✅ Done":
            # Store the values before clearing context
            bedtime = context.user_data.get('bedtime', '22:00')
            waketime = context.user_data.get('waketime', '07:00')
            water_target = context.user_data.get('water_target', 2500)
            spiritual_enabled = context.user_data.get('spiritual_enabled', False)
            reading_enabled = context.user_data.get('reading_enabled', False)
            habits_enabled = context.user_data.get('habits_enabled', True)
            
            # Save all settings to database
            success = db.update_user(
                user_id,
                bedtime=bedtime,
                waketime=waketime,
                water_target=water_target,
                spiritual_enabled=spiritual_enabled,
                reading_enabled=reading_enabled,
                habits_enabled=habits_enabled
            )
            
            if not success:
                await update.message.reply_text("Sorry, there was an error saving your settings. Please try again.")
                return
            
            # Build summary message
            summary_text = (
                "🎉 Setup complete! Welcome to your Daily Boost journey!\n\n"
                "Here's what I'll help you track:\n"
                f"💧 Water intake (goal: {water_target}ml)\n"
                "😊 Daily mood journal\n"
                "🏃 Physical activity\n"
            )
            
            if spiritual_enabled:
                summary_text += "📿 Spiritual check\n"
            if reading_enabled:
                summary_text += "📚 Reading tracker\n"
            if habits_enabled:
                summary_text += "🎯 Custom habits\n"
                
            summary_text += "\nUse /help to see all commands. Let's boost your daily wellness! 🚀"
            
            # Clear onboarding data
            context.user_data.clear()
            
            await update.message.reply_text(
                summary_text,
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/help")]], one_time_keyboard=True, resize_keyboard=True)
            )
            
            logger.info(f"Onboarding completed for user {user_id}")

async def handle_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle preferences flow messages"""
    user_id = update.effective_user.id
    mode = context.user_data.get('preferences_mode')
    text = update.message.text.strip()
    
    if mode == 'main_menu':
        if text == "👤 Change Name":
            await update.message.reply_text(
                "What would you like me to call you? (Enter your preferred name or nickname)"
            )
            context.user_data['preferences_mode'] = 'change_name'
            
        elif text == "🛏️ Change Sleep Times":
            await update.message.reply_text(
                "Let's update your sleep schedule.\n\n"
                "What's your target bedtime? (Format: HH:MM, e.g., 22:30)"
            )
            context.user_data['preferences_mode'] = 'change_bedtime'
            
        elif text == "💧 Change Water Goal":
            await update.message.reply_text(
                "What's your daily water intake goal in ml? (e.g., 2500)"
            )
            context.user_data['preferences_mode'] = 'change_water'
            
        elif text == "⚙️ Toggle Modules":
            # Get current user settings
            user = db.get_user(user_id)
            context.user_data['spiritual_enabled'] = user.get('spiritual_enabled', False)
            context.user_data['reading_enabled'] = user.get('reading_enabled', False)
            context.user_data['habits_enabled'] = user.get('habits_enabled', True)
            context.user_data['preferences_mode'] = 'toggle_modules'
            await show_module_selection(update, context)
            
        elif text == "❌ Cancel":
            context.user_data.clear()
            await update.message.reply_text(
                "Preferences cancelled. Use /preferences anytime to update your settings!",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/help")]], one_time_keyboard=True, resize_keyboard=True)
            )
            
    elif mode == 'change_name':
        new_name = text
        success = db.update_user(user_id, preferred_name=new_name)
        if success:
            await update.message.reply_text(
                f"✅ Name updated to: {new_name}\n\nUse /preferences to change other settings.",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/preferences")]], one_time_keyboard=True, resize_keyboard=True)
            )
        else:
            await update.message.reply_text("❌ Error updating name. Please try again.")
        context.user_data.clear()
        
    elif mode == 'change_bedtime':
        try:
            datetime.strptime(text, '%H:%M')
            context.user_data['new_bedtime'] = text
            await update.message.reply_text(
                "Great! And what time do you usually wake up? (Format: HH:MM, e.g., 07:00)"
            )
            context.user_data['preferences_mode'] = 'change_waketime'
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid time in HH:MM format (e.g., 22:30)"
            )
            
    elif mode == 'change_waketime':
        try:
            datetime.strptime(text, '%H:%M')
            bedtime = context.user_data.get('new_bedtime')
            waketime = text
            success = db.update_user(user_id, bedtime=bedtime, waketime=waketime)
            if success:
                await update.message.reply_text(
                    f"✅ Sleep times updated!\n"
                    f"🛏️ Bedtime: {bedtime}\n"
                    f"⏰ Wake time: {waketime}\n\n"
                    "Use /preferences to change other settings.",
                    reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/preferences")]], one_time_keyboard=True, resize_keyboard=True)
                )
            else:
                await update.message.reply_text("❌ Error updating sleep times. Please try again.")
            context.user_data.clear()
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid time in HH:MM format (e.g., 07:00)"
            )
            
    elif mode == 'change_water':
        try:
            water_target = int(text)
            if water_target <= 0:
                raise ValueError
            success = db.update_user(user_id, water_target=water_target)
            if success:
                await update.message.reply_text(
                    f"✅ Water goal updated to {water_target}ml!\n\n"
                    "Use /preferences to change other settings.",
                    reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/preferences")]], one_time_keyboard=True, resize_keyboard=True)
                )
            else:
                await update.message.reply_text("❌ Error updating water goal. Please try again.")
            context.user_data.clear()
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid number for your water target (e.g., 2500)"
            )
            
    elif mode == 'toggle_modules':
        if text == "📿 Spiritual Check":
            context.user_data['spiritual_enabled'] = not context.user_data.get('spiritual_enabled', False)
            status = "enabled" if context.user_data['spiritual_enabled'] else "disabled"
            await update.message.reply_text(f"📿 Spiritual Check {status}!")
            await show_module_selection(update, context)
            
        elif text == "📚 Reading Tracker":
            context.user_data['reading_enabled'] = not context.user_data.get('reading_enabled', False)
            status = "enabled" if context.user_data['reading_enabled'] else "disabled"
            await update.message.reply_text(f"📚 Reading Tracker {status}!")
            await show_module_selection(update, context)
            
        elif text == "🎯 Custom Habits":
            context.user_data['habits_enabled'] = not context.user_data.get('habits_enabled', True)
            status = "enabled" if context.user_data['habits_enabled'] else "disabled"
            await update.message.reply_text(f"🎯 Custom Habits {status}!")
            await show_module_selection(update, context)
            
        elif text == "✅ Done":
            # Save module settings
            success = db.update_user(
                user_id,
                spiritual_enabled=context.user_data.get('spiritual_enabled', False),
                reading_enabled=context.user_data.get('reading_enabled', False),
                habits_enabled=context.user_data.get('habits_enabled', True)
            )
            if success:
                spiritual = "✅" if context.user_data.get('spiritual_enabled') else "❌"
                reading = "✅" if context.user_data.get('reading_enabled') else "❌"
                habits = "✅" if context.user_data.get('habits_enabled') else "❌"
                
                await update.message.reply_text(
                    f"✅ Modules updated!\n\n"
                    f"📿 Spiritual Check: {spiritual}\n"
                    f"📚 Reading Tracker: {reading}\n"
                    f"🎯 Custom Habits: {habits}\n\n"
                    "Use /preferences to change other settings.",
                    reply_markup=ReplyKeyboardMarkup([[KeyboardButton("/preferences")]], one_time_keyboard=True, resize_keyboard=True)
                )
            else:
                await update.message.reply_text("❌ Error updating modules. Please try again.")
            context.user_data.clear()

async def handle_mood_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle mood tracking flow messages"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    mood_step = context.user_data.get('mood_step')
    
    if mood_step == 'rating':
        if text in ['1', '2', '3', '4', '5']:
            rating = int(text)
            context.user_data['mood_rating'] = rating
            context.user_data['mood_step'] = 'note'
            
            mood_emoji = ['😞', '😕', '😐', '😊', '😄'][rating - 1]
            await update.message.reply_text(
                f"You rated your day: {rating}/5 {mood_emoji}\n\n"
                "Would you like to add a note about your day? (optional)\n"
                "Type your note or 'skip' to finish:",
                reply_markup=ReplyKeyboardMarkup([['skip']], one_time_keyboard=True, resize_keyboard=True)
            )
        else:
            await update.message.reply_text(
                "Please select a rating from 1-5:",
                reply_markup=ReplyKeyboardMarkup([['1', '2', '3', '4', '5']], one_time_keyboard=True, resize_keyboard=True)
            )
    
    elif mood_step == 'note':
        rating = context.user_data.get('mood_rating')
        note = None if text.lower() == 'skip' else text
        
        # Save mood entry
        success = db.add_mood_entry(user_id, rating, note)
        context.user_data.clear()
        
        if success:
            mood_emoji = ['😞', '😕', '😐', '😊', '😄'][rating - 1]
            response = f"Mood logged successfully! {mood_emoji}\n\n"
            response += f"Rating: {rating}/5\n"
            if note:
                response += f"Note: {note}\n"
            response += "\nKeep tracking your daily mood! Use /moodstats to see your progress. 📈"
            await update.message.reply_text(response, reply_markup=ReplyKeyboardMarkup([['/moodstats']], one_time_keyboard=True, resize_keyboard=True))
        else:
            await update.message.reply_text("Sorry, there was an error saving your mood. Please try again.")

async def handle_habit_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle habit management flow messages"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    habit_step = context.user_data.get('habit_step')
    
    if habit_step == 'add_first':
        if text.lower() == 'cancel':
            context.user_data.clear()
            await update.message.reply_text("Habit creation cancelled! ❌")
            return
        
        # Add the first habit
        success = db.add_habit(user_id, text)
        context.user_data.clear()
        
        if success:
            await update.message.reply_text(
                f"Great! Your first habit '{text}' has been created! 🎯\n\n"
                "You'll receive daily reminders at 21:30 to check off your habits.\n\n"
                "Use /habits to manage your habits or add more!",
                reply_markup=ReplyKeyboardMarkup([['/habits']], one_time_keyboard=True, resize_keyboard=True)
            )
        else:
            await update.message.reply_text("Sorry, there was an error creating your habit. Please try again.")
    
    elif habit_step == 'manage':
        if text == "➕ Add Habit":
            await update.message.reply_text(
                "What new habit would you like to track?\n"
                "(e.g., 'Meditate 10 min', 'Call family', 'Stretch')\n\n"
                "Type your habit name or 'cancel' to exit:",
                reply_markup=ReplyKeyboardMarkup([['cancel']], one_time_keyboard=True, resize_keyboard=True)
            )
            context.user_data['habit_step'] = 'add_new'
            
        elif text == "🗑️ Delete Habit":
            habits = db.get_user_habits(user_id)
            if not habits:
                await update.message.reply_text("You don't have any habits to delete!")
                context.user_data.clear()
                return
            
            # Show habits for deletion
            keyboard = [[KeyboardButton(f"❌ {habit['habit_name']}") for habit in habits[:2]]]
            if len(habits) > 2:
                keyboard.extend([[KeyboardButton(f"❌ {habit['habit_name']}") for habit in habits[2:4]]])
            if len(habits) > 4:
                keyboard.extend([[KeyboardButton(f"❌ {habit['habit_name']}") for habit in habits[4:]]])
            keyboard.append([KeyboardButton("🔙 Back")])
            
            await update.message.reply_text(
                "Which habit would you like to delete?\n\n"
                "⚠️ This will permanently delete the habit and all its history!",
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
            context.user_data['habit_step'] = 'delete'
            
        elif text == "📊 Today's Progress":
            await show_daily_habits(update, context, db, user_id)
            context.user_data.clear()
            
        elif text == "❌ Cancel":
            context.user_data.clear()
            await update.message.reply_text("Habit management cancelled! 👍")
    
    elif habit_step == 'add_new':
        if text.lower() == 'cancel':
            context.user_data.clear()
            await update.message.reply_text("Habit creation cancelled! ❌")
            return
        
        success = db.add_habit(user_id, text)
        context.user_data.clear()
        
        if success:
            await update.message.reply_text(
                f"Excellent! New habit '{text}' added! 🎯\n\n"
                "Use /habits to manage all your habits.",
                reply_markup=ReplyKeyboardMarkup([['/habits']], one_time_keyboard=True, resize_keyboard=True)
            )
        else:
            await update.message.reply_text("Sorry, there was an error adding your habit. Please try again.")
    
    elif habit_step == 'delete':
        if text == "🔙 Back":
            # Go back to main habits menu
            habits = db.get_user_habits(user_id)
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
            return
        
        # Find and delete the habit
        if text.startswith("❌ "):
            habit_name = text[2:]  # Remove "❌ " prefix
            habits = db.get_user_habits(user_id)
            habit_to_delete = next((h for h in habits if h['habit_name'] == habit_name), None)
            
            if habit_to_delete:
                success = db.delete_habit(user_id, habit_to_delete['id'])
                context.user_data.clear()
                
                if success:
                    await update.message.reply_text(
                        f"Habit '{habit_name}' has been deleted! 🗑️\n\n"
                        "All associated history has been removed."
                    )
                else:
                    await update.message.reply_text("Sorry, there was an error deleting the habit.")
            else:
                await update.message.reply_text("Habit not found. Please try again.")
                context.user_data.clear()

async def show_daily_habits(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, user_id: int):
    """Show today's habit progress with inline buttons"""
    from datetime import date
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    today = date.today().isoformat()
    habit_logs = db.get_habit_logs_for_date(user_id, today)
    
    if not habit_logs:
        await update.message.reply_text(
            "You don't have any habits to track yet! 🎯\n\n"
            "Use /habits to create your first habit!"
        )
        return
    
    # Create inline keyboard for habit checking
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
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        progress_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle all text messages"""
    # Check if user is in onboarding flow
    if context.user_data.get('onboarding_step'):
        await handle_onboarding(update, context, db)
    # Check if user is in preferences flow
    elif context.user_data.get('preferences_mode'):
        await handle_preferences(update, context, db)
    # Check if user is in mood tracking flow
    elif context.user_data.get('mood_step'):
        await handle_mood_flow(update, context, db)
    # Check if user is in habit management flow
    elif context.user_data.get('habit_step'):
        await handle_habit_flow(update, context, db)
    else:
        # Handle other text messages here
        await update.message.reply_text(
            "I didn't understand that. Use /help to see available commands."
        )

def setup_message_handlers(application, db: Database):
    """Setup all message handlers"""
    
    # Wrapper function to pass db to handler
    async def message_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await handle_text_message(update, context, db)
    
    # Add message handler for text messages (excluding commands)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        message_wrapper
    ))
    
    logger.info("Message handlers setup complete")
