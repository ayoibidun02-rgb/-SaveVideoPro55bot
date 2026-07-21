from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from app.models import LeadManager, LeadQualifier
from app.utils import format_lead_summary, get_status_emoji
from app.config import logger

# Initialize managers
lead_manager = LeadManager()
lead_qualifier = LeadQualifier()

# User sessions
user_sessions = {}

class LeadCaptureSession:
    """Manage lead capture sessions"""
    
    QUESTIONS = [
        "📧 **What's your email address?**\n_(e.g., john@company.com)_",
        "🏢 **What's your company name?**",
        "💰 **What's your budget range?**\n_(e.g., 1000, 5000, 10000)_",
        "❓ **What are you looking for?**\n_(Briefly describe your needs)_",
        "📱 **What's your phone number?**\n_(e.g., +1234567890)_"
    ]
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.current_question = 0
        self.answers = []
        self.created_at = datetime.now()
    
    def is_complete(self) -> bool:
        return self.current_question >= len(self.QUESTIONS)
    
    def add_answer(self, answer: str):
        self.answers.append(answer)
        self.current_question += 1
    
    def get_current_question(self) -> str:
        if self.is_complete():
            return None
        return self.QUESTIONS[self.current_question]
    
    def get_progress(self) -> str:
        return f"Question {self.current_question + 1} of {len(self.QUESTIONS)}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    welcome_message = f"""
👋 **Welcome to AiAgentApiBot!**

I'm your AI-powered lead generation assistant. I help you:

🔍 **Generate Leads** - Automatically capture and qualify prospects
📊 **Track Progress** - Monitor lead status and interactions
💼 **Boost Sales** - Convert visitors into customers

🚀 **Quick Start:**
• Use /lead to start capturing a new lead
• Use /status to check your leads
• Use /help for more commands

Let's find you some great leads! 💪
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🎯 New Lead", callback_data="quick_lead"),
            InlineKeyboardButton("📊 My Leads", callback_data="view_status")
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="show_help"),
            InlineKeyboardButton("ℹ️ About", callback_data="show_about")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    help_text = """
🤖 **Help Center**

**Available Commands:**
/start - Start the bot
/help - Show this help
/about - About this bot
/lead - Start lead capture
/status - View lead stats
/cancel - Cancel current session
/reset - Reset your data

**How It Works:**
1. Use /lead to start the process
2. Answer 5 simple questions
3. Get instant lead qualification
4. Track all leads with /status

**Tips for Better Results:**
✅ Use your business email
✅ Provide accurate budget info
✅ Be specific about your needs
✅ Check status regularly

Need help? Contact: support@aiagentbot.com
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about command"""
    about_text = """
🚀 **AiAgentApiBot v1.0.0**

**AI-Powered Lead Generation**
Built with ❤️ for sales teams and business owners

**Features:**
✅ Automated lead capture
✅ Smart qualification scoring
✅ Real-time tracking
✅ Data persistence
✅ Interactive interface

**Tech Stack:**
• Python 3.9+
• python-telegram-bot
• Railway Hosting
• GitHub Version Control

**Contact:**
📧 support@aiagentbot.com
🐦 @AiAgentApiBot

Made for the future of sales! 🎯
"""
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def lead_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start lead generation process"""
    user_id = update.effective_user.id
    
    # Check for existing lead
    existing_lead = lead_manager.get_lead(str(user_id))
    if existing_lead:
        keyboard = [
            [
                InlineKeyboardButton("📊 View Lead", callback_data="view_lead"),
                InlineKeyboardButton("🔄 New Lead", callback_data="new_lead")
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "You already have an existing lead. What would you like to do?",
            reply_markup=reply_markup
        )
        return
    
    # Start new session
    session = LeadCaptureSession(user_id)
    user_sessions[user_id] = session
    
    # Ask first question
    question = session.get_current_question()
    progress = session.get_progress()
    
    await update.message.reply_text(
        f"🎯 **Lead Capture Started!**\n\n"
        f"**{progress}**\n{question}\n\n"
        f"_Type /cancel anytime to stop._",
        parse_mode='Markdown'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show lead statistics"""
    stats = lead_manager.get_stats()
    all_leads = lead_manager.get_all_leads()
    
    # Build status message
    status_text = f"""
📊 **Lead Dashboard**
━━━━━━━━━━━━━━━━━━━━━
📈 **Total Leads:** {stats['total']}

**By Status:**
"""
    
    for status, count in stats['by_status'].items():
        emoji = get_status_emoji(status)
        status_text += f"{emoji} {status.capitalize()}: {count}\n"
    
    status_text += f"\n📊 **Average Score:** {stats['average_score']:.1f}/100"
    
    # Add recent leads
    if all_leads:
        status_text += "\n\n**Recent Leads:**\n"
        recent = sorted(all_leads, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        for lead in recent:
            data = lead.get("data", {})
            emoji = get_status_emoji(lead.get("status", "unknown"))
            email = data.get("email", "Unknown")
            score = lead.get("score", 0)
            status_text += f"{emoji} {email} - {score}pts\n"
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel current session"""
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
        await update.message.reply_text("✅ Session cancelled. Use /lead to start fresh.")
    else:
        await update.message.reply_text("No active session to cancel.")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset user data"""
    user_id = str(update.effective_user.id)
    
    # Remove from sessions
    if int(user_id) in user_sessions:
        del user_sessions[int(user_id)]
    
    # Remove from leads
    if lead_manager.get_lead(user_id):
        lead_manager.leads.pop(user_id, None)
        lead_manager._save_data()
        await update.message.reply_text("✅ All your data has been reset. Use /start to begin again.")
    else:
        await update.message.reply_text("No data found to reset.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle non-command messages"""
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    # Check for active session
    if user_id not in user_sessions:
        await update.message.reply_text(
            "I don't see an active session. Use /lead to start, or /help for commands."
        )
        return
    
    session = user_sessions[user_id]
    
    # Handle cancellation
    if message_text.lower() == '/cancel':
        await cancel_command(update, context)
        return
    
    # Add answer and progress
    session.add_answer(message_text)
    
    if session.is_complete():
        # Process complete lead
        await process_lead_completion(update, context, session)
    else:
        # Ask next question
        question = session.get_current_question()
        progress = session.get_progress()
        
        await update.message.reply_text(
            f"**{progress}**\n{question}\n\n"
            f"_Type /cancel anytime to stop._",
            parse_mode='Markdown'
        )

async def process_lead_completion(update: Update, context: ContextTypes.DEFAULT_TYPE, session):
    """Process completed lead capture"""
    user_id = str(update.effective_user.id)
    
    # Extract lead data
    lead_data = {
        "email": session.answers[0],
        "company": session.answers[1],
        "budget": session.answers[2],
        "interest": session.answers[3],
        "phone": session.answers[4]
    }
    
    # Qualify lead
    qualification = lead_qualifier.qualify(lead_data)
    
    # Save lead
    if lead_manager.add_lead(user_id, lead_data):
        lead_manager.update_lead(user_id, {
            "score": qualification["score"],
            "status": qualification["status"]
        })
        lead_manager.add_interaction(
            user_id, 
            "qualification", 
            {
                "score": qualification["score"],
                "status": qualification["status"],
                "criteria": qualification["criteria"]
            }
        )
        logger.info(f"Lead captured and qualified for user {user_id}")
    else:
        await update.message.reply_text("❌ Error saving lead. Please try again.")
        return
    
    # Clear session
    if int(user_id) in user_sessions:
        del user_sessions[int(user_id)]
    
    # Send results
    result_message = f"""
✅ **Lead Captured Successfully!**

{format_lead_summary(lead_manager.get_lead(user_id))}

📋 **Qualification Details:**
• Score: {qualification['score']}/100
• Status: {qualification['status'].upper()}
• Criteria: {', '.join(qualification['criteria'])}

🎯 Use /status to see all your leads.
"""
    
    await update.message.reply_text(result_message, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "quick_lead":
        await lead_command(update, context)
    
    elif data == "view_status":
        await status_command(update, context)
    
    elif data == "show_help":
        await help_command(update, context)
    
    elif data == "show_about":
        await about_command(update, context)
    
    elif data == "view_lead":
        lead = lead_manager.get_lead(str(user_id))
        if lead:
            await query.edit_message_text(
                format_lead_summary(lead),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("No lead found.")
    
    elif data == "new_lead":
        # Clear existing lead
        if str(user_id) in lead_manager.leads:
            lead_manager.leads.pop(str(user_id), None)
            lead_manager._save_data()
        await query.edit_message_text("Starting new lead capture...")
        await lead_command(update, context)
    
    elif data == "cancel_action":
        await query.edit_message_text("Action cancelled. Use /lead to start again.")
