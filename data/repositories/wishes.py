"""Wishes repository - handles all wish-related database operations."""
import aiosqlite
from data.repositories.base import BaseRepository


class WishRepository(BaseRepository):
    """Repository for wish operations."""
    
    async def add_wish(self, user_id: int, text: str) -> bool:
        """Add a wish with atomic ticket allocation.
        
        Uses transaction to ensure data consistency.
        Returns True if wish added, False if user already has a wish.
        """
        async with await self._get_connection() as db:
            await db.execute("BEGIN IMMEDIATE")
            
            try:
                async with db.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                ) as cursor:
                    user = await cursor.fetchone()
                
                if not user:
                    await db.execute("ROLLBACK")
                    return False
                    
                if user['has_wished']:
                    await db.execute("ROLLBACK")
                    return False
                
                # Save wish
                await db.execute(
                    "INSERT INTO wishes (user_id, text) VALUES (?, ?)", 
                    (user_id, text)
                )
                
                # Update user tickets and status
                await db.execute(
                    "UPDATE users SET tickets = tickets + 1, has_wished = TRUE WHERE user_id = ?", 
                    (user_id,)
                )
                
                # Award referrer bonus if exists
                referrer_id = user['referrer_id']
                if referrer_id:
                    await db.execute(
                        "UPDATE users SET tickets = tickets + 1 WHERE user_id = ?", 
                        (referrer_id,)
                    )
                
                await db.execute("COMMIT")
                return True
                
            except Exception as e:
                await db.execute("ROLLBACK")
                raise e
    
    async def get_user_wish(self, user_id: int):
        """Get user's wish."""
        async with await self._get_connection() as db:
            async with db.execute(
                "SELECT * FROM wishes WHERE user_id = ?", (user_id,)
            ) as cursor:
                return await cursor.fetchone()
    
    async def get_random_wish(self):
        """Get a random wish with user info."""
        async with await self._get_connection() as db:
            async with db.execute("""
                SELECT w.text, u.username, u.user_id 
                FROM wishes w 
                JOIN users u ON w.user_id = u.user_id 
                ORDER BY RANDOM() LIMIT 1
            """) as cursor:
                return await cursor.fetchone()
    
    async def find_wish_by_text(self, text: str):
        """Find wish by exact text match."""
        async with await self._get_connection() as db:
            async with db.execute(
                "SELECT * FROM wishes WHERE text = ?", (text,)
            ) as cursor:
                return await cursor.fetchone()
    
    async def reset_wish(self, user_id: int) -> bool:
        """Reset user's wish and deduct tickets atomically."""
        async with await self._get_connection() as db:
            await db.execute("BEGIN IMMEDIATE")
            try:
                async with db.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                ) as cursor:
                    user = await cursor.fetchone()
                
                if not user or not user['has_wished']:
                    await db.execute("ROLLBACK")
                    return False
                
                # Delete wish
                await db.execute("DELETE FROM wishes WHERE user_id = ?", (user_id,))
                
                # Deduct 1 ticket from user
                await db.execute(
                    "UPDATE users SET tickets = MAX(0, tickets - 1), has_wished = FALSE WHERE user_id = ?",
                    (user_id,)
                )
                
                # Deduct 1 ticket from referrer if exists
                if user['referrer_id']:
                    await db.execute(
                        "UPDATE users SET tickets = MAX(0, tickets - 1) WHERE user_id = ?",
                        (user['referrer_id'],)
                    )
                
                await db.execute("COMMIT")
                return True
            except Exception:
                await db.execute("ROLLBACK")
                raise
    
    async def reset_wish_by_username(self, username: str) -> dict | None:
        """Reset wish by username. Returns user data if successful."""
        from data.repositories.users import UserRepository
        user_repo = UserRepository(self.db_path)
        
        user = await user_repo.find_user_by_username(username)
        if not user:
            return None
        
        success = await self.reset_wish(user['user_id'])
        if success:
            return dict(user)
        return None
