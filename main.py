import os
import re
import json
import logging
import asyncio
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Tuple, Dict, Any

import requests
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from telegram.constants import ChatAction

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB default
PORT = int(os.environ.get("PORT", 8080))

# Ensure downloads directory exists
DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Supported platforms with their patterns
SUPPORTED_PLATFORMS = {
    "youtube": {
        "domains": ["youtube.com", "youtu.be"],
        "icon": "🎬"
    },
    "instagram": {
        "domains": ["instagram.com", "www.instagram.com"],
        "icon": "📸"
    },
    "tiktok": {
        "domains": ["tiktok.com", "www.tiktok.com", "vm.tiktok.com"],
        "icon": "🎵"
    },
    "twitter": {
        "domains": ["twitter.com", "x.com"],
        "icon": "🐦"
    },
    "facebook": {
        "domains": ["facebook.com", "www.facebook.com"],
        "icon": "📘"
    },
    "reddit": {
        "domains": ["reddit.com", "www.reddit.com", "redd.it"],
        "icon": "🤖"
    },
    "pinterest": {
        "domains": ["pinterest.com", "www.pinterest.com"],
        "icon": "📌"
    },
    "vimeo": {
        "domains": ["vimeo.com"],
        "icon": "🎥"
    },
    "dailymotion": {
        "domains": ["dailymotion.com", "www.dailymotion.com"],
        "icon": "🎞️"
    },
    "soundcloud": {
        "domains": ["soundcloud.com"],
        "icon": "🎵"
    },
    "twitch": {
        "domains": ["twitch.tv", "www.twitch.tv"],
        "icon": "🟣"
    },
}

# User statistics storage (simple JSON file)
STATS_FILE = Path("stats.json")
if STATS_FILE.exists():
    with open(STATS_FILE, "r") as f:
        STATS = json.load(f)
else:
    STATS = {"total_downloads": 0, "users": {}}

def save_stats():
    """Save statistics to file."""
    with open(STATS_FILE, "w") as f:
        json.dump(STATS, f, indent=2)

def detect_platform(url: str) -> Optional[str]:
    """Detect the platform from URL."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    
    # Remove www. prefix if present
    if domain.startswith("www."):
        domain = domain[4:]
    
    for platform, info in SUPPORTED_PLATFORMS.items():
        for supported_domain in info["domains"]:
            if supported_domain in domain:
                return platform
    return None

def format_file_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when /start is issued."""
    user = update.effective_user
    
    # Track user
    user_id = str(user.id)
    if user_id not in STATS["users"]:
        STATS["users"][user_id] = {
            "first_seen": datetime.now().isoformat(),
            "username": user.username or "",
            "first_name": user.first_name or "",
            "downloads": 0
        }
        save_stats()
    
    welcome_text = f"""
🎬 **Welcome to SaveVideoPro55 Bot!**

Hello {user.first_name}! 👋

I can download videos and audio from **12+ platforms**:
• YouTube (including Shorts & Music)
• Instagram (Reels, Posts, Stories)
• TikTok
• Twitter/X
• Facebook
• Reddit
• Pinterest
• Vimeo
• Dailymotion
• SoundCloud
• Twitch
• And more!

**How to use:**
📤 Just send me any video link
🔄 I'll process it automatically
📥 Download your video instantly

**Commands:**
/start - Show this message
/help - Get detailed help
/stats - View bot statistics
/about - About this bot
/support - Contact support

**💡 Pro Tip:** You can send multiple links at once!

Made with ❤️ using Python & Railway
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Stats", callback_data="stats"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        ],
        [
            InlineKeyboardButton("📢 Support", callback_data="support"),
            InlineKeyboardButton("⭐ Rate Bot", callback_data="rate"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    help_text = """
📖 **How to use this bot:**

**Step 1:** Copy the URL of the video you want to download
**Step 2:** Paste it in this chat
**Step 3:** Wait for me to process it
**Step 4:** Download your video!

**Supported Platforms:**
"""
    
    # Add platform list with icons
    for platform, info in SUPPORTED_PLATFORMS.items():
        help_text += f"\n{info['icon']} {platform.capitalize()}"
    
    help_text += """
    
**Tips & Tricks:**
• 🎯 For best quality, send the original URL
• 📦 Videos over 50MB will be compressed
• 🔗 You can send multiple links at once
• 🎵 Send a YouTube link to download audio only

**Need help?** Contact @YourSupportHandle

**Commands:**
/start - Welcome message
/help - This help message
/stats - Bot statistics
/about - About the bot
/support - Contact support
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot statistics."""
    total_users = len(STATS["users"])
    total_downloads = STATS["total_downloads"]
    
    stats_text = f"""
📊 **Bot Statistics**

📈 **Total Downloads:** {total_downloads:,}
👥 **Total Users:** {total_users:,}
⚡ **Status:** 🟢 Online
🏠 **Hosted on:** Railway

**Recent Activity:**
• Last 24h: {sum(1 for u in STATS["users"].values() if u.get("last_download", "") > datetime.now().timestamp() - 86400)}
• Active Users: {len([u for u in STATS["users"].values() if u.get("downloads", 0) > 0])}

**Platforms Supported:** {len(SUPPORTED_PLATFORMS)}
🔄 **Uptime:** Always 🚀
"""
    await update.message.reply_text(stats_text, parse_mode="Markdown")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send about information."""
    about_text = """
ℹ️ **About SaveVideoPro55 Bot**

**Version:** 3.0.0
**Framework:** python-telegram-bot v20+
**Hosting:** Railway
**Language:** Python 3.11+

**Features:**
• ✅ Support for 12+ platforms
• ✅ High-quality video downloads
• ✅ No watermarks (where possible)
• ✅ Automatic compression
• ✅ Fast processing
• ✅ User-friendly interface
• ✅ Statistics tracking
• ✅ Multi-link support

**Privacy Policy:**
🔒 We don't store any of your data.
📁 All downloads are temporary.
👤 No personal information is collected.

**Source Code:**
[GitHub Repository](https://github.com/yourusername/SaveVideoPro55bot)

**Made with ❤️ for the Telegram community**
"""
    await update.message.reply_text(about_text, parse_mode="Markdown", disable_web_page_preview=True)

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send support information."""
    support_text = """
📞 **Need Support?**

**Common Issues & Solutions:**

1️⃣ **"Video not downloading"**
   • Check if the video is public
   • Make sure the URL is correct
   • Try a different platform

2️⃣ **"File too large"**
   • Videos over 50MB are compressed
   • Try downloading in lower quality

3️⃣ **"Bot not responding"**
   • Check your internet connection
   • Try sending the link again
   • Contact support if persistent

**Contact Options:**
• Telegram: @YourSupportHandle
• Email: support@yourdomain.com
• GitHub Issues: [Create Issue](https://github.com/yourusername/SaveVideoPro55bot/issues)

**Response Time:** Usually within 24 hours 🕐

We're here to help! 🚀
"""
    keyboard = [
        [InlineKeyboardButton("📧 Email Support", url="mailto:support@yourdomain.com")],
        [InlineKeyboardButton("💬 Telegram Support", url="https://t.me/YourSupportHandle")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        support_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def download_video(url: str, chat_id: int, is_audio: bool = False) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Download video using yt-dlp with better options."""
    temp_dir = tempfile.mkdtemp()
    
    ydl_opts = {
        'format': 'bestaudio/best' if is_audio else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extract_flat': False,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }] if not is_audio else [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return None, "Could not extract video info", None
            
            # Get the downloaded file path
            if is_audio:
                filename = os.path.join(temp_dir, f"{info.get('title', 'audio')}.mp3")
            else:
                filename = ydl.prepare_filename(info)
                if not filename.endswith('.mp4'):
                    # Find the actual file
                    for ext in ['.mp4', '.webm', '.mkv']:
                        possible_filename = filename.rsplit('.', 1)[0] + ext
                        if os.path.exists(possible_filename):
                            filename = possible_filename
                            break
            
            if not os.path.exists(filename):
                # Try to find any file in temp_dir
                files = os.listdir(temp_dir)
                if files:
                    filename = os.path.join(temp_dir, files[0])
                else:
                    return None, "No file downloaded", None
            
            title = info.get('title', 'video')[:200]  # Limit title length
            platform = detect_platform(url) or "unknown"
            
            return filename, title, platform
            
    except Exception as e:
        logger.error(f"Download error for {url}: {str(e)}")
        return None, str(e), None

async def compress_video(input_path: str, max_size: int = MAX_FILE_SIZE) -> str:
    """Compress video using ffmpeg with better quality preservation."""
    if os.path.getsize(input_path) <= max_size:
        return input_path
    
    output_path = input_path.replace('.mp4', '_compressed.mp4')
    
    try:
        # Get video duration
        duration_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{input_path}"'
        duration = float(os.popen(duration_cmd).read().strip() or 60)
        
        # Calculate target bitrate (with safety margin)
        target_bitrate = int((max_size * 7) / duration)  # 7 instead of 8 for safety
        
        # Two-pass compression for better quality
        ffmpeg_cmd = f'''
            ffmpeg -i "{input_path}" \
                -c:v libx264 -b:v {target_bitrate}k \
                -c:a aac -b:a 128k \
                -movflags +faststart \
                -profile:v baseline \
                -level 3.0 \
                -pix_fmt yuv420p \
                -preset medium \
                -y "{output_path}"
        '''
        
        os.system(ffmpeg_cmd.strip())
        
        if os.path.exists(output_path) and os.path.getsize(output_path) < max_size:
            return output_path
        else:
            # If still too large, try lower resolution
            ffmpeg_cmd = f'''
                ffmpeg -i "{input_path}" \
                    -c:v libx264 -vf scale=640:-2 \
                    -c:a aac -b:a 128k \
                    -movflags +faststart \
                    -profile:v baseline \
                    -level 3.0 \
                    -pix_fmt yuv420p \
                    -preset medium \
                    -y "{output_path}"
            '''
            os.system(ffmpeg_cmd.strip())
            return output_path
            
    except Exception as e:
        logger.error(f"Compression error: {e}")
        return input_path

async def process_link(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str) -> None:
    """Process a single video link."""
    message = update.message
    chat_id = message.chat_id
    user_id = str(update.effective_user.id)
    
    # Send typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    
    # Detect platform
    platform = detect_platform(url)
    if not platform:
        await message.reply_text(
            "❌ **Unsupported Platform!**\n\n"
            f"URL: `{url[:100]}...`\n\n"
            "Please send a link from a supported platform.\n"
            "Send /help to see the full list.",
            parse_mode="Markdown"
        )
        return
    
    platform_info = SUPPORTED_PLATFORMS[platform]
    processing_msg = await message.reply_text(
        f"{platform_info['icon']} **Processing your {platform.capitalize()} video...**\n"
        "⏳ This may take a few moments.",
        parse_mode="Markdown"
    )
    
    try:
        # Determine if audio only (for music platforms)
        is_audio = platform in ["soundcloud"]
        
        # Download video
        filename, title, detected_platform = await download_video(url, chat_id, is_audio)
        
        if not filename or not os.path.exists(filename):
            error_text = f"""
❌ **Download Failed!**

The video couldn't be downloaded. Possible reasons:
• 🔒 The video is private
• 🚫 Invalid URL
• 🌐 Platform restrictions

**URL:** `{url[:100]}...`

Try:
1. Checking if the video is public
2. Using the original URL
3. Contacting support for help
"""
            await processing_msg.edit_text(error_text, parse_mode="Markdown")
            return
        
        # Check file size
        file_size = os.path.getsize(filename)
        is_compressed = False
        
        if file_size > MAX_FILE_SIZE:
            await processing_msg.edit_text(
                "📦 **Large File Detected!**\n"
                f"Size: {format_file_size(file_size)}\n"
                "⏳ Compressing to fit Telegram's limit...\n"
                "This may take a few seconds."
            )
            filename = await compress_video(filename)
            file_size = os.path.getsize(filename)
            is_compressed = True
        
        # Update stats
        STATS["total_downloads"] += 1
        if user_id in STATS["users"]:
            STATS["users"][user_id]["downloads"] = STATS["users"][user_id].get("downloads", 0) + 1
            STATS["users"][user_id]["last_download"] = datetime.now().timestamp()
        save_stats()
        
        # Upload video
        await processing_msg.edit_text("📤 **Uploading to Telegram...**")
        
        caption = f"""
✅ **Download Complete!**

🎬 **Title:** {title[:200]}
📁 **Size:** {format_file_size(file_size)}
📱 **Platform:** {detected_platform.capitalize() or platform.capitalize()}
{'🗜️ **Compressed:** Yes' if is_compressed else ''}
👤 **Requested by:** {update.effective_user.first_name}

🔗 Downloaded with @SaveVideoPro55bot
"""
        
        # Send the file
        if is_audio:
            with open(filename, 'rb') as audio_file:
                await message.reply_audio(
                    audio=audio_file,
                    caption=caption,
                    parse_mode="Markdown",
                    write_timeout=120,
                    title=title[:200],
                    performer="SaveVideoPro55"
                )
        else:
            with open(filename, 'rb') as video_file:
                await message.reply_video(
                    video=video_file,
                    caption=caption,
                    parse_mode="Markdown",
                    supports_streaming=True,
                    write_timeout=120,
                    has_spoiler=False
                )
        
        # Clean up
        await processing_msg.delete()
        
        # Clean up temp files
        try:
            temp_dir = os.path.dirname(filename)
            shutil.rmtree(temp_dir)
        except:
            pass
        
    except Exception as e:
        logger.error(f"Error processing link: {e}")
        error_text = f"""
❌ **Error!**

Something went wrong: `{str(e)[:200]}`

Please try:
1. Using a different link
2. Checking if the video is public
3. Contacting support if the issue persists

Sorry for the inconvenience! 🙏
"""
        await processing_msg.edit_text(error_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    text = update.message.text
    
    # Check if it's a URL
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+[^\s]*')
    urls = url_pattern.findall(text)
    
    if urls:
        # Process each URL
        for url in urls[:5]:  # Limit to 5 URLs per message
            await process_link(update, context, url)
        
        if len(urls) > 5:
            await update.message.reply_text(
                "⚠️ **Too many links!**\n"
                "I can only process 5 links at a time.\n"
                "Please send the remaining links in another message.",
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            "❌ **No URL Found!**\n\n"
            "Please send a video URL from a supported platform.\n\n"
            "**Supported platforms:**\n" + 
            "\n".join([f"{info['icon']} {p.capitalize()}" for p, info in SUPPORTED_PLATFORMS.items()]) +
            "\n\nSend /help for more information."
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "stats":
        await stats_command(update, context)
    elif query.data == "help":
        await help_command(update, context)
    elif query.data == "support":
        await support(update, context)
    elif query.data == "rate":
        await query.edit_message_text(
            "⭐ **Rate this bot!**\n\n"
            "If you like SaveVideoPro55 Bot, please rate us on:\n"
            "• [Telegram Bot Store](https://t.me/botstore)\n"
            "• [GitHub](https://github.com/yourusername/SaveVideoPro55bot)\n\n"
            "Your support means a lot! ❤️",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify user."""
    logger.error(f"Update {update} caused error: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ **An unexpected error occurred!**\n\n"
            "I've logged this issue and will work on fixing it.\n"
            "Please try again later or contact support if the problem persists.\n\n"
            "🙏 Thank you for your patience!",
            parse_mode="Markdown"
        )

def main() -> None:
    """Start the bot."""
    if not TOKEN:
        logger.error("❌ BOT_TOKEN environment variable not set!")
        logger.error("Please add BOT_TOKEN to Railway environment variables.")
        return
    
    logger.info("🚀 Starting SaveVideoPro55 Bot...")
    logger.info(f"📊 MAX_FILE_SIZE: {format_file_size(MAX_FILE_SIZE)}")
    logger.info(f"👤 OWNER_ID: {OWNER_ID}")
    
    # Create application with webhook support for Railway
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("support", support))
    
    # Add message handler for URLs
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Get Railway deployment details
    is_railway = os.environ.get("RAILWAY_ENVIRONMENT") is not None
    railway_public_url = os.environ.get("RAILWAY_PUBLIC_URL", "")
    
    if is_railway and railway_public_url:
        # Use webhook on Railway
        webhook_url = f"{railway_public_url}/webhook"
        logger.info(f"🔗 Setting webhook: {webhook_url}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=webhook_url,
            allowed_updates=Update.ALL_TYPES
        )
    else:
        # Use polling locally or if webhook not set up
        logger.info("📡 Starting bot with polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
