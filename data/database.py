import aiosqlite
from config.config import DB_PATH
from datetime import datetime

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init(self):
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

    async def get_setting(self, key: str) -> str | None:
        """Получить значение настройки."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def set_setting(self, key: str, value: str):
        """Установить значение настройки."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            await db.commit()

    async def delete_setting(self, key: str):
        """Удалить настройку."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM settings WHERE key = ?", (key,))
            await db.commit()

    async def get_reply_message_id(self) -> int | None:
        """Получить ID сообщения для комментариев."""
        value = await self.get_setting("reply_message_id")
        return int(value) if value else None

    async def set_reply_message_id(self, message_id: int):
        """Установить ID сообщения для комментариев."""
        await self.set_setting("reply_message_id", str(message_id))

    async def clear_reply_message_id(self):
        """Очистить ID сообщения для комментариев."""
        await self.delete_setting("reply_message_id")

    async def get_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()

    async def create_user(self, user_id: int, username: str, referrer_id: int = None):
        """Создать нового пользователя с реферером.
        
        Проверяет существование реферера перед сохранением.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем существование реферера (если указан)
            valid_referrer_id = None
            if referrer_id is not None:
                async with db.execute(
                    "SELECT user_id FROM users WHERE user_id = ?", (referrer_id,)
                ) as cursor:
                    referrer_exists = await cursor.fetchone()
                    if referrer_exists:
                        valid_referrer_id = referrer_id
            
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)",
                (user_id, username, valid_referrer_id)
            )
            await db.commit()

    async def update_username(self, user_id: int, username: str):
        """Обновить username пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET username = ? WHERE user_id = ?",
                (username, user_id)
            )
            await db.commit()

    async def add_wish(self, user_id: int, text: str):
        """Добавить пожелание с атомарным начислением билетов.
        
        Использует транзакцию для гарантии консистентности данных.
        Returns: True если пожелание добавлено, False если уже есть пожелание.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Включаем режим транзакции
            await db.execute("BEGIN IMMEDIATE")
            
            try:
                # Получаем данные пользователя внутри транзакции
                db.row_factory = aiosqlite.Row
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
                
                # Сохраняем пожелание
                await db.execute(
                    "INSERT INTO wishes (user_id, text) VALUES (?, ?)", 
                    (user_id, text)
                )
                
                # Обновляем билеты и статус пользователя
                await db.execute(
                    "UPDATE users SET tickets = tickets + 1, has_wished = TRUE WHERE user_id = ?", 
                    (user_id,)
                )
                
                # Начисляем бонус рефереру (если есть и существует)
                referrer_id = user['referrer_id']
                if referrer_id:
                    # Проверяем что реферер существует и начисляем билет
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
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM wishes WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()

    async def get_referral_count(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE referrer_id = ? AND has_wished = TRUE", 
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_random_wish(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT w.text, u.username, u.user_id 
                FROM wishes w 
                JOIN users u ON w.user_id = u.user_id 
                ORDER BY RANDOM() LIMIT 1
            """) as cursor:
                return await cursor.fetchone()

    async def get_all_participants_data(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT u.user_id, u.username, w.text, u.tickets
                FROM users u
                LEFT JOIN wishes w ON u.user_id = w.user_id
                WHERE u.has_wished = TRUE
            """
            async with db.execute(query) as cursor:
                return await cursor.fetchall()

    async def get_users_count(self) -> int:
        """Получить общее количество пользователей."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_wishes_count(self) -> int:
        """Получить количество оставленных пожеланий."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM wishes") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0


db = Database(str(DB_PATH))
