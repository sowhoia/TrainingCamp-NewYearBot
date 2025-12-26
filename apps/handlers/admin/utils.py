"""Shared utilities for admin handlers."""
from aiogram.fsm.state import State, StatesGroup

from config.config import ADMIN_IDS


class AdminState(StatesGroup):
    """FSM states for admin operations."""
    waiting_for_post_link = State()
    waiting_for_username_to_reset = State()
    waiting_for_username_to_give_tickets = State()
    waiting_for_ticket_count = State()
    waiting_for_ticket_message = State()


def is_admin(user_id: int) -> bool:
    """Check if user is an administrator."""
    return user_id in ADMIN_IDS


def get_ticket_word(count: int) -> str:
    """Get correct Russian declension for 'билет'."""
    if 11 <= count % 100 <= 14:
        return "билетов"
    last_digit = count % 10
    if last_digit == 1:
        return "билет"
    elif 2 <= last_digit <= 4:
        return "билета"
    else:
        return "билетов"
