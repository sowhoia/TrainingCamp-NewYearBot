"""Wish management handlers - reset wishes by username or forwarded message."""
import re
import html

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatType

from config.config import ADMIN_IDS
from data.database import db
from utils.keyboards.inline import get_admin_cancel_button
from apps.handlers.admin.utils import AdminState

router = Router()


@router.callback_query(F.data == "admin_reset_wish", F.from_user.id.in_(ADMIN_IDS))
async def admin_reset_wish_start(callback: types.CallbackQuery, state: FSMContext):
    """Start wish reset process by username."""
    await callback.answer()
    await callback.message.edit_text(
        "👤 <b>Введите username пользователя</b>\n\n"
        "Можно с @ или без. Пример: <code>@username</code> или <code>username</code>\n\n"
        "Пожелание будет удалено, билеты изъяты.",
        parse_mode="HTML",
        reply_markup=get_admin_cancel_button()
    )
    await state.set_state(AdminState.waiting_for_username_to_reset)


@router.message(AdminState.waiting_for_username_to_reset, F.from_user.id.in_(ADMIN_IDS))
async def process_username_to_reset(message: types.Message, state: FSMContext):
    """Process username for wish reset."""
    username = message.text.strip()
    
    user = await db.find_user_by_username(username)
    
    if not user:
        await message.answer(
            f"❌ Пользователь <code>{username}</code> не найден.\n"
            "Попробуйте ещё раз или нажмите «Отменить».",
            parse_mode="HTML",
            reply_markup=get_admin_cancel_button()
        )
        return
    
    if not user['has_wished']:
        await message.answer(
            f"❌ У пользователя <code>@{user['username']}</code> нет пожелания.\n"
            "Попробуйте другого пользователя или нажмите «Отменить».",
            parse_mode="HTML",
            reply_markup=get_admin_cancel_button()
        )
        return
    
    success = await db.reset_wish(user['user_id'])
    
    if success:
        username_display = f"@{user['username']}" if user['username'] else f"ID: {user['user_id']}"
        referrer_info = ""
        if user['referrer_id']:
            referrer_info = f"\n👤 Реферер: <code>{user['referrer_id']}</code> (−1 билет)"
        
        await message.answer(
            f"✅ Пожелание сброшено!\n\n"
            f"👤 Пользователь: {username_display}\n"
            f"🆔 User ID: <code>{user['user_id']}</code>\n"
            f"🎫 Билет изъят (−1){referrer_info}",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Ошибка при сбросе пожелания.")
    
    await state.clear()


@router.message(F.forward_from_chat, F.from_user.id.in_(ADMIN_IDS), F.chat.type == ChatType.PRIVATE)
async def handle_forwarded_wish(message: types.Message):
    """Reset wish when admin forwards a wish message from chat."""
    if not message.text:
        return
    
    # Parse wish text from forwarded message
    # Format: "🎄 Новогоднее пожелание от @username:\n<blockquote>текст</blockquote>"
    wish_text = None
    text = message.text or message.caption or ""
    
    # Try to find blockquote via HTML entities
    if message.html_text:
        match = re.search(r'<blockquote>(.*?)</blockquote>', message.html_text, re.DOTALL)
        if match:
            wish_text = html.unescape(match.group(1)).strip()
    
    # If blockquote not found, try text after first line
    if not wish_text:
        lines = text.split('\n', 1)
        if len(lines) > 1 and "пожелание от" in lines[0].lower():
            wish_text = lines[1].strip()
    
    if not wish_text:
        await message.answer(
            "❌ Не удалось распознать пожелание.\n"
            "Убедитесь, что пересылаете сообщение с пожеланием из чата."
        )
        return
    
    wish = await db.find_wish_by_text(wish_text)
    if not wish:
        preview = f"{wish_text[:100]}..." if len(wish_text) > 100 else wish_text
        await message.answer(
            f"❌ Пожелание не найдено в базе данных.\n"
            f"Текст: <i>{preview}</i>",
            parse_mode="HTML"
        )
        return
    
    user = await db.get_user(wish['user_id'])
    success = await db.reset_wish(wish['user_id'])
    
    if success:
        username_display = f"@{user['username']}" if user and user['username'] else f"ID: {wish['user_id']}"
        referrer_info = ""
        if user and user['referrer_id']:
            referrer_info = f"\n👤 Реферер: <code>{user['referrer_id']}</code> (−1 билет)"
        
        await message.answer(
            f"✅ Пожелание сброшено!\n\n"
            f"👤 Пользователь: {username_display}\n"
            f"🆔 User ID: <code>{wish['user_id']}</code>\n"
            f"🎫 Билет изъят (−1){referrer_info}",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Ошибка при сбросе пожелания.")


@router.callback_query(F.data == "admin_cancel_input", F.from_user.id.in_(ADMIN_IDS))
async def admin_cancel_input(callback: types.CallbackQuery, state: FSMContext):
    """Cancel input and return to admin panel."""
    from apps.handlers.admin.menu import get_admin_panel_text
    from utils.keyboards.inline import get_admin_menu
    
    await state.clear()
    await callback.answer("❌ Ввод отменён")
    
    text, bot_enabled, _ = await get_admin_panel_text()
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_admin_menu(bot_enabled)
    )
