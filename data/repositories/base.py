"""Base repository with shared database connection logic."""
import aiosqlite
from contextlib import asynccontextmanager
from config.config import DB_PATH


class BaseRepository:
    """Base class for all repositories."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
    
    @asynccontextmanager
    async def _get_connection(self):
        """Get a database connection as async context manager."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db
