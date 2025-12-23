import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config.config import BOT_TOKEN
from data.database import db
from apps.handlers import common, wishes, tickets, admin
from utils.scheduler import setup_scheduler

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stdout
    )

    if not BOT_TOKEN:
        logging.error("BOT_TOKEN is not set!")
        return

    # Initialize database
    await db.init()

    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers
    dp.include_router(common.router)
    dp.include_router(wishes.router)
    dp.include_router(tickets.router)
    dp.include_router(admin.router)

    # Start scheduler
    scheduler_task = setup_scheduler(bot)
    asyncio.create_task(scheduler_task())

    # Start polling
    logging.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped.")
