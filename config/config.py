import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID", 0))

# Admin IDs - поддержка нескольких администраторов
admin_ids_str = os.getenv("ADMIN_ID", "0")
ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]

# Required subscriptions for participation
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@TrainingCampTON")
REQUIRED_CHAT = os.getenv("REQUIRED_CHAT", "@TrainingCampTelegram")

# Invite links for private channels/chats (optional, used if channel/chat is private)
CHANNEL_INVITE_LINK = os.getenv("CHANNEL_INVITE_LINK", "")
CHAT_INVITE_LINK = os.getenv("CHAT_INVITE_LINK", "")

# Paths
BASE_DIR = Path(__file__).parent.parent
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = BASE_DIR / "bot.db"

# Asset files
MAIN_IMAGE = ASSETS_DIR / "main.png"
RULES_IMAGE = ASSETS_DIR / "rules.png"
TICKETS_IMAGE = ASSETS_DIR / "tickets.png"
CONGRAT_IMAGE = ASSETS_DIR / "congratt.png"
