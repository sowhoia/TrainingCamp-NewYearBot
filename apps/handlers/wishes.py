from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile

from config.config import CONGRAT_IMAGE
from data.database import db
from utils.keyboards.inline import get_back_button
from utils.subscription import check_subscription, get_subscription_keyboard, get_subscription_text

router = Router()


class WishState(StatesGroup):
    waiting_for_wish = State()


@router.callback_query(F.data == "leave_wish")
async def start_wish(callback: types.CallbackQuery, state: FSMContext):
    """Начало процесса оставления пожелания."""
    
    # Проверяем подписку перед оставлением пожелания
    sub_status = await check_subscription(callback.bot, callback.from_user.id)
    
    if not sub_status["all_ok"]:
        await callback.answer("❌ Сначала подпишитесь на каналы!", show_alert=True)
        
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        await callback.message.answer(
            get_subscription_text(sub_status),
            parse_mode="HTML",
            reply_markup=get_subscription_keyboard(sub_status)
        )
        return
    
    user = await db.get_user(callback.from_user.id)
    
    if user and user['has_wished']:
        wish = await db.get_user_wish(callback.from_user.id)
        text = (
            f"✨ <b>Ваше пожелание:</b>\n<i>{wish['text']}</i>\n\n"
            "Вы уже оставили пожелание и получили билет! 🎫"
        )
        
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_back_button())
        return

    text = (
        "📝 <b>Введите ваше новогоднее пожелание:</b>\n\n"
        "Оно будет сохранено, и вы получите 1 билет на розыгрыш! 🎫"
    )
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.answer(text, parse_mode="HTML", reply_markup=get_back_button())
    await state.set_state(WishState.waiting_for_wish)


@router.message(WishState.waiting_for_wish)
async def process_wish(message: types.Message, state: FSMContext):
    """Обработка полученного пожелания."""
    if not message.text:
        await message.answer("❌ Пожалуйста, пришлите текстовое пожелание.")
        return

    success = await db.add_wish(message.from_user.id, message.text)
    
    if success:
        congrat_text = (
            "🎄 <b>Твоё пожелание сохранено!</b>\n\n"
            "Ты получил +1 билет 🎫\n"
            "Приглашай друзей, чтобы увеличить свои шансы!"
        )
        
        if CONGRAT_IMAGE.exists():
            photo = FSInputFile(CONGRAT_IMAGE)
            await message.answer_photo(
                photo,
                caption=congrat_text,
                parse_mode="HTML",
                reply_markup=get_back_button()
            )
        else:
            await message.answer(congrat_text, parse_mode="HTML", reply_markup=get_back_button())
    else:
        await message.answer(
            "❌ Произошла ошибка или вы уже оставляли пожелание.",
            reply_markup=get_back_button()
        )
    
    await state.clear()
