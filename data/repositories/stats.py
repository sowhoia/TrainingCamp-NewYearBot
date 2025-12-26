"""Stats repository - handles statistics and data export queries."""
from data.repositories.base import BaseRepository


class StatsRepository(BaseRepository):
    """Repository for statistics and exports."""
    
    async def get_users_count(self) -> int:
        """Get total user count."""
        async with self._get_connection() as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    async def get_wishes_count(self) -> int:
        """Get total wishes count."""
        async with self._get_connection() as db:
            async with db.execute("SELECT COUNT(*) FROM wishes") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    async def get_all_participants_data(self):
        """Get all participants with wishes for export."""
        async with self._get_connection() as db:
            query = """
                SELECT u.user_id, u.username, w.text, u.tickets
                FROM users u
                LEFT JOIN wishes w ON u.user_id = w.user_id
                WHERE u.has_wished = TRUE
            """
            async with db.execute(query) as cursor:
                return await cursor.fetchall()
