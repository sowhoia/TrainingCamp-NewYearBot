import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus

from config.config import REQUIRED_CHANNEL, REQUIRED_CHAT, CHAT_INVITE_LINK, CHANNEL_INVITE_LINK

logger = logging.getLogger(__name__)


async def check_subscription(bot: Bot, user_id: int) -> dict:
    """
    Проверяет подписку пользователя на канал и чат.
    
    Returns:
        dict: {"channel": bool, "chat": bool, "all_ok": bool}
    """
    result = {"channel": False, "chat": False, "all_ok": False}
    
    # Проверяем канал
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        result["channel"] = member.status not in [
            ChatMemberStatus.LEFT, 
            ChatMemberStatus.KICKED
        ]
    except Exception as e:
        logger.warning(f"Ошибка проверки подписки на канал: {e}")
        result["channel"] = False
    
    # Проверяем чат
    try:
        member = await bot.get_chat_member(REQUIRED_CHAT, user_id)
        result["chat"] = member.status not in [
            ChatMemberStatus.LEFT, 
            ChatMemberStatus.KICKED
        ]
    except Exception as e:
        logger.warning(f"Ошибка проверки подписки на чат: {e}")
        result["chat"] = False
    
    result["all_ok"] = result["channel"] and result["chat"]
    return result


def get_subscription_keyboard(sub_status: dict = None) -> InlineKeyboardMarkup:
    """Клавиатура с кнопками для подписки с отображением статуса."""
    from config.config import REQUIRED_CHANNEL, REQUIRED_CHAT, CHANNEL_INVITE_LINK, CHAT_INVITE_LINK
    
    # Определяем URL для канала
    if CHANNEL_INVITE_LINK:
        channel_url = CHANNEL_INVITE_LINK
    elif REQUIRED_CHANNEL.startswith('@'):
        channel_url = f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}"
    else:
        # Если это числовой ID без invite-ссылки, используем заглушку
        channel_url = "https://t.me/"
    
    # Определяем URL для чата
    if CHAT_INVITE_LINK:
        chat_url = CHAT_INVITE_LINK
    elif REQUIRED_CHAT.startswith('@'):
        chat_url = f"https://t.me/{REQUIRED_CHAT.lstrip('@')}"
    else:
        # Если это числовой ID без invite-ссылки, используем заглушку
        chat_url = "https://t.me/"
    
    # Определяем статусы для кнопок
    if sub_status:
        chat_icon = "✅" if sub_status["chat"] else "❌"
        channel_icon = "✅" if sub_status["channel"] else "❌"
    else:
        chat_icon = "❌"
        channel_icon = "❌"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{chat_icon} Чат", 
                url=chat_url
            ),
            InlineKeyboardButton(
                text=f"{channel_icon} Канал", 
                url=channel_url
            )
        ],
        [InlineKeyboardButton(
            text="✅ Проверить подписку", 
            callback_data="check_subscription"
        )]
    ])


def get_subscription_text(sub_status: dict = None) -> str:
    """Текст с информацией о необходимых подписках."""
    return "📋 <b>Для участия в розыгрыше нужно подписаться:</b>"
