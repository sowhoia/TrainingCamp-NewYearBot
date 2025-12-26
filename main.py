import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config.config import BOT_TOKEN
from data.database import db
from apps.handlers import common, wishes, tickets
from apps.handlers.admin import router as admin_router
from utils.scheduler import setup_scheduler, check_and_run_missed_broadcast
from utils.middlewares import ErrorHandlerMiddleware

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
    dp.include_router(admin_router)

    # Register middleware
    dp.update.outer_middleware(ErrorHandlerMiddleware())

    # Setup and start scheduler
    scheduler = setup_scheduler(bot)
    scheduler.start()
    
    # Check for missed broadcasts
    await check_and_run_missed_broadcast(bot)

    # Start polling
    logging.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped.")
