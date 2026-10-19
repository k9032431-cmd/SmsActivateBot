from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, LinkPreviewOptions, Message, TelegramObject

from . import db
from .config import config
from .i18n import plain_t, t


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
                await event.answer(plain_t(user["lang"], "banned_short"), show_alert=True)
            return None
        return await handler(event, data)


def preview(banner: bool = False) -> LinkPreviewOptions:
    """Баннер показывается как большое превью ссылки над текстом; иначе превью выключено."""
    if banner and config.banner_url:
        return LinkPreviewOptions(url=config.banner_url, prefer_large_media=True, show_above_text=True)
    return LinkPreviewOptions(is_disabled=True)


async def show(call: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None = None,
               banner: bool = False) -> Message:
    """Редактирует сообщение с кнопкой, а если нельзя (инвойс, старое сообщение) — шлёт новое."""
    msg = call.message
    try:
        if isinstance(msg, Message) and (msg.text or msg.html_text) and not msg.invoice:
            result = await msg.edit_text(text, reply_markup=markup, link_preview_options=preview(banner))
            return result if isinstance(result, Message) else msg
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return msg
    return await call.bot.send_message(call.from_user.id, text, reply_markup=markup,
                                       link_preview_options=preview(banner))


def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids
