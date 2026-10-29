import time
from html import escape

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .. import catalog, db
from ..common import send_banner, show
from ..boomlify import boomlify
from ..config import config
from ..i18n import LANGS, fmt_money, plain_t, t
from ..keyboards import BLUE, GREEN, btn, kb

router = Router()


def lang_kb(lang: str | None = None):
    rows = [btn(name, cb=f"lang:{code}", style=BLUE) for code, name in LANGS.items()]
    if lang:
        rows.append(btn(t(lang, "btn_back"), "back", cb="profile"))
    return kb(*rows)


def main_text(user, lang: str) -> str:
    services, countries = catalog.counts()
    name = user["full_name"] or (user["username"] and "@" + user["username"]) or "—"
    return t(lang, "main", bot_name=escape(config.bot_name), name=escape(name),
             services=services or 500, countries=countries or 150)


def main_kb(lang: str):
    rows = [
        btn(t(lang, "btn_buy"), "buy", GREEN, cb="buy"),
    ]
    if boomlify.enabled:
        rows.append(btn(t(lang, "btn_mail"), "mail", GREEN, cb="mail"))
    rows += [
        [btn(t(lang, "btn_profile"), "user", BLUE, cb="profile"),
         btn(t(lang, "btn_topup"), "topup", BLUE, cb="topup")],
    ]
    second = [btn(t(lang, "btn_orders"), "orders", BLUE, cb="orders")]
    if config.support_username:
        second.append(btn(t(lang, "btn_support"), "support", BLUE,
                          url=f"https://t.me/{config.support_username.lstrip('@')}"))
    rows.append(second)
    if config.channel_url:
        rows.append(btn(t(lang, "btn_channel"), "channel", BLUE, url=config.channel_url))
    return kb(*rows)


def home_btn(lang: str):
    return btn(t(lang, "btn_home"), "home", cb="menu")


@router.message(CommandStart())
async def cmd_start(message: Message, user, lang: str | None, state: FSMContext):
    await state.clear()
    if not lang:
        await message.answer(t(None, "choose_lang") + "\nChoose your language · Dili saýlaň",
                             reply_markup=lang_kb())
        return
    await send_banner(message.bot, message.chat.id, main_text(user, lang), main_kb(lang))


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(call: CallbackQuery):
    lang = call.data.split(":", 1)[1]
    if lang not in LANGS:
        return await call.answer()
    await db.set_lang(call.from_user.id, lang)
    user = await db.get_user(call.from_user.id)
    await call.answer(plain_t(lang, "lang_set"))
    await show(call, main_text(user, lang), main_kb(lang), banner=True)


@router.callback_query(F.data == "lang_menu")
async def lang_menu(call: CallbackQuery, lang: str | None):
    await call.answer()
    await show(call, t(lang, "choose_lang"), lang_kb(lang))


@router.callback_query(F.data.in_({"menu", "menu:new"}))
async def menu(call: CallbackQuery, user, lang: str | None, state: FSMContext):
    await state.clear()
    await call.answer()
    if not lang:
        return await show(call, t(None, "choose_lang"), lang_kb())
    if call.data == "menu:new":
        await send_banner(call.bot, call.from_user.id, main_text(user, lang), main_kb(lang))
        return
    await show(call, main_text(user, lang), main_kb(lang), banner=True)


@router.callback_query(F.data == "profile")
async def profile(call: CallbackQuery, user, lang: str | None):
    await call.answer()
    text = t(lang, "profile", user_id=user["id"], balance=fmt_money(user["balance"]),
             orders=await db.user_bought_count(user["id"]),
             since=time.strftime("%d.%m.%Y", time.localtime(user["created_at"])))
    await show(call, text, kb(
        btn(t(lang, "btn_topup"), "topup", GREEN, cb="topup"),
        [btn(t(lang, "btn_orders"), "orders", BLUE, cb="orders"),
         btn(t(lang, "btn_lang"), "lang", BLUE, cb="lang_menu")],
        btn(t(lang, "btn_back"), "back", cb="menu"),
    ))

