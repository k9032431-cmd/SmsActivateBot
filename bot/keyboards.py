from aiogram.enums import ButtonStyle
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .emoji import icon, plain

BLUE = ButtonStyle.PRIMARY
GREEN = ButtonStyle.SUCCESS
RED = ButtonStyle.DANGER


def btn(text: str, emoji: str | None = None, style: str | None = None, *,
        cb: str | None = None, url: str | None = None, pay: bool = False,
        copy: str | None = None) -> InlineKeyboardButton:
    """Кнопка с цветом и иконкой. Если для эмодзи задан премиум ID — он ставится иконкой кнопки."""
    custom_id = icon(emoji) if emoji else None
    if emoji and not custom_id:
        text = f"{plain(emoji)} {text}"
    extra = {}
    if copy:
        extra["copy_text"] = {"text": copy}
    return InlineKeyboardButton(
        text=text, style=style, icon_custom_emoji_id=custom_id,
        callback_data=cb, url=url, pay=pay or None, **extra,
    )


def kb(*rows: list[InlineKeyboardButton] | InlineKeyboardButton) -> InlineKeyboardMarkup:
    rows = [r if isinstance(r, list) else [r] for r in rows]
    return InlineKeyboardMarkup(inline_keyboard=[r for r in rows if r])


def grid(buttons: list[InlineKeyboardButton], width: int) -> list[list[InlineKeyboardButton]]:
    return [buttons[i:i + width] for i in range(0, len(buttons), width)]
