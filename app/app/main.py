import os
import sys
import logging
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from app.config import Config, logger
from app.handlers import (
    start_command, help_command, about_command, 
    lead_command, status_command, cancel_command, 
    reset_command, handle_message, button_callback
)

def setup_application() -> Application:
    """Setup and configure the bot application"""
    
    # Validate configuration
    Config.validate()
    
    # Create application
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("lead", lead_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("reset", reset_command))
    
    # Register message handler
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # Register callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    return application

def main():
    """Main entry point"""
    try:
        logger.info("🚀 Starting AiAgentApiBot...")
        logger.info(f"Environment: {Config.ENVIRONMENT}")
        
        # Setup application
        application = setup_application()
        
        # Start bot
        logger.info("✅ Bot is ready and polling for updates...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
