import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get token from environment
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN is not set!")
    exit(1)

# File to store leads
LEADS_FILE = "leads.json"

# Store user sessions
user_sessions = {}

# Lead capture questions
QUESTIONS = [
    "📧 What's your email address?\n_(e.g., john@company.com)_",
    "🏢 What's your company name?",
    "💰 What's your budget range?\n_(e.g., 1000, 5000, 10000)_",
    "❓ What are you looking for?\n_(Briefly describe your needs)_",
    "📱 What's your phone number?\n_(e.g., +2348012345678)_"
]

# ============= LEAD STORAGE =============

def load_leads():
    """Load leads from JSON file"""
    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_leads(leads):
    """Save leads to JSON file"""
    with open(LEADS_FILE, 'w') as f:
        json.dump(leads, f, indent=2)

def get_user_lead(user_id):
    """Get lead for a specific user"""
    leads = load_leads()
    return leads.get(str(user_id))

def save_user_lead(user_id, lead_data):
    """Save lead for a specific user"""
    leads = load_leads()
    leads[str(user_id)] = lead_data
    save_leads(leads)

def delete_user_lead(user_id):
    """Delete lead for a specific user"""
    leads = load_leads()
    if str(user_id) in leads:
        del leads[str(user_id)]
        save_leads(leads)
        return True
    return False

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

async def lead_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start lead capture process"""
    user_id = update.effective_user.id
    
    # Check if user has an existing lead
    existing_lead = get_user_lead(user_id)
    if existing_lead:
        keyboard = [
            [InlineKeyboardButton("📊 View Current Lead", callback_data="view_lead")],
            [InlineKeyboardButton("🔄 Start New Lead", callback_data="force_new_lead")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ You already have an existing lead. What would you like to do?",
            reply_markup=reply_markup
        )
        return
    
    # Check if user has an active session
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
        f"**Question 1 of {len(QUESTIONS)}:**\n{QUESTIONS[0]}\n\n"
        f"_Type /cancel anytime to stop._",
        parse_mode='Markdown'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show lead statistics"""
    user_id = update.effective_user.id
    leads = load_leads()
    
    if not leads:
        await update.message.reply_text(
            "📊 **No leads found yet!**\n\n"
            "Start capturing leads with /lead",
            parse_mode='Markdown'
        )
        return
    
    # Get user's lead
    user_lead = leads.get(str(user_id))
    
    if not user_lead:
        await update.message.reply_text(
            "📊 **You don't have any leads yet!**\n\n"
            "Start capturing leads with /lead",
            parse_mode='Markdown'
        )
        return
    
    # Format lead details
    data = user_lead.get("data", {})
    score = user_lead.get("score", 0)
    status = user_lead.get("status", "new")
    
    # Get status emoji
    status_emoji = {
        "qualified": "🟢",
        "potential": "🟡",
        "new": "⚪"
    }.get(status, "⚪")
    
    status_text = f"""
📊 **Your Lead Details**

📋 **Information:**
📧 Email: {data.get('email', 'N/A')}
🏢 Company: {data.get('company', 'N/A')}
💰 Budget: ${data.get('budget', 'N/A')}
❓ Interest: {data.get('interest', 'N/A')}
📱 Phone: {data.get('phone', 'N/A')}

📈 **Qualification:**
Score: {score}/100
Status: {status_emoji} {status.upper()}

📅 Created: {user_lead.get('created_at', 'N/A')}

🎯 Use /lead to capture a new lead.
"""
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current session"""
    user_id = update.effective_user.id
    
    if user_id in user_sessions:
        del user_sessions[user_id]
        await update.message.reply_text("✅ Session cancelled. Use /lead to start fresh.")
    else:
        await update.message.reply_text("ℹ️ No active session to cancel.")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset user data"""
    user_id = update.effective_user.id
    
    # Remove session
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    # Remove lead
    deleted = delete_user_lead(user_id)
    
    if deleted:
        await update.message.reply_text("✅ Your lead data has been reset. Use /lead to start again.")
    else:
        await update.message.reply_text("ℹ️ No data found to reset.")

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
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "start_lead":
        await lead_command(update, context)
    
    elif data == "view_status":
        await status_command(update, context)
    
    elif data == "view_lead":
        lead = get_user_lead(user_id)
        if lead:
            data = lead.get("data", {})
            status_emoji = {
                "qualified": "🟢",
                "potential": "🟡",
                "new": "⚪"
            }.get(lead.get("status", "new"), "⚪")
            
            await query.edit_message_text(
                f"📋 **Your Lead Details**\n\n"
                f"📧 Email: {data.get('email', 'N/A')}\n"
                f"🏢 Company: {data.get('company', 'N/A')}\n"
                f"💰 Budget: ${data.get('budget', 'N/A')}\n"
                f"❓ Interest: {data.get('interest', 'N/A')}\n"
                f"📱 Phone: {data.get('phone', 'N/A')}\n\n"
                f"📊 Score: {lead.get('score', 0)}/100\n"
                f"Status: {status_emoji} {lead.get('status', 'new').upper()}",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("ℹ️ No lead found.")
    
    elif data == "force_new_lead":
        # Delete existing lead
        delete_user_lead(user_id)
        await query.edit_message_text("🔄 Starting fresh lead capture...")
        await lead_command(update, context)
    
    elif data == "cancel_action":
        await query.edit_message_text("✅ Action cancelled.")
    
    elif data == "show_help":
        await help_command(update, context)

# ============= HELPER FUNCTIONS =============

def validate_email(email):
    """Validate email format"""
    return "@" in email and "." in email

def validate_phone(phone):
    """Validate phone number"""
    # Remove spaces and special characters
    cleaned = ''.join(filter(str.isdigit, phone))
    return len(cleaned) >= 10

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
    if validate_email(lead_data["email"]):
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
        elif budget >= 500:
            score += 10
            criteria.append("Low budget")
    except:
        pass
    
    # Check interest
    interest = lead_data["interest"].lower()
    if any(word in interest for word in ["high", "urgent", "ready", "now", "immediate"]):
        score += 20
        criteria.append("High interest")
    
    # Determine status
    if score >= 70:
        status = "qualified"
        status_emoji = "🟢"
    elif score >= 40:
        status = "potential"
        status_emoji = "🟡"
    else:
        status = "new"
        status_emoji = "⚪"
    
    # Save lead
    lead_record = {
        "user_id": str(user_id),
        "data": lead_data,
        "score": score,
        "status": status,
        "criteria": criteria,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_user_lead(user_id, lead_record)
    
    # Clear session
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    # Send result
    result = f"""
✅ **Lead Captured Successfully!**

📋 **Lead Information:**
📧 Email: {lead_data['email']}
🏢 Company: {lead_data['company']}
💰 Budget: ${lead_data['budget']}
❓ Interest: {lead_data['interest']}
📱 Phone: {lead_data['phone']}

📊 **Qualification:**
Score: {score}/100
Status: {status_emoji} {status.upper()}
Criteria: {', '.join(criteria) if criteria else 'None'}

🎯 Use /status to see your lead details.
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
    app.add_handler(CommandHandler("lead", lead_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("reset", reset_command))
    
    # Add message handler for non-command messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add callback handler for inline buttons
    app.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("✅ Bot is ready! Waiting for messages...")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
