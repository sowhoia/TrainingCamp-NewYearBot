from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню бота."""
    buttons = [
        [InlineKeyboardButton(text="🎫 Мои билеты", callback_data="my_tickets")],
        [
            InlineKeyboardButton(text="✨ Оставить пожелание", callback_data="leave_wish"),
            InlineKeyboardButton(text="📜 Правила", callback_data="rules")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_button() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])


def get_admin_menu() -> InlineKeyboardMarkup:
    """Главное меню админ-панели."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📁 Экспорт данных", callback_data="admin_export")],
        [InlineKeyboardButton(text="📨 Установить пост", callback_data="admin_set_post")],
        [InlineKeyboardButton(text="🗑 Убрать привязку к посту", callback_data="admin_clear_post")]
    ])


def get_admin_export_menu() -> InlineKeyboardMarkup:
    """Меню экспорта данных для админа."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Экспорт CSV", callback_data="export_csv")],
        [InlineKeyboardButton(text="📄 Экспорт TXT", callback_data="export_txt")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ])


def get_admin_cancel_button() -> InlineKeyboardMarkup:
    """Кнопка отмены для админ-панели."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="admin_cancel_input")]
    ])
