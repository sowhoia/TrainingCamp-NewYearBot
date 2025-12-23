from aiogram import Router, types, F
from aiogram.types import FSInputFile
from aiogram.utils.deep_linking import create_start_link

from config.config import TICKETS_IMAGE
from data.database import db
from utils.keyboards.inline import get_back_button

router = Router()


@router.callback_query(F.data == "my_tickets")
async def show_tickets(callback: types.CallbackQuery):
    """Показать билеты и реферальную ссылку."""
    user = await db.get_user(callback.from_user.id)
    
    if not user:
        await callback.answer("Ошибка: пользователь не найден.", show_alert=True)
        return

    ref_count = await db.get_referral_count(callback.from_user.id)
    link = await create_start_link(callback.bot, str(callback.from_user.id), encode=True)
    
    text = (
        f"🎫 <b>Ваши билеты:</b> {user['tickets']}\n"
        f"👥 <b>Приглашено друзей:</b> {ref_count}\n\n"
        f"🔗 <b>Ваша реферальная ссылка:</b>\n<code>{link}</code>\n\n"
        "Отправьте её друзьям! За каждого приглашённого друга, "
        "который оставит пожелание, вы получите +1 билет 🎁"
    )
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    if TICKETS_IMAGE.exists():
        photo = FSInputFile(TICKETS_IMAGE)
        await callback.message.answer_photo(
            photo,
            caption=text,
            parse_mode="HTML",
            reply_markup=get_back_button()
        )
    else:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_back_button())
