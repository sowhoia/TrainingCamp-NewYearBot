"""Settings repository - handles key-value settings storage."""
from data.repositories.base import BaseRepository


class SettingsRepository(BaseRepository):
    """Repository for bot settings."""
    
    async def get_setting(self, key: str) -> str | None:
        """Get a setting value by key."""
        async with self._get_connection() as db:
            async with db.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None
    
    async def set_setting(self, key: str, value: str):
        """Set a setting value."""
        async with self._get_connection() as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            await db.commit()
    
    async def delete_setting(self, key: str):
        """Delete a setting."""
        async with self._get_connection() as db:
            await db.execute("DELETE FROM settings WHERE key = ?", (key,))
            await db.commit()
    
    # Convenience methods for common settings
    
    async def get_reply_message_id(self) -> int | None:
        """Get the message ID for comments."""
        value = await self.get_setting("reply_message_id")
        return int(value) if value else None
    
    async def set_reply_message_id(self, message_id: int):
        """Set the message ID for comments."""
        await self.set_setting("reply_message_id", str(message_id))
    
    async def clear_reply_message_id(self):
        """Clear the reply message ID."""
        await self.delete_setting("reply_message_id")
    
    async def get_bot_enabled(self) -> bool:
        """Check if bot is enabled."""
        value = await self.get_setting("bot_enabled")
        return value != "false"  # Enabled by default
    
    async def set_bot_enabled(self, enabled: bool):
        """Set bot enabled status."""
        await self.set_setting("bot_enabled", "true" if enabled else "false")
    
    async def get_last_broadcast_time(self) -> float | None:
        """Get last broadcast timestamp."""
        value = await self.get_setting("last_broadcast_time")
        return float(value) if value else None
    
    async def set_last_broadcast_time(self, timestamp: float):
        """Set last broadcast timestamp."""
        await self.set_setting("last_broadcast_time", str(timestamp))
