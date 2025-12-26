"""Error handling middleware for catching unhandled exceptions."""
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware to catch and log unhandled exceptions.
    
    This middleware wraps all handlers and catches any exceptions
    that aren't handled, logging them for debugging.
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            # Get user info for logging if available
            user_id = None
            chat_id = None
            
            if isinstance(event, Update):
                if event.message:
                    user_id = event.message.from_user.id if event.message.from_user else None
                    chat_id = event.message.chat.id
                elif event.callback_query:
                    user_id = event.callback_query.from_user.id
                    chat_id = event.callback_query.message.chat.id if event.callback_query.message else None
            
            logger.error(
                f"Unhandled exception in handler: {e}",
                exc_info=True,
                extra={
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "event_type": type(event).__name__
                }
            )
            
            # Re-raise to let aiogram's default error handling work
            raise
