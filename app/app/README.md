# 🤖 AiAgentApiBot

AI-Powered Lead Generation Bot for Telegram

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template)

## 🚀 Features

- **Smart Lead Capture**: Automated 5-step questionnaire
- **AI Qualification**: Scores leads based on business criteria
- **Real-time Tracking**: Monitor all leads and interactions
- **Data Persistence**: JSON-based storage (upgradeable to DB)
- **Interactive UI**: Inline keyboards and buttons
- **Production Ready**: Optimized for Railway deployment

## 🛠️ Tech Stack

- Python 3.9+
- python-telegram-bot 20.7
- Railway (Hosting)
- GitHub (Version Control)
- JSON (Data Storage)

## 📦 Quick Start

### 1. Create Bot on Telegram
1. Message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Save your API token

### 2. Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template)

Or manually:

1. Fork this repository
2. Connect to Railway
3. Add `TELEGRAM_BOT_TOKEN` as environment variable
4. Deploy!

### 3. Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/AiAgentApiBot.git
cd AiAgentApiBot

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your bot token

# Run bot
python -m app.main
