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

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Handle all text messages"""
    # Check if user is in onboarding flow
    if context.user_data.get('onboarding_step'):
        await handle_onboarding(update, context, db)
    # Check if user is in preferences flow
    elif context.user_data.get('preferences_mode'):
        await handle_preferences(update, context, db)
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
