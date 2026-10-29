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
    "mail": "📧",
    "inbox": "📩",
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
    "copy": "📋",
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

# Где используется каждый эмодзи — подсказка для мастера /emojiwizard.
WHERE = {
    "logo": "логотип бота", "wave": "приветствие в главном меню", "sparkle": "украшение заголовков",
    "crown": "заголовок админ-панели", "diamond": "кнопка CryptoBot и список монет",
    "rocket": "призыв к покупке", "lightning": "«моментальная выдача»", "shield": "«возврат денег»",
    "down": "указатель «выберите ниже»", "info": "подсказки и номера страниц", "bell": "уведомления",
    "phone": "номер телефона, кнопка «Скопировать номер»",
    "mail": "кнопка «Временная почта»", "inbox": "новое письмо, кнопка «Входящие»", "buy": "кнопка «Купить номер» и заголовок покупки",
    "wallet": "баланс, кнопка «ЮMoney»", "topup": "кнопка «Пополнить»", "orders": "кнопка «Мои номера»",
    "lang": "кнопка «Язык»", "support": "кнопка «Поддержка»", "channel": "кнопка «Наш канал»",
    "back": "кнопка «Назад»", "next": "кнопка «Дальше» в списках", "home": "кнопка «Главное меню»",
    "search": "кнопка «Поиск»", "fire": "популярное", "service": "сервис и кнопка «Все сервисы»",
    "globe": "страна", "price": "цена", "stock": "сколько номеров в наличии", "money": "суммы и кнопки сумм",
    "wait": "ожидание СМС", "clock": "таймер и сроки", "code": "код из СМС, кнопка «Скопировать код»",
    "sms": "кнопка «Ещё СМС»", "ok": "галочки «готово», кнопка «Завершить»", "cancel": "кнопка «Отменить»",
    "done": "активация завершена", "refresh": "кнопка «Проверить оплату»", "copy": "кнопка «Скопировать адрес»",
    "warning": "предупреждения и ошибки", "check": "отметки", "box": "пустой список",
    "star": "кнопка «Telegram Stars»", "crypto": "кнопка «Крипта» (Cryptomus)", "card": "кнопки оплаты картой",
    "gift": "зачисление на баланс", "user": "кнопка «Профиль»", "id": "ID пользователя",
    "admin": "админ", "stats": "статистика", "chart": "прибыль", "broadcast": "кнопка «Рассылка»",
    "settings": "настройки",
}

# Похожие эмодзи — по ним /emojipack подбирает замену, если точного совпадения в паке нет.
SIMILAR = {
    "buy": "🛍🧺💸", "wallet": "👛💼🏦", "topup": "💸💰➕", "orders": "🗂📋🧾", "lang": "🌍🗣🔤",
    "support": "💬🎧🛟❓", "channel": "📢📰", "back": "⬅↩🔙", "next": "➡🔜", "home": "🏡",
    "search": "🔍", "service": "📲🧰", "globe": "🌎🌏🗺", "price": "💲💵", "stock": "📦📊",
    "money": "💰💸🪙", "wait": "⌛🕐", "clock": "⏰⏱🕒", "code": "🔐🔒", "sms": "✉📩💭",
    "ok": "✔☑👍", "cancel": "✖🚫⛔", "done": "🎉🏆", "refresh": "🔃♻", "copy": "📄📑",
    "warning": "❗‼🚨", "star": "🌟✨", "crypto": "🪙₿", "card": "💸🏧", "gift": "🎉",
    "user": "🙂👨🧑", "id": "🪪🔢", "sparkle": "🌟💫", "rocket": "🛸", "lightning": "🔥",
    "shield": "🔒✅", "down": "⬇🔽", "info": "💡❕", "bell": "🔔📣", "phone": "📲☎", "mail": "✉📨📬", "inbox": "📨📬✉",
    "stats": "📈", "chart": "📊💹", "broadcast": "📣", "settings": "🔧🛠", "fire": "💥",
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


def similar_names(char: str) -> list[str]:
    """Имена, для которых char — похожий эмодзи (второй проход автоподбора)."""
    c = _norm(char)
    return [name for name, chars in SIMILAR.items() if c and c in _norm(chars)]


def missing() -> list[str]:
    return [name for name in FALLBACK if name not in _ids]


def e(name: str) -> str:
    """Эмодзи для текста сообщения (parse_mode=HTML)."""
    char = FALLBACK.get(name, "▫️")
    custom_id = _ids.get(name)
    if custom_id:
        return f'<tg-emoji emoji-id="{custom_id}">{char}</tg-emoji>'
    return char
