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
    "/setlowbalance <code>1</code> — предупреждать, когда баланс Grizzly ниже $1\n"
    "\n<b>Баннер главного меню</b>\n"
    "/setbanner — отправьте фото или GIF с подписью /setbanner (или ответьте этой командой на фото)\n"
    "/delbanner — вернуть баннер, который рисует бот\n"
    "\n<b>Премиум-эмодзи</b>\n"
    "/emojis — все эмодзи бота и их имена\n"
    "/emojiwizard — мастер: бот по очереди спрашивает премиум-эмодзи для каждого места\n"
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
        f"{e('crown')} <b>АДМИН-ПАНЕЛЬ</b>\n\n"
        f"{e('user')} Пользователи: <b>{s['users']}</b> <i>(+{s['users_day']} за 24ч)</i>\n"
        f"{e('phone')} Продано номеров: <b>{s['orders']}</b> <i>(+{s['orders_day']} за 24ч)</i>\n\n"
        f"{e('money')} Выручка: <b>{fmt_money(s['revenue'])}</b>\n"
        f"{e('chart')} Прибыль: <b>{fmt_money(s['profit'])}</b> <i>(+{fmt_money(s['profit_day'])} за 24ч)</i>\n"
        f"{e('topup')} Пополнения: <b>{fmt_money(s['deposits'])}</b>\n"
        f"{e('wallet')} На балансах клиентов: <b>{fmt_money(s['balances'])}</b>\n\n"
        f"{e('logo')} Баланс Grizzly: <b>{g_text}</b>\n"
        f"{e('bell')} Предупреждение при балансе ниже: <b>${await catalog.low_balance_usd():g}</b>\n"
        f"{e('settings')} Наценка: <b>×{await catalog.markup():g}</b>\n"
        f"{e('star')} 1 звезда: <b>{await catalog.star_rub():g} ₽</b>"
        + (f"\n{e('money')} $1: <b>{await catalog.usd_rub():g} ₽</b>" if config.grizzly_currency == "USD" else "")
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
                 "По шагам: /emojiwizard\n"
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
    text = f"{emoji.e('ok')} Установлено:\n" + "\n".join(done) if done else "Ничего не установлено."
    if unknown:
        text += f"\n\n{emoji.e('warning')} Неизвестные имена: " + ", ".join(unknown) + " (список: /emojis)"
    await message.answer(text)


@router.message(Command("emojipack"))
async def cmd_emojipack(message: Message, command: CommandObject, bot: Bot):
    """Берёт эмодзи из одного или нескольких паков: сначала точные совпадения, потом похожие.
    Уже поставленные эмодзи не трогает (кроме «/emojipack all ссылка»)."""
    args = (command.args or "").split()
    overwrite = bool(args) and args[0] == "all"
    links = args[1:] if overwrite else args
    if not links:
        return await message.answer(
            "Пример: <code>/emojipack https://t.me/addemoji/НазваниеПака</code>\n"
            "Можно сразу несколько ссылок через пробел. Чтобы заменить уже поставленные — "
            "<code>/emojipack all ссылка</code>")
    targets = list(emoji.FALLBACK) if overwrite else emoji.missing()
    assigned: dict[str, str] = {}
    report = []
    for link in links:
        name = link.strip().rstrip("/").split("/")[-1]
        try:
            sticker_set = await bot.get_sticker_set(name)
        except Exception as exc:
            report.append(f"{emoji.e('warning')} {escape(name)}: {escape(str(exc))}")
            continue
        stickers = [st for st in sticker_set.stickers if st.custom_emoji_id and st.emoji]
        used = set(assigned.values())
        before = len(assigned)
        for matcher in (emoji.match_names, emoji.similar_names):
            for st in stickers:
                if st.custom_emoji_id in used:
                    continue
                for target in matcher(st.emoji):
                    if target in targets and target not in assigned:
                        assigned[target] = st.custom_emoji_id
                        used.add(st.custom_emoji_id)
                        break
        report.append(f"{emoji.e('ok')} {escape(sticker_set.title)}: +{len(assigned) - before}")
    for target, custom_id in assigned.items():
        await emoji.set_id(target, custom_id)
    left = len(emoji.missing())
    text = "\n".join(report)
    if assigned:
        text += "\n\n" + " ".join(emoji.e(n) for n in assigned)
    text += (f"\n\nОсталось без премиум-эмодзи: <b>{left}</b>. "
             "Добавьте ещё пак или заполните остальные: /emojiwizard" if left else
             "\n\nВсе эмодзи бота теперь премиум!")
    await message.answer(text)


class EmojiWizard(StatesGroup):
    waiting = State()


def _wizard_prompt(queue: list[str], total: int) -> tuple[str, object]:
    name = queue[0]
    done = total - len(queue)
    text = (f"{emoji.e('sparkle')} <b>Премиум-эмодзи · {done + 1}/{total}</b>\n\n"
            f"Где: <b>{emoji.WHERE.get(name, name)}</b>\n"
            f"Сейчас: {emoji.e(name)}  <code>{name}</code>\n\n"
            "Отправьте премиум-эмодзи для этого места.\n"
            "Можно отправить сразу несколько — они встанут по порядку в следующие места.")
    return text, kb([btn("Пропустить", "next", BLUE, cb="ew:skip"), btn("Готово", "ok", GREEN, cb="ew:stop")])


@router.message(Command("emojiwizard"))
async def cmd_emojiwizard(message: Message, command: CommandObject, state: FSMContext):
    queue = list(emoji.FALLBACK) if (command.args or "").strip() == "all" else emoji.missing()
    # Сначала кнопки главного меню и оплаты — их видят чаще всего.
    first = ["buy", "user", "topup", "orders", "support", "back", "home", "card", "wallet", "crypto",
             "diamond", "star", "wave", "ok"]
    queue.sort(key=lambda n: first.index(n) if n in first else len(first))
    if not queue:
        return await message.answer(f"{emoji.e('ok')} Все эмодзи уже премиум. Заменить заново: "
                                    "<code>/emojiwizard all</code>")
    await state.set_state(EmojiWizard.waiting)
    await state.update_data(queue=queue, total=len(queue))
    text, markup = _wizard_prompt(queue, len(queue))
    await message.answer(text, reply_markup=markup)


@router.message(EmojiWizard.waiting, ~F.text.startswith("/"))
async def wizard_input(message: Message, state: FSMContext):
    data = await state.get_data()
    queue, total = data["queue"], data["total"]
    ids = [ent.custom_emoji_id for ent in (message.entities or []) if ent.type == "custom_emoji"]
    if not ids:
        return await message.answer("Это обычный эмодзи. Нужен премиум-эмодзи из панели эмодзи "
                                    "(требуется Telegram Premium).")
    shown = []
    while ids and queue:
        name = queue.pop(0)
        await emoji.set_id(name, ids.pop(0))
        shown.append(f"{emoji.e(name)} {emoji.WHERE.get(name, name)}")
    await message.answer(f"{emoji.e('ok')} " + "\n".join(shown))
    if not queue:
        await state.clear()
        return await message.answer(f"{emoji.e('sparkle')} Готово! Откройте /start и посмотрите.")
    await state.update_data(queue=queue)
    text, markup = _wizard_prompt(queue, total)
    await message.answer(text, reply_markup=markup)


@router.callback_query(EmojiWizard.waiting, F.data.startswith("ew:"))
async def wizard_button(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    queue = data["queue"]
    if call.data == "ew:skip" and len(queue) > 1:
        queue = queue[1:]
        await state.update_data(queue=queue)
        text, markup = _wizard_prompt(queue, data["total"])
        return await show(call, text, markup)
    await state.clear()
    await show(call, f"{emoji.e('ok')} Мастер закрыт. Без премиум-эмодзи осталось: {len(emoji.missing())}. "
                     "Продолжить: /emojiwizard")


@router.message(Command("setbanner"))
async def cmd_setbanner(message: Message):
    source = message if (message.photo or message.animation) else message.reply_to_message
    if not source or not (source.photo or source.animation):
        return await message.answer("Отправьте фото или GIF с подписью <code>/setbanner</code> "
                                    "или ответьте этой командой на сообщение с картинкой.")
    if source.animation:
        kind, file_id = "animation", source.animation.file_id
    else:
        kind, file_id = "photo", source.photo[-1].file_id
    await db.set_setting("banner_type", kind)
    await db.set_setting("banner_file_id", file_id)
    await message.answer(f"{emoji.e('ok')} Баннер обновлён — откройте /start")


@router.message(Command("delbanner"))
async def cmd_delbanner(message: Message):
    await db.del_setting("banner_type")
    await db.del_setting("banner_file_id")
    await message.answer(f"{emoji.e('ok')} Вернул баннер, который рисует бот — откройте /start")


@router.message(Command("delemoji"))
async def cmd_delemoji(message: Message, command: CommandObject):
    name = (command.args or "").strip()
    if name == "all":
        for n in emoji.FALLBACK:
            await emoji.set_id(n, None)
        return await message.answer(f"{emoji.e('ok')} Все эмодзи сброшены на обычные")
    if name not in emoji.FALLBACK:
        return await message.answer("Укажите имя из /emojis")
    await emoji.set_id(name, None)
    await message.answer(f"{emoji.e('ok')} <code>{name}</code> → {emoji.e(name)}")


async def _set_number(message: Message, command: CommandObject, key: str, title: str):
    try:
        value = float((command.args or "").replace(",", "."))
        assert value > 0
    except (ValueError, AssertionError):
        return await message.answer(f"Укажите число, например: <code>/{command.command} 2</code>")
    await db.set_setting(key, str(value))
    await message.answer(f"{emoji.e('ok')} {title}: <b>{value:g}</b>")


@router.message(Command("setmarkup"))
async def cmd_markup(message: Message, command: CommandObject):
    await _set_number(message, command, "markup", "Наценка ×")


@router.message(Command("setusd"))
async def cmd_usd(message: Message, command: CommandObject):
    await _set_number(message, command, "usd_rub", "Курс $1 =")


@router.message(Command("setlowbalance"))
async def cmd_lowbalance(message: Message, command: CommandObject):
    await _set_number(message, command, "low_balance_usd", "Предупреждать при балансе Grizzly ниже $")


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
        f"Статус: {emoji.e('cancel') + ' забанен' if user['banned'] else emoji.e('ok') + ' активен'}\n"
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
    await message.answer(f"{emoji.e('ok')} Готово")


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
    await message.answer(f"{emoji.e('ok')} Баланс <code>{user_id}</code>: <b>{fmt_money(user['balance'])}</b>")


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
    status = await message.answer(f"{emoji.e('wait')} Рассылка на {len(user_ids)} пользователей…")
    sent = 0
    for user_id in user_ids:
        try:
            await bot.copy_message(user_id, message.chat.id, message.message_id)
            sent += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)
    await status.edit_text(f"{emoji.e('ok')} Рассылка завершена: {sent}/{len(user_ids)}")
