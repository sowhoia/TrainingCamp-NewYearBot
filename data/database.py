"""Database module with repository pattern.

This module provides a unified Database class that:
1. Initializes the database schema
2. Exposes repository instances for different domains
3. Maintains backwards compatibility via proxy methods
"""
import aiosqlite
from config.config import DB_PATH

from data.repositories.users import UserRepository
from data.repositories.wishes import WishRepository
from data.repositories.settings import SettingsRepository
from data.repositories.stats import StatsRepository


class Database:
    """Main database class with repository access and backwards compatibility."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        
        # Initialize repositories
        self.users = UserRepository(self.db_path)
        self.wishes = WishRepository(self.db_path)
        self.settings = SettingsRepository(self.db_path)
        self.stats = StatsRepository(self.db_path)
    
    async def init(self):
        """Initialize database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    tickets INTEGER DEFAULT 0,
                    referrer_id INTEGER,
                    has_wished BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS wishes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    text TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            await db.commit()
    
    # ==================== BACKWARDS COMPATIBILITY PROXIES ====================
    # These methods proxy to the appropriate repository for backwards compatibility
    # with existing handler code. New code should use db.users, db.wishes, etc.
    
    # --- User methods ---
    async def get_user(self, user_id: int):
        return await self.users.get_user(user_id)
    
    async def create_user(self, user_id: int, username: str, referrer_id: int = None):
        return await self.users.create_user(user_id, username, referrer_id)
    
    async def update_username(self, user_id: int, username: str):
        return await self.users.update_username(user_id, username)
    
    async def find_user_by_username(self, username: str):
        return await self.users.find_user_by_username(username)
    
    async def add_tickets_to_user(self, user_id: int, count: int) -> int | None:
        return await self.users.add_tickets_to_user(user_id, count)
    
    async def get_referral_count(self, user_id: int) -> int:
        return await self.users.get_referral_count(user_id)
    
    async def get_total_referrals(self, user_id: int) -> int:
        return await self.users.get_total_referrals(user_id)
    
    # --- Wish methods ---
    async def add_wish(self, user_id: int, text: str) -> bool:
        return await self.wishes.add_wish(user_id, text)
    
    async def get_user_wish(self, user_id: int):
        return await self.wishes.get_user_wish(user_id)
    
    async def get_random_wish(self):
        return await self.wishes.get_random_wish()
    
    async def find_wish_by_text(self, text: str):
        return await self.wishes.find_wish_by_text(text)
    
    async def reset_wish(self, user_id: int) -> bool:
        return await self.wishes.reset_wish(user_id)
    
    async def reset_wish_by_username(self, username: str) -> dict | None:
        return await self.wishes.reset_wish_by_username(username)
    
    # --- Settings methods ---
    async def get_setting(self, key: str) -> str | None:
        return await self.settings.get_setting(key)
    
    async def set_setting(self, key: str, value: str):
        return await self.settings.set_setting(key, value)
    
    async def delete_setting(self, key: str):
        return await self.settings.delete_setting(key)
    
    async def get_reply_message_id(self) -> int | None:
        return await self.settings.get_reply_message_id()
    
    async def set_reply_message_id(self, message_id: int):
        return await self.settings.set_reply_message_id(message_id)
    
    async def clear_reply_message_id(self):
        return await self.settings.clear_reply_message_id()
    
    async def get_bot_enabled(self) -> bool:
        return await self.settings.get_bot_enabled()
    
    async def set_bot_enabled(self, enabled: bool):
        return await self.settings.set_bot_enabled(enabled)
    
    async def get_last_broadcast_time(self) -> float | None:
        return await self.settings.get_last_broadcast_time()
    
    async def set_last_broadcast_time(self, timestamp: float):
        return await self.settings.set_last_broadcast_time(timestamp)
    
    # --- Stats methods ---
    async def get_users_count(self) -> int:
        return await self.stats.get_users_count()
    
    async def get_wishes_count(self) -> int:
        return await self.stats.get_wishes_count()
    
    async def get_all_participants_data(self):
        return await self.stats.get_all_participants_data()


# Global database instance
db = Database(str(DB_PATH))
