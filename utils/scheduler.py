"""Scheduler module for periodic wish broadcasting.

Uses APScheduler for robust job scheduling with:
- Persistent job tracking via database
- Graceful handling of missed jobs
- Proper async support
"""
import logging
import time
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.config import CHAT_ID
from data.database import db

logger = logging.getLogger(__name__)

BROADCAST_INTERVAL_SECONDS = 60 * 60  # 1 hour


async def broadcast_random_wish(bot: Bot) -> None:
    """Publish a random wish to the chat (or as a comment to a post)."""
    # Check if bot is enabled
    if not await db.get_bot_enabled():
        logger.info("Bot is disabled, skipping broadcast")
        return
    
    if not CHAT_ID:
        logger.warning("CHAT_ID not set, skipping broadcast")
        return
    
    wish = await db.get_random_wish()
    if not wish:
        logger.info("No wishes to broadcast")
        return

    username = f"@{wish['username']}" if wish['username'] else f"ID: {wish['user_id']}"
    text = (
        f"🎄 Новогоднее пожелание от {username}:\n"
        f"<blockquote>{wish['text']}</blockquote>"
    )
    
    # Get reply message ID for comments
    reply_to = await db.get_reply_message_id()
    
    try:
        if reply_to:
            await bot.send_message(
                CHAT_ID, 
                text, 
                parse_mode="HTML",
                reply_to_message_id=reply_to
            )
            logger.info(f"Published wish from {username} as comment to post {reply_to}")
        else:
            await bot.send_message(CHAT_ID, text, parse_mode="HTML")
            logger.info(f"Published wish from {username}")
        
        # Save broadcast time
        await db.set_last_broadcast_time(time.time())
    except Exception as e:
        logger.error(f"Error broadcasting wish: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Create and configure the APScheduler instance.
    
    Returns:
        AsyncIOScheduler: Configured scheduler instance (not started).
    """
    scheduler = AsyncIOScheduler()
    
    # Add the hourly broadcast job
    scheduler.add_job(
        broadcast_random_wish,
        trigger=IntervalTrigger(seconds=BROADCAST_INTERVAL_SECONDS),
        args=[bot],
        id="hourly_wish_broadcast",
        name="Broadcast Random Wish",
        replace_existing=True,
        misfire_grace_time=300,  # 5 minutes grace for missed jobs
    )
    
    logger.info(f"Scheduler configured: wish broadcast every {BROADCAST_INTERVAL_SECONDS // 60} minutes")
    
    return scheduler


async def check_and_run_missed_broadcast(bot: Bot) -> None:
    """Check if a broadcast was missed and run it immediately if needed."""
    last_broadcast = await db.get_last_broadcast_time()
    current_time = time.time()
    
    if last_broadcast:
        elapsed = current_time - last_broadcast
        if elapsed >= BROADCAST_INTERVAL_SECONDS:
            logger.info("Missed broadcast detected, running now...")
            await broadcast_random_wish(bot)
    else:
        # First run - don't broadcast immediately, wait for first interval
        logger.info("First run detected, waiting for first scheduled broadcast")
