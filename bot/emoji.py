"""Премиум-эмодзи.

У каждого эмодзи есть имя и обычный (запасной) символ. ID премиум-эмодзи задаётся
админом командой /setemoji и хранится в БД. Пока ID не задан, показывается обычный эмодзи.
"""
from . import db

FALLBACK = {
    "logo": "🐻",
    "phone": "📱",
    "buy": "🛒",
    "wallet": "💰",
    "topup": "💳",
    "orders": "📦",
    "lang": "🌐",
    "support": "🆘",
    "channel": "📣",
    "back": "◀️",
    "next": "▶️",
    "home": "🏠",
    "search": "🔎",
    "fire": "🔥",
    "star": "⭐",
    "crypto": "💎",
    "card": "💳",
    "ok": "✅",
    "cancel": "❌",
    "wait": "⏳",
    "code": "🔑",
    "refresh": "🔄",
    "sms": "💬",
    "money": "💵",
    "warning": "⚠️",
    "globe": "🌍",
    "admin": "👑",
    "stats": "📊",
    "broadcast": "📢",
    "settings": "⚙️",
    "user": "👤",
    "id": "🆔",
    "gift": "🎁",
    "check": "☑️",
    "box": "📭",
    "done": "🏁",
}

_ids: dict[str, str] = {}


async def load() -> None:
    _ids.clear()
    _ids.update(await db.settings_with_prefix("emoji:"))


async def set_id(name: str, custom_id: str | None) -> None:
    if custom_id:
        await db.set_setting(f"emoji:{name}", custom_id)
        _ids[name] = custom_id
    else:
        await db.del_setting(f"emoji:{name}")
        _ids.pop(name, None)


def icon(name: str) -> str | None:
    """ID премиум-эмодзи для иконки на кнопке."""
    return _ids.get(name)


def plain(name: str) -> str:
    return FALLBACK.get(name, "")


def e(name: str) -> str:
    """Эмодзи для текста сообщения (parse_mode=HTML)."""
    char = FALLBACK.get(name, "▫️")
    custom_id = _ids.get(name)
    if custom_id:
        return f'<tg-emoji emoji-id="{custom_id}">{char}</tg-emoji>'
    return char
