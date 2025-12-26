"""User repository - handles all user-related database operations."""
import aiosqlite
from data.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Repository for user operations."""
    
    async def get_user(self, user_id: int):
        """Get user by ID."""
        async with await self._get_connection() as db:
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                return await cursor.fetchone()
    
    async def create_user(self, user_id: int, username: str, referrer_id: int = None):
        """Create a new user with optional referrer.
        
        Validates referrer exists before saving.
        """
        async with await self._get_connection() as db:
            # Validate referrer exists
            valid_referrer_id = None
            if referrer_id is not None:
                async with db.execute(
                    "SELECT user_id FROM users WHERE user_id = ?", (referrer_id,)
                ) as cursor:
                    if await cursor.fetchone():
                        valid_referrer_id = referrer_id
            
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)",
                (user_id, username, valid_referrer_id)
            )
            await db.commit()
    
    async def update_username(self, user_id: int, username: str):
        """Update user's username."""
        async with await self._get_connection() as db:
            await db.execute(
                "UPDATE users SET username = ? WHERE user_id = ?",
                (username, user_id)
            )
            await db.commit()
    
    async def find_user_by_username(self, username: str):
        """Find user by username (case-insensitive, without @)."""
        clean_username = username.lstrip("@")
        async with await self._get_connection() as db:
            async with db.execute(
                "SELECT * FROM users WHERE LOWER(username) = LOWER(?)", 
                (clean_username,)
            ) as cursor:
                return await cursor.fetchone()
    
    async def add_tickets_to_user(self, user_id: int, count: int) -> int | None:
        """Add tickets to user. Returns new ticket count or None if user not found."""
        async with await self._get_connection() as db:
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                if not await cursor.fetchone():
                    return None
            
            await db.execute(
                "UPDATE users SET tickets = tickets + ? WHERE user_id = ?",
                (count, user_id)
            )
            await db.commit()
            
            async with db.execute(
                "SELECT tickets FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row['tickets'] if row else None
    
    async def get_referral_count(self, user_id: int) -> int:
        """Get count of referrals who have left a wish (earn tickets)."""
        async with await self._get_connection() as db:
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE referrer_id = ? AND has_wished = TRUE", 
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    async def get_total_referrals(self, user_id: int) -> int:
        """Get total count of invited users (regardless of wish status)."""
        async with await self._get_connection() as db:
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE referrer_id = ?", 
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
