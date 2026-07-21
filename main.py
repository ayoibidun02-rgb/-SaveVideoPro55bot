import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get token from environment
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN is not set!")
    logger.error("Please add it in Railway's Variables tab")
    exit(1)

# Store user sessions
user_sessions = {}

# Lead capture questions
QUESTIONS = [
    "📧 What's your email address?",
    "🏢 What's your company name?",
    "💰 What's your budget range?",
    "❓ What are you looking for?",
    "📱 What's your phone number?"
]

# ============= COMMAND HANDLERS =============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    welcome = f"""
👋 **Welcome to AiAgentApiBot!**

I'm your AI-powered lead generation assistant. I help you capture and qualify leads automatically.

🚀 **Quick Commands:**
• /lead - Start lead capture
• /status - View your leads
• /help - Show all commands

Let's find you some great leads! 💪
"""
    
    keyboard = [
        [InlineKeyboardButton("🎯 New Lead", callback_data="start_lead")],
        [InlineKeyboardButton("📊 My Leads", callback_data="view_status")],
        [InlineKeyboardButton("❓ Help", callback_data="show_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome, parse_mode='Markdown', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
🤖 **Available Commands**

/start - Welcome message
/lead - Start lead capture
/status - View lead statistics  
/help - Show this help
/cancel - Cancel current session
/reset - Reset your data

**How It Works:**
1. Use /lead to start
2. Answer 5 questions
3. Get instant lead qualification
4. Track all leads with /status
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start lead capture process"""
    user_id = update.effective_user.id
    
    # Check if user already has a session
    if user_id in user_sessions:
        await update.message.reply_text(
            "⚠️ You already have an active lead capture session.\n"
            "Type /cancel to stop it and start fresh."
        )
        return
    
    # Create new session
    user_sessions[user_id] = {
        "answers": [],
        "question_index": 0,
        "started_at": datetime.now().isoformat()
    }
    
    # Send first question
    await update.message.reply_text(
        f"🎯 **Lead Capture Started!**\n\n"
        f"**Question 1 of 5:**\n{QUESTIONS[0]}\n\n"
        f"_Type /cancel anytime to stop._",
        parse_mode='Markdown'
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show lead statistics"""
    # This is a simple example - in production, you'd have a database
    stats_text = """
📊 **Lead Statistics**

📈 Total Leads: 0
🟢 Qualified: 0
🟡 Potential: 0
🔴 New: 0

_Start capturing leads with /lead!_
"""
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current session"""
    user_id = update.effective_user.id
    
    if user_id in user_sessions:
        del user_sessions[user_id]
        await update.message.reply_text("✅ Session cancelled. Use /lead to start fresh.")
    else:
        await update.message.reply_text("ℹ️ No active session to cancel.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset user data"""
    user_id = update.effective_user.id
    
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    await update.message.reply_text("✅ All your data has been reset. Use /start to begin again.")

# ============= MESSAGE HANDLER =============

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command messages"""
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    # Check if user has an active session
    if user_id not in user_sessions:
        await update.message.reply_text(
            "I don't see an active session. Use /lead to start, or /help for commands."
        )
        return
    
    session = user_sessions[user_id]
    
    # Check if session is complete
    if session["question_index"] >= len(QUESTIONS):
        await update.message.reply_text(
            "✅ You've already completed the lead capture!\n"
            "Use /status to see your leads or /lead to start a new one."
        )
        return
    
    # Save answer
    session["answers"].append(message_text)
    session["question_index"] += 1
    
    # Check if all questions are answered
    if session["question_index"] >= len(QUESTIONS):
        # Process complete lead
        await process_lead(update, context, session)
        return
    
    # Ask next question
    next_question = QUESTIONS[session["question_index"]]
    await update.message.reply_text(
        f"**Question {session['question_index'] + 1} of {len(QUESTIONS)}:**\n{next_question}\n\n"
        f"_Type /cancel anytime to stop._",
        parse_mode='Markdown'
    )

# ============= BUTTON CALLBACKS =============

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "start_lead":
        await lead(update, context)
    
    elif data == "view_status":
        await status(update, context)
    
    elif data == "show_help":
        await help_command(update, context)

# ============= HELPER FUNCTIONS =============

async def process_lead(update: Update, context: ContextTypes.DEFAULT_TYPE, session):
    """Process completed lead capture"""
    user_id = update.effective_user.id
    
    # Extract answers
    answers = session["answers"]
    lead_data = {
        "email": answers[0] if len(answers) > 0 else "N/A",
        "company": answers[1] if len(answers) > 1 else "N/A",
        "budget": answers[2] if len(answers) > 2 else "N/A",
        "interest": answers[3] if len(answers) > 3 else "N/A",
        "phone": answers[4] if len(answers) > 4 else "N/A"
    }
    
    # Simple qualification
    score = 0
    criteria = []
    
    # Check email
    if "@" in lead_data["email"]:
        score += 20
        criteria.append("Valid email")
        if not lead_data["email"].endswith(("gmail.com", "yahoo.com", "hotmail.com")):
            score += 15
            criteria.append("Business email")
    
    # Check company
    if len(lead_data["company"]) > 2:
        score += 20
        criteria.append("Company provided")
    
    # Check budget
    try:
        budget = float(lead_data["budget"].replace(",", ""))
        if budget >= 5000:
            score += 30
            criteria.append("High budget")
        elif budget >= 1000:
            score += 20
            criteria.append("Medium budget")
    except:
        pass
    
    # Determine status
    if score >= 70:
        status = "🟢 QUALIFIED"
    elif score >= 40:
        status = "🟡 POTENTIAL"
    else:
        status = "⚪ NEW"
    
    # Clear session
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    # Send result
    result = f"""
✅ **Lead Captured Successfully!**

📋 **Lead Information:**
📧 Email: {lead_data['email']}
🏢 Company: {lead_data['company']}
💰 Budget: {lead_data['budget']}
❓ Interest: {lead_data['interest']}
📱 Phone: {lead_data['phone']}

📊 **Qualification:**
Score: {score}/100
Status: {status}
Criteria: {', '.join(criteria) if criteria else 'None'}

🎯 Use /status to see all your leads.
"""
    
    await update.message.reply_text(result, parse_mode='Markdown')

# ============= MAIN =============

def main():
    """Main entry point"""
    logger.info("🚀 Starting AiAgentApiBot...")
    
    # Create application
    app = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("lead", lead))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("reset", reset))
    
    # Add message handler
    app.add_handler(CommandHandler("message", handle_message))
    
    # Add callback handler
    app.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("✅ Bot is ready! Waiting for messages...")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
