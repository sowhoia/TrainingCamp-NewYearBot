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


def get_admin_menu(bot_enabled: bool = True) -> InlineKeyboardMarkup:
    """Главное меню админ-панели с красивой компоновкой."""
    toggle_text = "🟢 Бот ВКЛ" if bot_enabled else "🔴 Бот ВЫКЛ"
    toggle_data = "admin_toggle_bot"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        # Тумблер бота - на всю ширину
        [InlineKeyboardButton(text=toggle_text, callback_data=toggle_data)],
        # Экспорт и пост - в 2 колонки
        [
            InlineKeyboardButton(text="📁 Экспорт", callback_data="admin_export"),
            InlineKeyboardButton(text="📨 Установить пост", callback_data="admin_set_post")
        ],
        # Управление пожеланиями и очистка поста - в 2 колонки
        [
            InlineKeyboardButton(text="🗑 Удалить пожелание", callback_data="admin_reset_wish"),
            InlineKeyboardButton(text="❌ Убрать пост", callback_data="admin_clear_post")
        ]
    ])


def get_admin_export_menu() -> InlineKeyboardMarkup:
    """Меню экспорта данных для админа."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 CSV", callback_data="export_csv"),
            InlineKeyboardButton(text="📄 TXT", callback_data="export_txt")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ])


def get_admin_cancel_button() -> InlineKeyboardMarkup:
    """Кнопка отмены для админ-панели."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="admin_cancel_input")]
    ])

