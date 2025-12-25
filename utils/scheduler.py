import asyncio
import logging
import random
from aiogram import Bot

from config.config import CHAT_ID
from data.database import db

logger = logging.getLogger(__name__)


async def broadcast_random_wish(bot: Bot) -> None:
    """Публикует случайное пожелание в чат (или как комментарий к посту)."""
    if not CHAT_ID:
        logger.warning("CHAT_ID не установлен, пропускаем публикацию")
        return
    
    wish = await db.get_random_wish()
    if not wish:
        logger.info("Нет пожеланий для публикации")
        return

    username = f"@{wish['username']}" if wish['username'] else f"ID: {wish['user_id']}"
    text = (
        f"🎄 Новогоднее пожелание от {username}:\n"
        f"<blockquote>{wish['text']}</blockquote>"
    )
    
    # Получаем ID сообщения для комментариев
    reply_to = await db.get_reply_message_id()
    
    try:
        if reply_to:
            # Отправляем как комментарий к посту
            await bot.send_message(
                CHAT_ID, 
                text, 
                parse_mode="HTML",
                reply_to_message_id=reply_to
            )
            logger.info(f"Опубликовано пожелание от {username} как комментарий к посту {reply_to}")
        else:
            # Отправляем как обычное сообщение
            await bot.send_message(CHAT_ID, text, parse_mode="HTML")
            logger.info(f"Опубликовано пожелание от {username}")
    except Exception as e:
        logger.error(f"Ошибка публикации пожелания: {e}")


def setup_scheduler(bot: Bot):
    """Создаёт задачу для публикации случайного пожелания каждый час."""
    async def hourly_scheduler_loop():
        # Начальная задержка - 1 час
        initial_delay = 60 * 60
        logger.info(f"Планировщик запущен. Первое рандомное пожелание через 1 час.")
        await asyncio.sleep(initial_delay)
        
        while True:
            await broadcast_random_wish(bot)
            wait_time = 60 * 60  # 1 час
            logger.info(f"Следующее рандомное пожелание через 1 час")
            await asyncio.sleep(wait_time)

    return hourly_scheduler_loop
