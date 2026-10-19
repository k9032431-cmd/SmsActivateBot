"""Премиум-эмодзи.

У каждого эмодзи есть имя и обычный (запасной) символ. ID премиум-эмодзи задаёт админ:
по одному (/setemoji), списком или целым паком (/emojipack). ID хранятся в БД.
Пока ID не задан, показывается обычный эмодзи.
"""
from . import db

FALLBACK = {
    # бренд и оформление
    "logo": "🐻",
    "wave": "👋",
    "sparkle": "✨",
    "crown": "👑",
    "diamond": "💎",
    "rocket": "🚀",
    "lightning": "⚡",
    "shield": "🛡",
    "down": "👇",
    "info": "ℹ️",
    "bell": "🔔",
    # меню
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
    # покупка и заказ
    "service": "🧩",
    "globe": "🌍",
    "price": "🏷",
    "stock": "🔢",
    "money": "💵",
    "wait": "⏳",
    "clock": "🕐",
    "code": "🔑",
    "sms": "💬",
    "ok": "✅",
    "cancel": "❌",
    "done": "🏁",
    "refresh": "🔄",
    "warning": "⚠️",
    "check": "☑️",
    "box": "📭",
    # оплата
    "star": "⭐",
    "crypto": "💎",
    "card": "💳",
    "gift": "🎁",
    # профиль и админка
    "user": "👤",
    "id": "🆔",
    "admin": "👑",
    "stats": "📊",
    "chart": "📈",
    "broadcast": "📢",
    "settings": "⚙️",
    # логотипы сервисов на кнопках (svc_<код сервиса>)
    "svc_tg": "✈️",
    "svc_wa": "💚",
    "svc_ig": "📸",
    "svc_go": "🔍",
    "svc_fb": "👥",
    "svc_tw": "🐦",
    "svc_ds": "🎮",
    "svc_lf": "🎵",
    "svc_vk": "🔵",
    "svc_ok": "🟠",
    "svc_ya": "🟡",
    "svc_ma": "📧",
    "svc_mm": "🪟",
    "svc_am": "📦",
    "svc_oi": "❤️",
    "svc_wb": "💬",
    "svc_ts": "💲",
    "svc_nf": "🎬",
    "svc_mt": "🕹",
    "svc_av": "🏷",
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


def _norm(char: str) -> str:
    return char.replace("️", "")


def match_names(char: str) -> list[str]:
    """Имена, у которых обычный эмодзи совпадает с char (для автоподбора из пака)."""
    return [name for name, fallback in FALLBACK.items() if _norm(fallback) == _norm(char)]


def e(name: str) -> str:
    """Эмодзи для текста сообщения (parse_mode=HTML)."""
    char = FALLBACK.get(name, "▫️")
    custom_id = _ids.get(name)
    if custom_id:
        return f'<tg-emoji emoji-id="{custom_id}">{char}</tg-emoji>'
    return char
