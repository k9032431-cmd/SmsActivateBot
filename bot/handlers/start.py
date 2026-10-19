from html import escape

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .. import db
from ..common import show
from ..config import config
from ..i18n import LANGS, fmt_money, t
from ..keyboards import BLUE, GREEN, btn, kb

router = Router()


def lang_kb():
    return kb(*[btn(name, cb=f"lang:{code}", style=BLUE) for code, name in LANGS.items()])


def main_text(user, lang: str) -> str:
    return t(lang, "main", bot_name=escape(config.bot_name), name=escape(user["full_name"] or "—"),
             user_id=user["id"], balance=fmt_money(user["balance"]))


def main_kb(lang: str):
    rows = [
        btn(t(lang, "btn_buy"), "buy", GREEN, cb="buy"),
        [btn(t(lang, "btn_topup"), "topup", BLUE, cb="topup"),
         btn(t(lang, "btn_orders"), "orders", BLUE, cb="orders")],
    ]
    bottom = [btn(t(lang, "btn_lang"), "lang", cb="lang_menu")]
    if config.support_username:
        bottom.append(btn(t(lang, "btn_support"), "support", cb="support"))
    rows.append(bottom)
    if config.channel_url:
        rows.append(btn(t(lang, "btn_channel"), "channel", url=config.channel_url))
    return kb(*rows)


def home_btn(lang: str):
    return btn(t(lang, "btn_home"), "home", cb="menu")


@router.message(CommandStart())
async def cmd_start(message: Message, user, lang: str | None, state: FSMContext):
    await state.clear()
    if not lang:
        await message.answer(t(None, "choose_lang") + "\n" + "Choose your language · Dili saýlaň",
                             reply_markup=lang_kb())
        return
    await message.answer(main_text(user, lang), reply_markup=main_kb(lang))


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(call: CallbackQuery):
    lang = call.data.split(":", 1)[1]
    if lang not in LANGS:
        return await call.answer()
    await db.set_lang(call.from_user.id, lang)
    user = await db.get_user(call.from_user.id)
    await call.answer(t(lang, "lang_set").split(" ", 1)[-1])
    await show(call, main_text(user, lang), main_kb(lang))


@router.callback_query(F.data == "lang_menu")
async def lang_menu(call: CallbackQuery, lang: str | None):
    await call.answer()
    await show(call, t(lang, "choose_lang"), lang_kb())


@router.callback_query(F.data == "menu")
async def menu(call: CallbackQuery, user, lang: str | None, state: FSMContext):
    await state.clear()
    await call.answer()
    if not lang:
        return await show(call, t(None, "choose_lang"), lang_kb())
    await show(call, main_text(user, lang), main_kb(lang))


@router.callback_query(F.data == "support")
async def support(call: CallbackQuery, lang: str | None):
    await call.answer()
    contact = "@" + config.support_username.lstrip("@")
    await show(call, t(lang, "support", contact=contact), kb(
        btn(contact, "support", BLUE, url=f"https://t.me/{contact[1:]}"),
        home_btn(lang),
    ))
