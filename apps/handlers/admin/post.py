"""Post management handlers - set/clear reply message for comments."""
import re

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from config.config import ADMIN_IDS
from data.database import db
from utils.keyboards.inline import get_admin_cancel_button, get_admin_menu
from apps.handlers.admin.utils import AdminState

router = Router()


@router.callback_query(F.data == "admin_set_post", F.from_user.id.in_(ADMIN_IDS))
async def admin_set_post(callback: types.CallbackQuery, state: FSMContext):
    """Start post setting process."""
    await callback.answer()
    await callback.message.edit_text(
        "📨 <b>Отправьте ссылку на сообщение в чате</b>\n\n"
        "Формат: https://t.me/c/XXXXXXXXXX/XXX\n\n"
        "Это сообщение должно быть копией поста канала в группе-обсуждении.",
        parse_mode="HTML",
        reply_markup=get_admin_cancel_button()
    )
    await state.set_state(AdminState.waiting_for_post_link)


@router.message(AdminState.waiting_for_post_link, F.from_user.id.in_(ADMIN_IDS))
async def process_post_link(message: types.Message, state: FSMContext):
    """Process post link."""
    text = message.text.strip()
    
    message_id = None
    
    # Pattern 1: Private link - t.me/c/CHAT_ID/MESSAGE_ID
    match_private = re.search(r't\.me/c/(\d+)/(\d+)', text)
    
    # Pattern 2: Public link - t.me/username/MESSAGE_ID
    match_public = re.search(r't\.me/([a-zA-Z_][a-zA-Z0-9_]*)/(\d+)', text)
    
    if match_private:
        message_id = int(match_private.group(2))
    elif match_public:
        message_id = int(match_public.group(2))
    else:
        # Try as plain ID
        try:
            message_id = int(text)
        except ValueError:
            pass
    
    if message_id:
        await db.set_reply_message_id(message_id)
        await message.answer(
            f"✅ Пост для комментариев установлен!\n"
            f"ID сообщения: <code>{message_id}</code>",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    await message.answer(
        "❌ Не удалось распознать ссылку или ID.\n"
        "Попробуйте ещё раз или нажмите кнопку «Отменить»."
    )


@router.callback_query(F.data == "admin_clear_post", F.from_user.id.in_(ADMIN_IDS))
async def admin_clear_post(callback: types.CallbackQuery):
    """Clear post binding."""
    await db.clear_reply_message_id()
    await callback.answer("✅ Привязка к посту удалена")
    
    # Update menu
    from apps.handlers.admin.menu import get_admin_panel_text
    
    users_count = await db.get_users_count()
    wishes_count = await db.get_wishes_count()
    bot_enabled = await db.get_bot_enabled()
    bot_status = "🟢 Включен" if bot_enabled else "🔴 Выключен"
    
    await callback.message.edit_text(
        f"👨‍💼 <b>Админ-панель</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Всего пользователей: {users_count}\n"
        f"• Оставлено пожеланий: {wishes_count}\n\n"
        f"🤖 <b>Статус бота:</b> {bot_status}\n"
        f"💬 <b>Пост для комментариев:</b> ❌ Не установлен",
        parse_mode="HTML",
        reply_markup=get_admin_menu(bot_enabled)
    )
