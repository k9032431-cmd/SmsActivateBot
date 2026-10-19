from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, TelegramObject

from . import db
from .config import config
from .i18n import t


class UserMiddleware(BaseMiddleware):
    """Регистрирует пользователя, подставляет user/lang в хендлеры и не пускает забаненных."""

    async def __call__(self, handler: Callable[[TelegramObject, dict], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        tg_user = data.get("event_from_user")
        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)
        user = await db.upsert_user(tg_user.id, tg_user.username, tg_user.full_name)
        data["user"] = user
        data["lang"] = user["lang"]
        if user["banned"] and tg_user.id not in config.admin_ids:
            if isinstance(event, Message):
                await event.answer(t(user["lang"], "banned"))
            elif isinstance(event, CallbackQuery):
                await event.answer(t(user["lang"], "banned").split(" ", 1)[-1], show_alert=True)
            return None
        return await handler(event, data)


async def show(call: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None = None) -> Message:
    """Редактирует сообщение с кнопкой, а если нельзя (инвойс, старое сообщение) — шлёт новое."""
    msg = call.message
    try:
        if isinstance(msg, Message) and (msg.text or msg.html_text) and not msg.invoice:
            result = await msg.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
            return result if isinstance(result, Message) else msg
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return msg
    return await call.bot.send_message(call.from_user.id, text, reply_markup=markup,
                                       disable_web_page_preview=True)


def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids
