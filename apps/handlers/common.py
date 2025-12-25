from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.utils.deep_linking import decode_payload
from aiogram.enums import ChatType
import logging

from config.config import MAIN_IMAGE, RULES_IMAGE, REQUIRED_CHANNEL, REQUIRED_CHAT
from data.database import db
from utils.keyboards.inline import get_main_menu, get_back_button
from utils.subscription import check_subscription, get_subscription_keyboard, get_subscription_text

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
async def cmd_start(message: types.Message):
    """Обработчик команды /start с поддержкой реферальных ссылок."""
    args = message.text.split()
    referrer_id = None
    
    logger.info(f"User {message.from_user.id} (@{message.from_user.username}) started bot with args: {args}")
    
    if len(args) > 1:
        raw_payload = args[1]
        logger.info(f"Raw referral payload: {raw_payload}")
        
        try:
            # Декодируем payload (может быть закодирован в base64)
            payload = decode_payload(raw_payload)
            referrer_id = int(payload)
            logger.info(f"Decoded referrer_id: {referrer_id}")
            
            # Нельзя быть рефералом самого себя
            if referrer_id == message.from_user.id:
                logger.info(f"Self-referral attempt rejected")
                referrer_id = None
        except (ValueError, Exception) as e:
            logger.warning(f"Failed to decode payload: {e}, trying as raw int")
            # Если не удалось декодировать, пробуем как обычное число
            try:
                referrer_id = int(raw_payload)
                logger.info(f"Parsed raw referrer_id: {referrer_id}")
                if referrer_id == message.from_user.id:
                    referrer_id = None
            except ValueError as ve:
                logger.warning(f"Failed to parse referrer: {ve}")

    # Проверяем, существует ли пользователь
    existing_user = await db.get_user(message.from_user.id)
    
    if existing_user:
        # Обновляем username если изменился
        await db.update_username(message.from_user.id, message.from_user.username)
        if referrer_id and not existing_user['referrer_id']:
            logger.info(f"Existing user {message.from_user.id} tried to use referral link, but referrer cannot be changed")
        logger.info(f"Existing user updated: {message.from_user.id}, current referrer: {existing_user['referrer_id']}")
    else:
        # Создаём нового пользователя с реферером
        await db.create_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            referrer_id=referrer_id
        )
        logger.info(f"New user created: {message.from_user.id} with referrer: {referrer_id}")
    
    # Проверяем подписку
    sub_status = await check_subscription(message.bot, message.from_user.id)
    
    if not sub_status["all_ok"]:
        # Показываем сообщение о необходимости подписки
        await message.answer(
            get_subscription_text(sub_status),
            parse_mode="HTML",
            reply_markup=get_subscription_keyboard(sub_status)
        )
        return
    
    # Показываем главное меню
    welcome_text = (
        "🎄 <b>С Наступающим Новым Годом!</b>\n\n"
        "Добро пожаловать в нашу праздничную акцию! 🎅\n"
        "Оставляйте пожелания, приглашайте друзей и выигрывайте призы.\n\n"
        "Чем больше у вас билетов, тем выше шанс на победу! 🎁"
    )
    
    if MAIN_IMAGE.exists():
        photo = FSInputFile(MAIN_IMAGE)
        await message.answer_photo(photo, caption=welcome_text, parse_mode="HTML", reply_markup=get_main_menu())
    else:
        await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu())


@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: types.CallbackQuery):
    """Проверка подписки по кнопке."""
    sub_status = await check_subscription(callback.bot, callback.from_user.id)
    
    if not sub_status["all_ok"]:
        await callback.answer("❌ Вы не подписаны на все каналы!", show_alert=True)
        
        # Обновляем сообщение с актуальными статусами
        try:
            await callback.message.edit_text(
                get_subscription_text(sub_status),
                parse_mode="HTML",
                reply_markup=get_subscription_keyboard(sub_status)
            )
        except Exception:
            pass
        return
    
    # Подписка подтверждена — показываем главное меню
    await callback.answer("✅ Подписка подтверждена!")
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    welcome_text = (
        "🎄 <b>С Наступающим Новым Годом!</b>\n\n"
        "Добро пожаловать в нашу праздничную акцию! 🎅\n"
        "Оставляйте пожелания, приглашайте друзей и выигрывайте призы.\n\n"
        "Чем больше у вас билетов, тем выше шанс на победу! 🎁"
    )
    
    if MAIN_IMAGE.exists():
        photo = FSInputFile(MAIN_IMAGE)
        await callback.message.answer_photo(photo, caption=welcome_text, parse_mode="HTML", reply_markup=get_main_menu())
    else:
        await callback.message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu())


@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery):
    """Возврат в главное меню."""
    welcome_text = (
        "🎄 <b>Главное меню</b>\n\n"
        "Выберите действие:"
    )
    
    # Удаляем старое сообщение и отправляем новое с фото
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    if MAIN_IMAGE.exists():
        photo = FSInputFile(MAIN_IMAGE)
        await callback.message.answer_photo(photo, caption=welcome_text, parse_mode="HTML", reply_markup=get_main_menu())
    else:
        await callback.message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu())


@router.callback_query(F.data == "rules")
async def show_rules(callback: types.CallbackQuery):
    """Показать правила акции."""
    from config.config import CHANNEL_INVITE_LINK, CHAT_INVITE_LINK
    
    # Формируем ссылку на канал
    if CHANNEL_INVITE_LINK:
        channel_link = f'<a href="{CHANNEL_INVITE_LINK}">канал</a>'
    elif REQUIRED_CHANNEL.startswith('@'):
        channel_link = f'<a href="https://t.me/{REQUIRED_CHANNEL.lstrip("@")}">{REQUIRED_CHANNEL}</a>'
    else:
        channel_link = "канал"
    
    # Формируем ссылку на чат
    if CHAT_INVITE_LINK:
        chat_link = f'<a href="{CHAT_INVITE_LINK}">чат</a>'
    elif REQUIRED_CHAT.startswith('@'):
        chat_link = f'<a href="https://t.me/{REQUIRED_CHAT.lstrip("@")}">{REQUIRED_CHAT}</a>'
    else:
        chat_link = "чат"
    
    rules_text = (
        "📜 <b>Правила акции:</b>\n\n"
        f"1. Подпишитесь на {channel_link} и {chat_link}\n"
        "2. Оставьте одно новогоднее пожелание и получите билет 🎫\n"
        "3. Приглашайте друзей по своей реферальной ссылке\n"
        "4. За каждого друга, который оставит пожелание, вы получите +1 билет 🎫\n"
        "5. Больше билетов - больше шансов в розыгрыше!\n\n"
        "Желаем удачи! ✨"
    )
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    if RULES_IMAGE.exists():
        photo = FSInputFile(RULES_IMAGE)
        await callback.message.answer_photo(
            photo, 
            caption=rules_text, 
            parse_mode="HTML",
            reply_markup=get_back_button()
        )
    else:
        await callback.message.answer(
            rules_text, 
            parse_mode="HTML",
            reply_markup=get_back_button()
        )
