"""Ticket management handlers - give tickets to users."""
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config.config import ADMIN_IDS
from data.database import db
from utils.keyboards.inline import get_admin_cancel_button
from apps.handlers.admin.utils import AdminState, get_ticket_word

router = Router()


def get_skip_message_button() -> InlineKeyboardMarkup:
    """Button to skip message when giving tickets."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏩ Без сообщения", callback_data="admin_skip_ticket_message")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="admin_cancel_input")]
    ])


@router.callback_query(F.data == "admin_give_tickets", F.from_user.id.in_(ADMIN_IDS))
async def admin_give_tickets_start(callback: types.CallbackQuery, state: FSMContext):
    """Start ticket giving process."""
    await callback.answer()
    await callback.message.edit_text(
        "🎁 <b>Выдача билетов пользователю</b>\n\n"
        "👤 Введите username пользователя:\n\n"
        "<i>Можно с @ или без. Пример: @username или username</i>",
        parse_mode="HTML",
        reply_markup=get_admin_cancel_button()
    )
    await state.set_state(AdminState.waiting_for_username_to_give_tickets)


@router.message(AdminState.waiting_for_username_to_give_tickets, F.from_user.id.in_(ADMIN_IDS))
async def process_username_for_tickets(message: types.Message, state: FSMContext):
    """Process username for ticket giving."""
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
    
    await state.update_data(target_user_id=user['user_id'], target_username=user['username'])
    
    await message.answer(
        f"👤 Пользователь: <b>@{user['username']}</b>\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"🎫 Текущих билетов: <b>{user['tickets']}</b>\n\n"
        "📝 <b>Введите количество билетов для выдачи:</b>",
        parse_mode="HTML",
        reply_markup=get_admin_cancel_button()
    )
    await state.set_state(AdminState.waiting_for_ticket_count)


@router.message(AdminState.waiting_for_ticket_count, F.from_user.id.in_(ADMIN_IDS))
async def process_ticket_count(message: types.Message, state: FSMContext):
    """Process ticket count."""
    try:
        count = int(message.text.strip())
        if count <= 0:
            raise ValueError("Count must be positive")
    except ValueError:
        await message.answer(
            "❌ Введите корректное положительное число билетов.",
            reply_markup=get_admin_cancel_button()
        )
        return
    
    await state.update_data(ticket_count=count)
    
    data = await state.get_data()
    username = data.get('target_username', 'N/A')
    
    await message.answer(
        f"🎁 Выдаём <b>{count}</b> билетов пользователю <b>@{username}</b>\n\n"
        "💬 <b>Введите сообщение для пользователя</b> (опционально):\n\n"
        "<i>Это сообщение будет отправлено пользователю вместе с уведомлением о билетах.\n"
        "Или нажмите «Без сообщения» для отправки стандартного уведомления.</i>",
        parse_mode="HTML",
        reply_markup=get_skip_message_button()
    )
    await state.set_state(AdminState.waiting_for_ticket_message)


@router.callback_query(F.data == "admin_skip_ticket_message", F.from_user.id.in_(ADMIN_IDS))
async def skip_ticket_message(callback: types.CallbackQuery, state: FSMContext, bot):
    """Skip message and give tickets."""
    await callback.answer()
    await _give_tickets_and_notify(callback.message, state, bot, custom_message=None)


@router.message(AdminState.waiting_for_ticket_message, F.from_user.id.in_(ADMIN_IDS))
async def process_ticket_message(message: types.Message, state: FSMContext, bot):
    """Process message and give tickets."""
    custom_message = message.text.strip() if message.text else None
    await _give_tickets_and_notify(message, state, bot, custom_message=custom_message)


async def _give_tickets_and_notify(
    message_ctx: types.Message, 
    state: FSMContext, 
    bot,
    custom_message: str | None
):
    """Give tickets and send notification to user."""
    data = await state.get_data()
    user_id = data.get('target_user_id')
    username = data.get('target_username', 'N/A')
    count = data.get('ticket_count', 0)
    
    if not user_id or not count:
        await message_ctx.answer("❌ Ошибка: данные не найдены. Попробуйте снова.")
        await state.clear()
        return
    
    # Give tickets
    new_total = await db.add_tickets_to_user(user_id, count)
    
    if new_total is None:
        await message_ctx.answer("❌ Ошибка: пользователь не найден.")
        await state.clear()
        return
    
    # Build user notification
    ticket_word = get_ticket_word(count)
    
    user_notification = (
        f"🎉 <b>Поздравляем!</b>\n\n"
        f"✨ Вы получили <b>{count}</b> дополнительн{'ый' if count == 1 else 'ых'} {ticket_word}!\n"
        f"🎫 Теперь у вас: <b>{new_total}</b> {get_ticket_word(new_total)}"
    )
    
    if custom_message:
        user_notification += f"\n\n💬 <i>{custom_message}</i>"
    
    # Send notification to user
    notification_sent = False
    try:
        await bot.send_message(user_id, user_notification, parse_mode="HTML")
        notification_sent = True
    except Exception:
        pass  # User may have blocked the bot
    
    # Admin report
    notification_status = "✅ отправлено" if notification_sent else "❌ не доставлено (возможно, бот заблокирован)"
    
    admin_report = (
        f"✅ <b>Билеты выданы!</b>\n\n"
        f"👤 Пользователь: @{username}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"🎫 Выдано билетов: <b>+{count}</b>\n"
        f"📊 Всего билетов: <b>{new_total}</b>\n"
        f"📬 Уведомление: {notification_status}"
    )
    
    if custom_message:
        admin_report += f"\n💬 Сообщение: <i>{custom_message[:100]}{'...' if len(custom_message) > 100 else ''}</i>"
    
    await message_ctx.answer(admin_report, parse_mode="HTML")
    await state.clear()
