import hashlib
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (BufferedInputFile, CallbackQuery, InlineKeyboardMarkup, InputMediaAnimation,
                           InputMediaPhoto, LinkPreviewOptions, Message, TelegramObject)

from . import banner, db
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


NO_PREVIEW = LinkPreviewOptions(is_disabled=True)
log = logging.getLogger(__name__)


async def _banner_media() -> tuple[str, str | None]:
    """(тип, file_id) баннера: свой от админа (/setbanner) или нарисованный ботом."""
    kind = await db.get_setting("banner_type")
    file_id = await db.get_setting("banner_file_id")
    if kind and file_id:
        return kind, file_id
    tag = hashlib.md5(config.bot_name.encode()).hexdigest()[:8]
    return "auto", await db.get_setting(f"banner_auto:{tag}")


async def send_banner(bot: Bot, chat_id: int, caption: str, markup: InlineKeyboardMarkup | None) -> Message:
    kind, file_id = await _banner_media()
    if kind == "animation":
        return await bot.send_animation(chat_id, file_id, caption=caption, reply_markup=markup)
    if kind == "photo" or file_id:
        return await bot.send_photo(chat_id, file_id, caption=caption, reply_markup=markup)
    # Первый показ: рисуем баннер и запоминаем file_id, дальше Telegram отдаёт его из кэша.
    image = BufferedInputFile(banner.render(config.bot_name), "banner.jpg")
    msg = await bot.send_photo(chat_id, image, caption=caption, reply_markup=markup)
    if msg.photo:
        tag = hashlib.md5(config.bot_name.encode()).hexdigest()[:8]
        await db.set_setting(f"banner_auto:{tag}", msg.photo[-1].file_id)
    return msg


def _is_media(msg) -> bool:
    return isinstance(msg, Message) and bool(msg.photo or msg.animation)


async def show(call: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None = None,
               banner: bool = False) -> Message:
    """Показывает экран в том же сообщении.

    banner=True — экран с картинкой (главное меню), иначе — обычный текст. Если тип сообщения
    меняется (картинка ↔ текст), старое сообщение удаляется и отправляется новое.
    """
    msg = call.message
    can_edit = isinstance(msg, Message) and not msg.invoice
    try:
        if can_edit and banner and _is_media(msg):
            kind, file_id = await _banner_media()
            current = msg.animation.file_id if msg.animation else msg.photo[-1].file_id
            if file_id and file_id != current and kind in ("photo", "animation"):
                media_cls = InputMediaAnimation if kind == "animation" else InputMediaPhoto
                result = await msg.edit_media(media_cls(media=file_id, caption=text), reply_markup=markup)
            else:
                result = await msg.edit_caption(caption=text, reply_markup=markup)
            return result if isinstance(result, Message) else msg
        if can_edit and not banner and msg.text:
            result = await msg.edit_text(text, reply_markup=markup, link_preview_options=NO_PREVIEW)
            return result if isinstance(result, Message) else msg
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return msg
        log.debug("edit failed: %s", exc)
    if can_edit:
        try:
            await msg.delete()
        except TelegramBadRequest:
            pass
    if banner:
        return await send_banner(call.bot, call.from_user.id, text, markup)
    return await call.bot.send_message(call.from_user.id, text, reply_markup=markup, link_preview_options=NO_PREVIEW)


def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids
