"""Admin menu handler - main dashboard and navigation."""
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums import ChatType

from config.config import ADMIN_IDS
from data.database import db
from utils.keyboards.inline import get_admin_menu

router = Router()


async def get_admin_panel_text() -> tuple[str, bool, int | None]:
    """Get admin panel text and status data."""
    users_count = await db.get_users_count()
    wishes_count = await db.get_wishes_count()
    reply_id = await db.get_reply_message_id()
    bot_enabled = await db.get_bot_enabled()
    
    post_status = f"✅ ID: {reply_id}" if reply_id else "❌ Не установлен"
    bot_status = "🟢 Включен" if bot_enabled else "🔴 Выключен"
    
    text = (
        f"👨‍💼 <b>Админ-панель</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Всего пользователей: {users_count}\n"
        f"• Оставлено пожеланий: {wishes_count}\n\n"
        f"🤖 <b>Статус бота:</b> {bot_status}\n"
        f"💬 <b>Пост для комментариев:</b> {post_status}"
    )
    
    return text, bot_enabled, reply_id


@router.message(Command("admin"), F.from_user.id.in_(ADMIN_IDS), F.chat.type == ChatType.PRIVATE)
async def cmd_admin(message: types.Message):
    """Admin panel with statistics and menu."""
    text, bot_enabled, _ = await get_admin_panel_text()
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_admin_menu(bot_enabled)
    )


@router.callback_query(F.data == "admin_back", F.from_user.id.in_(ADMIN_IDS))
async def admin_back(callback: types.CallbackQuery):
    """Return to main admin menu."""
    text, bot_enabled, _ = await get_admin_panel_text()
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_admin_menu(bot_enabled)
    )


@router.callback_query(F.data == "admin_toggle_bot", F.from_user.id.in_(ADMIN_IDS))
async def admin_toggle_bot(callback: types.CallbackQuery):
    """Toggle bot enabled status."""
    current_status = await db.get_bot_enabled()
    new_status = not current_status
    await db.set_bot_enabled(new_status)
    
    status_text = "🟢 включен" if new_status else "🔴 выключен"
    await callback.answer(f"Бот {status_text}")
    
    text, _, _ = await get_admin_panel_text()
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_admin_menu(new_status)
    )
