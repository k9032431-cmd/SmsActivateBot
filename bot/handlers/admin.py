import asyncio
import logging
from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from .. import catalog, db, emoji
from ..common import show
from ..config import config
from ..grizzly import grizzly
from ..i18n import fmt_money
from ..keyboards import BLUE, GREEN, RED, btn, kb

router = Router()
router.message.filter(F.from_user.id.in_(config.admin_ids))
router.callback_query.filter(F.from_user.id.in_(config.admin_ids))
log = logging.getLogger(__name__)

HELP = (
    "<b>Команды админа</b>\n"
    "/admin — панель\n"
    "/user <code>ID</code> — инфо о пользователе\n"
    "/addbal <code>ID сумма</code> — начислить ₽ (минус — списать)\n"
    "/ban <code>ID</code>, /unban <code>ID</code>\n"
    "/setmarkup <code>2</code> — наценка (×2 = цена в 2 раза выше)\n"
    "/setusd <code>95</code> — курс USD→RUB (если баланс Grizzly в $)\n"
    "/setstar <code>1.8</code> — сколько ₽ стоит 1 ⭐\n"
    "\n<b>Премиум-эмодзи</b>\n"
    "/emojis — все эмодзи бота и их имена\n"
    "/emojipack <code>ссылка</code> — взять эмодзи из пака (t.me/addemoji/…), подбираются автоматически\n"
    "/setemoji <code>имя</code> <i>эмодзи</i> — поставить один; можно списком, по строке на каждый:\n"
    "<code>/setemoji buy</code> 🛒\n<code>wallet</code> 💰\n"
    "/delemoji <code>имя</code> — вернуть обычный эмодзи (<code>/delemoji all</code> — все)\n"
)


class Broadcast(StatesGroup):
    message = State()


async def panel_text() -> str:
    s = await db.stats()
    try:
        g_balance = await grizzly.get_balance()
        g_text = f"{g_balance:.2f} {'$' if config.grizzly_currency == 'USD' else '₽'}"
    except Exception as exc:
        g_text = f"ошибка: {escape(str(exc))}"
    e = emoji.e
    return (
        f"{e('crown')} <b>Админ-панель</b> {e('sparkle')}\n\n"
        f"<blockquote>{e('user')} Пользователи · <b>{s['users']}</b> <i>(+{s['users_day']} за 24ч)</i>\n"
        f"{e('phone')} Продано номеров · <b>{s['orders']}</b> <i>(+{s['orders_day']} за 24ч)</i></blockquote>\n\n"
        f"<blockquote>{e('money')} Выручка · <b>{fmt_money(s['revenue'])}</b>\n"
        f"{e('chart')} Прибыль · <b>{fmt_money(s['profit'])}</b> <i>(+{fmt_money(s['profit_day'])} за 24ч)</i>\n"
        f"{e('topup')} Пополнения · <b>{fmt_money(s['deposits'])}</b>\n"
        f"{e('wallet')} На балансах клиентов · <b>{fmt_money(s['balances'])}</b></blockquote>\n\n"
        f"<blockquote>{e('logo')} Баланс Grizzly · <b>{g_text}</b>\n"
        f"{e('settings')} Наценка · <b>×{await catalog.markup():g}</b>\n"
        f"{e('star')} 1 звезда · <b>{await catalog.star_rub():g} ₽</b>"
        + (f"\n{e('money')} $1 · <b>{await catalog.usd_rub():g} ₽</b>" if config.grizzly_currency == "USD" else "")
        + "</blockquote>"
    )


def panel_kb():
    return kb(
        [btn("Обновить", "refresh", BLUE, cb="adm:panel"), btn("Рассылка", "broadcast", GREEN, cb="adm:bc")],
        [btn("Команды", "settings", cb="adm:help"), btn("Эмодзи", "star", cb="adm:emojis")],
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(await panel_text(), reply_markup=panel_kb())


@router.callback_query(F.data == "adm:panel")
async def cb_panel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await show(call, await panel_text(), panel_kb())


@router.callback_query(F.data == "adm:help")
async def cb_help(call: CallbackQuery):
    await call.answer()
    await show(call, HELP, kb(btn("Назад", "back", cb="adm:panel")))


def emojis_texts() -> list[str]:
    """Список эмодзи, разбитый на сообщения (лимит Telegram — 4096 символов)."""
    chunks, current = [], ""
    for line in emojis_text().split("\n"):
        if len(current) + len(line) > 3500:
            chunks.append(current)
            current = ""
        current += line + "\n"
    return chunks + [current]


def emojis_text() -> str:
    done = sum(1 for name in emoji.FALLBACK if emoji.icon(name))
    lines = [f"{emoji.e('sparkle')} <b>Эмодзи бота</b> · премиум {done}/{len(emoji.FALLBACK)}\n"]
    for name in emoji.FALLBACK:
        mark = "⭐" if emoji.icon(name) else "▫️"
        lines.append(f"{mark} {emoji.e(name)} <code>{name}</code>")
    lines.append("\n⭐ — стоит премиум-эмодзи.\n"
                 "Быстро: <code>/emojipack ссылка_на_пак</code>\n"
                 "Вручную: <code>/setemoji buy</code> + премиум-эмодзи")
    return "\n".join(lines)


@router.message(Command("emojis"))
async def cmd_emojis(message: Message):
    for chunk in emojis_texts():
        await message.answer(chunk)


@router.callback_query(F.data == "adm:emojis")
async def cb_emojis(call: CallbackQuery):
    await call.answer()
    for chunk in emojis_texts():
        await call.message.answer(chunk)


def _line_emojis(message: Message) -> list[tuple[str, str]]:
    """[(имя, custom_emoji_id)] из сообщения вида «/setemoji имя 😀» с любым числом строк.
    Можно вместо эмодзи указать числовой ID."""
    text = message.text or ""
    raw = text.encode("utf-16-le")
    by_line: dict[int, str] = {}
    for ent in message.entities or []:
        if ent.type == "custom_emoji":
            line_no = raw[:ent.offset * 2].decode("utf-16-le").count("\n")
            by_line.setdefault(line_no, ent.custom_emoji_id)
    pairs = []
    for line_no, line in enumerate(text.split("\n")):
        words = line.split()
        if words and words[0].startswith("/"):
            words = words[1:]
        if not words:
            continue
        custom_id = by_line.get(line_no) or (words[1] if len(words) > 1 and words[1].isdigit() else None)
        if custom_id:
            pairs.append((words[0], custom_id))
    return pairs


@router.message(Command("setemoji"))
async def cmd_setemoji(message: Message):
    pairs = _line_emojis(message)
    if not pairs:
        return await message.answer(
            "Отправьте имя из /emojis и премиум-эмодзи, например:\n<code>/setemoji buy</code> 🛒\n"
            "Можно сразу несколько — по одному на строку. Для премиум-эмодзи нужен Telegram Premium.")
    done, unknown = [], []
    for name, custom_id in pairs:
        if name in emoji.FALLBACK:
            await emoji.set_id(name, custom_id)
            done.append(f"{emoji.e(name)} <code>{name}</code>")
        else:
            unknown.append(escape(name))
    text = "✅ Установлено:\n" + "\n".join(done) if done else "Ничего не установлено."
    if unknown:
        text += "\n\n⚠️ Неизвестные имена: " + ", ".join(unknown) + " (список: /emojis)"
    await message.answer(text)


@router.message(Command("emojipack"))
async def cmd_emojipack(message: Message, command: CommandObject, bot: Bot):
    """Берёт эмодзи из пака и ставит их тем местам бота, где обычный эмодзи совпадает."""
    name = (command.args or "").strip().rstrip("/").split("/")[-1]
    if not name:
        return await message.answer("Пример: <code>/emojipack https://t.me/addemoji/НазваниеПака</code>")
    try:
        sticker_set = await bot.get_sticker_set(name)
    except Exception as exc:
        return await message.answer(f"Не удалось открыть пак: {escape(str(exc))}")
    assigned: dict[str, str] = {}
    for sticker in sticker_set.stickers:
        if not sticker.custom_emoji_id or not sticker.emoji:
            continue
        for target in emoji.match_names(sticker.emoji):
            if target not in assigned:
                assigned[target] = sticker.custom_emoji_id
    for target, custom_id in assigned.items():
        await emoji.set_id(target, custom_id)
    if not assigned:
        return await message.answer("В этом паке не нашлось подходящих эмодзи. Попробуйте другой пак "
                                    "или поставьте вручную через /setemoji.")
    shown = " ".join(emoji.e(n) for n in assigned)
    await message.answer(f"✅ Из пака <b>{escape(sticker_set.title)}</b> поставлено {len(assigned)} эмодзи:\n"
                         f"{shown}\n\nОстальные можно поставить вручную — смотрите /emojis")


@router.message(Command("delemoji"))
async def cmd_delemoji(message: Message, command: CommandObject):
    name = (command.args or "").strip()
    if name == "all":
        for n in emoji.FALLBACK:
            await emoji.set_id(n, None)
        return await message.answer("✅ Все эмодзи сброшены на обычные")
    if name not in emoji.FALLBACK:
        return await message.answer("Укажите имя из /emojis")
    await emoji.set_id(name, None)
    await message.answer(f"✅ <code>{name}</code> → {emoji.e(name)}")


async def _set_number(message: Message, command: CommandObject, key: str, title: str):
    try:
        value = float((command.args or "").replace(",", "."))
        assert value > 0
    except (ValueError, AssertionError):
        return await message.answer(f"Укажите число, например: <code>/{command.command} 2</code>")
    await db.set_setting(key, str(value))
    await message.answer(f"✅ {title}: <b>{value:g}</b>")


@router.message(Command("setmarkup"))
async def cmd_markup(message: Message, command: CommandObject):
    await _set_number(message, command, "markup", "Наценка ×")


@router.message(Command("setusd"))
async def cmd_usd(message: Message, command: CommandObject):
    await _set_number(message, command, "usd_rub", "Курс $1 =")


@router.message(Command("setstar"))
async def cmd_star(message: Message, command: CommandObject):
    await _set_number(message, command, "star_rub", "1 ⭐ =")


def _parse_id(command: CommandObject) -> int | None:
    try:
        return int((command.args or "").split()[0])
    except (ValueError, IndexError):
        return None


@router.message(Command("user"))
async def cmd_user(message: Message, command: CommandObject):
    user = await db.get_user(_parse_id(command) or 0)
    if not user:
        return await message.answer("Пользователь не найден")
    orders = await db.user_orders(user["id"], 5)
    await message.answer(
        f"{emoji.e('user')} <b>{escape(user['full_name'] or '—')}</b> "
        f"{'@' + user['username'] if user['username'] else ''}\n"
        f"ID: <code>{user['id']}</code> · язык: {user['lang']}\n"
        f"Баланс: <b>{fmt_money(user['balance'])}</b>\n"
        f"Статус: {'🚫 забанен' if user['banned'] else '✅ активен'}\n"
        f"Последние заказы: " + (", ".join(f"{o['service']} {fmt_money(o['price'])} ({o['status']})"
                                          for o in orders) or "нет"),
        reply_markup=kb([
            btn("Разбанить", "ok", GREEN, cb=f"adm:unban:{user['id']}") if user["banned"]
            else btn("Забанить", "cancel", RED, cb=f"adm:ban:{user['id']}"),
        ]),
    )


@router.callback_query(F.data.startswith("adm:ban:") | F.data.startswith("adm:unban:"))
async def cb_ban(call: CallbackQuery):
    _, action, user_id = call.data.split(":")
    await db.set_banned(int(user_id), action == "ban")
    await call.answer("Готово", show_alert=True)


@router.message(Command("ban", "unban"))
async def cmd_ban(message: Message, command: CommandObject):
    user_id = _parse_id(command)
    if not user_id or not await db.set_banned(user_id, command.command == "ban"):
        return await message.answer("Пользователь не найден")
    await message.answer("✅ Готово")


@router.message(Command("addbal"))
async def cmd_addbal(message: Message, command: CommandObject, bot: Bot):
    try:
        user_id, amount = (command.args or "").split()
        user_id, kop = int(user_id), round(float(amount.replace(",", ".")) * 100)
    except ValueError:
        return await message.answer("Пример: <code>/addbal 123456789 500</code>")
    if not await db.add_balance(user_id, kop):
        return await message.answer("Пользователь не найден")
    user = await db.get_user(user_id)
    await message.answer(f"✅ Баланс <code>{user_id}</code>: <b>{fmt_money(user['balance'])}</b>")


@router.callback_query(F.data == "adm:bc")
async def cb_broadcast(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(Broadcast.message)
    await show(call, f"{emoji.e('broadcast')} Отправьте сообщение для рассылки (текст, фото, видео — что угодно). "
                     "Оно будет скопировано всем пользователям.",
               kb(btn("Отмена", "cancel", RED, cb="adm:panel")))


@router.message(Broadcast.message)
async def do_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user_ids = await db.all_user_ids()
    status = await message.answer(f"⏳ Рассылка на {len(user_ids)} пользователей…")
    sent = 0
    for user_id in user_ids:
        try:
            await bot.copy_message(user_id, message.chat.id, message.message_id)
            sent += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)
    await status.edit_text(f"✅ Рассылка завершена: {sent}/{len(user_ids)}")
