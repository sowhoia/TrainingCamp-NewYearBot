import asyncio
import logging
import random
import time
from aiogram import Bot

from config.config import CHAT_ID
from data.database import db

logger = logging.getLogger(__name__)

BROADCAST_INTERVAL = 60 * 60  # 1 час в секундах


async def broadcast_random_wish(bot: Bot) -> None:
    """Публикует случайное пожелание в чат (или как комментарий к посту)."""
    # Проверяем, включен ли бот
    if not await db.get_bot_enabled():
        logger.info("Бот отключен, пропускаем публикацию")
        return
    
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
        
        # Сохраняем время публикации
        await db.set_last_broadcast_time(time.time())
    except Exception as e:
        logger.error(f"Ошибка публикации пожелания: {e}")


def setup_scheduler(bot: Bot):
    """Создаёт задачу для публикации случайного пожелания каждый час."""
    async def hourly_scheduler_loop():
        # Проверяем время последней публикации
        last_broadcast = await db.get_last_broadcast_time()
        current_time = time.time()
        
        if last_broadcast:
            elapsed = current_time - last_broadcast
            remaining = BROADCAST_INTERVAL - elapsed
            
            if remaining > 0:
                logger.info(f"Планировщик запущен. До следующего поста: {remaining / 60:.1f} мин")
                await asyncio.sleep(remaining)
            else:
                # Пора публиковать сразу
                logger.info("Планировщик запущен. Время публикации пропущено, публикуем сейчас.")
                await broadcast_random_wish(bot)
        else:
            # Первый запуск - ждём час
            logger.info(f"Планировщик запущен. Первое рандомное пожелание через 1 час.")
            await asyncio.sleep(BROADCAST_INTERVAL)
            await broadcast_random_wish(bot)
        
        # Основной цикл
        while True:
            await asyncio.sleep(BROADCAST_INTERVAL)
            await broadcast_random_wish(bot)
            logger.info(f"Следующее рандомное пожелание через 1 час")

    return hourly_scheduler_loop

