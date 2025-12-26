"""Base repository with shared database connection logic."""
import aiosqlite
from config.config import DB_PATH


class BaseRepository:
    """Base class for all repositories."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
    
    async def _get_connection(self) -> aiosqlite.Connection:
        """Get a new database connection."""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        return conn
