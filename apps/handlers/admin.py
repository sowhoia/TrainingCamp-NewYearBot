import csv
import io
import re
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config.config import ADMIN_IDS
from data.database import db
from utils.keyboards.inline import get_admin_export_menu, get_admin_menu, get_admin_cancel_button

router = Router()


class AdminState(StatesGroup):
    waiting_for_post_link = State()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором."""
    return user_id in ADMIN_IDS


@router.message(Command("admin"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_admin(message: types.Message):
    """Админ-панель с статистикой и меню."""
    users_count = await db.get_users_count()
    wishes_count = await db.get_wishes_count()
    reply_id = await db.get_reply_message_id()
    
    post_status = f"✅ ID: {reply_id}" if reply_id else "❌ Не установлен"
    
    await message.answer(
        f"👨‍💼 <b>Админ-панель</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Всего пользователей: {users_count}\n"
        f"• Оставлено пожеланий: {wishes_count}\n\n"
        f"💬 <b>Пост для комментариев:</b> {post_status}",
        parse_mode="HTML",
        reply_markup=get_admin_menu()
    )


@router.callback_query(F.data == "admin_export", F.from_user.id.in_(ADMIN_IDS))
async def admin_export(callback: types.CallbackQuery):
    """Выбор формата экспорта."""
    await callback.message.edit_text(
        "📁 <b>Выберите формат экспорта:</b>",
        parse_mode="HTML",
        reply_markup=get_admin_export_menu()
    )


@router.callback_query(F.data == "admin_set_post", F.from_user.id.in_(ADMIN_IDS))
async def admin_set_post(callback: types.CallbackQuery, state: FSMContext):
    """Начать процесс установки поста для комментариев."""
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
    """Обработка ссылки на пост."""
    text = message.text.strip()
    
    # Парсим ссылку формата https://t.me/c/XXXXXXXXXX/XXX
    match = re.search(r't\.me/c/(\d+)/(\d+)', text)
    
    if match:
        message_id = int(match.group(2))
        await db.set_reply_message_id(message_id)
        await message.answer(
            f"✅ Пост для комментариев установлен!\n"
            f"ID сообщения: <code>{message_id}</code>",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    # Пробуем как просто ID
    try:
        message_id = int(text)
        await db.set_reply_message_id(message_id)
        await message.answer(
            f"✅ Пост для комментариев установлен!\n"
            f"ID сообщения: <code>{message_id}</code>",
            parse_mode="HTML"
        )
        await state.clear()
        return
    except ValueError:
        pass
    
    await message.answer(
        "❌ Не удалось распознать ссылку или ID.\n"
        "Попробуйте ещё раз или нажмите кнопку «Отменить»."
    )


@router.callback_query(F.data == "admin_cancel_input", F.from_user.id.in_(ADMIN_IDS))
async def admin_cancel_input(callback: types.CallbackQuery, state: FSMContext):
    """Отменить ввод данных и вернуться в админ-панель."""
    await state.clear()
    await callback.answer("❌ Ввод отменён")
    
    # Возвращаемся в главное меню админки
    users_count = await db.get_users_count()
    wishes_count = await db.get_wishes_count()
    reply_id = await db.get_reply_message_id()
    
    post_status = f"✅ ID: {reply_id}" if reply_id else "❌ Не установлен"
    
    await callback.message.edit_text(
        f"👨‍💼 <b>Админ-панель</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Всего пользователей: {users_count}\n"
        f"• Оставлено пожеланий: {wishes_count}\n\n"
        f"💬 <b>Пост для комментариев:</b> {post_status}",
        parse_mode="HTML",
        reply_markup=get_admin_menu()
    )


@router.callback_query(F.data == "admin_clear_post", F.from_user.id.in_(ADMIN_IDS))
async def admin_clear_post(callback: types.CallbackQuery):
    """Очистить привязку к посту."""
    await db.clear_reply_message_id()
    await callback.answer("✅ Привязка к посту удалена")
    
    # Обновляем меню
    users_count = await db.get_users_count()
    wishes_count = await db.get_wishes_count()
    
    await callback.message.edit_text(
        f"👨‍💼 <b>Админ-панель</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Всего пользователей: {users_count}\n"
        f"• Оставлено пожеланий: {wishes_count}\n\n"
        f"💬 <b>Пост для комментариев:</b> ❌ Не установлен",
        parse_mode="HTML",
        reply_markup=get_admin_menu()
    )


@router.callback_query(F.data == "admin_back", F.from_user.id.in_(ADMIN_IDS))
async def admin_back(callback: types.CallbackQuery):
    """Вернуться в главное меню админки."""
    users_count = await db.get_users_count()
    wishes_count = await db.get_wishes_count()
    reply_id = await db.get_reply_message_id()
    
    post_status = f"✅ ID: {reply_id}" if reply_id else "❌ Не установлен"
    
    await callback.message.edit_text(
        f"👨‍💼 <b>Админ-панель</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Всего пользователей: {users_count}\n"
        f"• Оставлено пожеланий: {wishes_count}\n\n"
        f"💬 <b>Пост для комментариев:</b> {post_status}",
        parse_mode="HTML",
        reply_markup=get_admin_menu()
    )


@router.callback_query(F.data == "export_csv", F.from_user.id.in_(ADMIN_IDS))
async def export_csv(callback: types.CallbackQuery):
    """Экспорт данных в CSV."""
    await callback.answer("Генерирую CSV...")
    
    data = await db.get_all_participants_data()
    
    if not data:
        await callback.message.answer("❌ Нет участников для выгрузки.")
        return

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ticket Number', 'User ID', 'Username', 'Wish'])
    
    ticket_counter = 1
    for row in data:
        for _ in range(row['tickets']):
            writer.writerow([
                ticket_counter,
                row['user_id'], 
                row['username'] or "N/A", 
                row['text']
            ])
            ticket_counter += 1
            
    output.seek(0)
    
    file_content = output.getvalue().encode('utf-8-sig')  # BOM для Excel
    input_file = types.BufferedInputFile(file_content, filename="raffle_participants.csv")
    
    await callback.message.answer_document(
        input_file, 
        caption=f"📊 Список участников для розыгрыша\n🎫 Всего билетов: {ticket_counter - 1}"
    )


@router.callback_query(F.data == "export_txt", F.from_user.id.in_(ADMIN_IDS))
async def export_txt(callback: types.CallbackQuery):
    """Экспорт данных в TXT - простой формат для рандомайзера."""
    await callback.answer("Генерирую TXT...")
    
    data = await db.get_all_participants_data()
    
    if not data:
        await callback.message.answer("❌ Нет участников для выгрузки.")
        return

    lines = []
    ticket_counter = 1
    
    for row in data:
        # Формируем имя пользователя
        username = f"@{row['username']}" if row['username'] else f"ID:{row['user_id']}"
        
        # Добавляем строки: номер билета + пользователь
        for _ in range(row['tickets']):
            lines.append(f"{ticket_counter}. {username}")
            ticket_counter += 1
    
    file_content = "\n".join(lines).encode('utf-8')
    input_file = types.BufferedInputFile(file_content, filename="raffle_participants.txt")
    
    await callback.message.answer_document(
        input_file, 
        caption=f"📄 Список участников для розыгрыша\n🎫 Всего билетов: {ticket_counter - 1}"
    )


# Обратная совместимость с командой /export
@router.message(Command("export"), F.from_user.id.in_(ADMIN_IDS))
async def export_command(message: types.Message):
    """Альтернативный доступ к экспорту через команду."""
    await message.answer(
        "📁 Выберите формат экспорта:",
        reply_markup=get_admin_export_menu()
    )
