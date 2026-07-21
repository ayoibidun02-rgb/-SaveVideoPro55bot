import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "AiAgentApibot")
    
    # Application Settings
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Data Storage
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    LEADS_FILE = os.path.join(DATA_DIR, "leads.json")
    
    # Lead Qualification Settings
    QUALIFICATION_THRESHOLDS = {
        "high": 70,
        "medium": 40,
        "low": 20
    }
    
    # Validation Rules
    FREE_EMAIL_DOMAINS = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 
        'outlook.com', 'aol.com', 'icloud.com'
    ]
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN is not set in environment variables!\n"
                "Please add it to Railway's Variables tab."
            )
        return True

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)
