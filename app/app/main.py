import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get token from environment
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN environment variable is not set!")
    logger.error("Please add it in Railway's Variables tab")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "✅ Bot is working!\n\n"
        "Use /lead to start lead capture\n"
        "Use /help for more commands"
    )

async def lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /lead command"""
    await update.message.reply_text(
        "🔄 Lead capture started!\n\n"
        "Please answer these questions:\n"
        "1. What's your email?\n"
        "2. What's your company?\n"
        "3. What's your budget?"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "🤖 Available commands:\n"
        "/start - Start the bot\n"
        "/lead - Start lead capture\n"
        "/help - Show this help"
    )

def main():
    """Main function"""
    logger.info("🚀 Starting bot...")
    
    # Create application
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lead", lead))
    app.add_handler(CommandHandler("help", help_command))
    
    logger.info("✅ Bot is running! Waiting for messages...")
    app.run_polling()

if __name__ == "__main__":
    main()
