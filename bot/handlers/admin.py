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
    "/emojis — список эмодзи бота\n"
    "/setemoji <code>имя</code> <i>премиум-эмодзи</i> — поставить премиум-эмодзи\n"
    "/delemoji <code>имя</code> — вернуть обычный эмодзи\n"
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
    return (
        f"{emoji.e('admin')} <b>Админ-панель</b>\n━━━━━━━━━━━━━━━\n"
        f"{emoji.e('user')} Пользователей: <b>{s['users']}</b> (+{s['users_day']} за 24ч)\n"
        f"{emoji.e('phone')} Продано номеров: <b>{s['orders']}</b> (+{s['orders_day']} за 24ч)\n"
        f"{emoji.e('money')} Выручка: <b>{fmt_money(s['revenue'])}</b>\n"
        f"{emoji.e('fire')} Прибыль: <b>{fmt_money(s['profit'])}</b> (+{fmt_money(s['profit_day'])} за 24ч)\n"
        f"{emoji.e('topup')} Пополнений: <b>{fmt_money(s['deposits'])}</b>\n"
        f"{emoji.e('wallet')} На балансах клиентов: <b>{fmt_money(s['balances'])}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{emoji.e('logo')} Баланс Grizzly: <b>{g_text}</b>\n"
        f"{emoji.e('settings')} Наценка: <b>×{await catalog.markup():g}</b> · "
        f"1⭐ = {await catalog.star_rub():g} ₽"
        + (f" · $1 = {await catalog.usd_rub():g} ₽" if config.grizzly_currency == "USD" else "")
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


def emojis_text() -> str:
    lines = ["<b>Эмодзи бота</b> (имя → как выглядит сейчас)\n"]
    for name in emoji.FALLBACK:
        mark = "⭐" if emoji.icon(name) else "▫️"
        lines.append(f"{mark} <code>{name}</code> → {emoji.e(name)}")
    lines.append("\n⭐ — стоит премиум-эмодзи. Поставить: <code>/setemoji имя</code> + премиум-эмодзи "
                 "в том же сообщении. Пример: <code>/setemoji buy</code> 🛒")
    return "\n".join(lines)


@router.message(Command("emojis"))
async def cmd_emojis(message: Message):
    await message.answer(emojis_text())


@router.callback_query(F.data == "adm:emojis")
async def cb_emojis(call: CallbackQuery):
    await call.answer()
    await show(call, emojis_text(), kb(btn("Назад", "back", cb="adm:panel")))


@router.message(Command("setemoji"))
async def cmd_setemoji(message: Message, command: CommandObject):
    args = (command.args or "").split()
    if not args or args[0] not in emoji.FALLBACK:
        return await message.answer("Укажите имя из /emojis и премиум-эмодзи: <code>/setemoji buy</code> 🛒")
    custom = [ent.custom_emoji_id for ent in (message.entities or []) if ent.type == "custom_emoji"]
    custom_id = custom[0] if custom else (args[1] if len(args) > 1 and args[1].isdigit() else None)
    if not custom_id:
        return await message.answer("В сообщении нет премиум-эмодзи. Нужен Telegram Premium, "
                                    "чтобы отправить его.")
    await emoji.set_id(args[0], custom_id)
    await message.answer(f"✅ <code>{args[0]}</code> → {emoji.e(args[0])} (ID <code>{custom_id}</code>)")


@router.message(Command("delemoji"))
async def cmd_delemoji(message: Message, command: CommandObject):
    name = (command.args or "").strip()
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
