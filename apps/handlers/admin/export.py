"""Export handlers - CSV and TXT data export."""
import csv
import io

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums import ChatType

from config.config import ADMIN_IDS
from data.database import db
from utils.keyboards.inline import get_admin_export_menu

router = Router()


@router.callback_query(F.data == "admin_export", F.from_user.id.in_(ADMIN_IDS))
async def admin_export(callback: types.CallbackQuery):
    """Show export format selection."""
    await callback.message.edit_text(
        "📁 <b>Выберите формат экспорта:</b>",
        parse_mode="HTML",
        reply_markup=get_admin_export_menu()
    )


@router.callback_query(F.data == "export_csv", F.from_user.id.in_(ADMIN_IDS))
async def export_csv(callback: types.CallbackQuery):
    """Export data as CSV."""
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
    
    file_content = output.getvalue().encode('utf-8-sig')  # BOM for Excel
    input_file = types.BufferedInputFile(file_content, filename="raffle_participants.csv")
    
    await callback.message.answer_document(
        input_file, 
        caption=f"📊 Список участников для розыгрыша\n🎫 Всего билетов: {ticket_counter - 1}"
    )


@router.callback_query(F.data == "export_txt", F.from_user.id.in_(ADMIN_IDS))
async def export_txt(callback: types.CallbackQuery):
    """Export data as TXT - simple format for randomizer."""
    await callback.answer("Генерирую TXT...")
    
    data = await db.get_all_participants_data()
    
    if not data:
        await callback.message.answer("❌ Нет участников для выгрузки.")
        return

    lines = []
    ticket_counter = 1
    
    for row in data:
        username = f"@{row['username']}" if row['username'] else f"ID:{row['user_id']}"
        
        for _ in range(row['tickets']):
            lines.append(f"{ticket_counter}. {username}")
            ticket_counter += 1
    
    file_content = "\n".join(lines).encode('utf-8')
    input_file = types.BufferedInputFile(file_content, filename="raffle_participants.txt")
    
    await callback.message.answer_document(
        input_file, 
        caption=f"📄 Список участников для розыгрыша\n🎫 Всего билетов: {ticket_counter - 1}"
    )


@router.message(Command("export"), F.from_user.id.in_(ADMIN_IDS), F.chat.type == ChatType.PRIVATE)
async def export_command(message: types.Message):
    """Alternative export access via command."""
    await message.answer(
        "📁 Выберите формат экспорта:",
        reply_markup=get_admin_export_menu()
    )
