import logging
from html import escape

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from .. import catalog, db, order_view
from ..common import show
from ..config import config
from ..grizzly import GrizzlyError, grizzly
from ..i18n import fmt_money, t
from ..keyboards import BLUE, GREEN, btn, grid, kb
from .start import home_btn

router = Router()
log = logging.getLogger(__name__)

SERVICES_PER_PAGE = 20
COUNTRIES_PER_PAGE = 10


class Search(StatesGroup):
    query = State()


def back_btn(lang, cb: str):
    return btn(t(lang, "btn_back"), "back", cb=cb)


def services_kb(lang, items: list[tuple[str, str]], extra_rows: list | None = None):
    buttons = [btn(name[:30], cb=f"svc:{code}:0", style=BLUE) for code, name in items]
    return kb(*grid(buttons, 2), *(extra_rows or []))


def pager(lang, prefix: str, page: int, pages: int):
    row = []
    if page > 0:
        row.append(btn(f"{page}/{pages}", "back", cb=f"{prefix}:{page - 1}"))
    if page < pages - 1:
        row.append(btn(f"{page + 2}/{pages}", "next", cb=f"{prefix}:{page + 1}"))
    return row


@router.callback_query(F.data == "buy")
async def buy_menu(call: CallbackQuery, lang, state: FSMContext):
    await state.clear()
    await call.answer()
    try:
        items = await catalog.popular()
    except Exception:
        log.exception("services")
        return await show(call, t(lang, "buy_error"), kb(home_btn(lang)))
    await show(call, t(lang, "choose_service"), services_kb(lang, items, [
        [btn(t(lang, "btn_search"), "search", GREEN, cb="search"),
         btn(t(lang, "btn_all_services"), "phone", BLUE, cb="all:0")],
        home_btn(lang),
    ]))


@router.callback_query(F.data.startswith("all:"))
async def all_services(call: CallbackQuery, lang):
    await call.answer()
    items = sorted((await catalog.services()).items(), key=lambda x: x[1].lower())
    pages = max(1, -(-len(items) // SERVICES_PER_PAGE))
    page = min(max(0, int(call.data.split(":")[1])), pages - 1)
    chunk = items[page * SERVICES_PER_PAGE:(page + 1) * SERVICES_PER_PAGE]
    await show(call, t(lang, "all_services", page=page + 1, pages=pages), services_kb(lang, chunk, [
        pager(lang, "all", page, pages),
        [btn(t(lang, "btn_search"), "search", GREEN, cb="search"), back_btn(lang, "buy")],
    ]))


@router.callback_query(F.data == "search")
async def search_start(call: CallbackQuery, lang, state: FSMContext):
    await call.answer()
    await state.set_state(Search.query)
    await show(call, t(lang, "search_prompt"), kb(back_btn(lang, "buy")))


async def do_search(message: Message, lang, query: str):
    query = query.strip()[:40]
    items = (await catalog.search(query))[:30]
    if not items:
        return await message.answer(t(lang, "search_empty", query=escape(query)),
                                    reply_markup=kb(back_btn(lang, "buy")))
    await message.answer(t(lang, "search_results", query=escape(query)),
                         reply_markup=services_kb(lang, items, [back_btn(lang, "buy")]))


@router.message(Search.query, F.text)
async def search_query(message: Message, lang, state: FSMContext):
    await state.clear()
    await do_search(message, lang, message.text)


@router.callback_query(F.data.startswith("svc:"))
async def countries(call: CallbackQuery, lang):
    _, service, page = call.data.split(":")
    await call.answer()
    await catalog.refresh()
    name = escape(catalog.service_name(service))
    try:
        items = await catalog.offers(service)
    except Exception:
        log.exception("prices %s", service)
        return await show(call, t(lang, "buy_error"), kb(back_btn(lang, "buy")))
    if not items:
        return await show(call, t(lang, "no_countries", service=name), kb(back_btn(lang, "buy")))
    pages = max(1, -(-len(items) // COUNTRIES_PER_PAGE))
    page = min(max(0, int(page)), pages - 1)
    rows = [
        btn(f"{catalog.country_name(cid, lang)} — {fmt_money(price)}", cb=f"c:{service}:{cid}", style=BLUE)
        for cid, _cost, _count, price in items[page * COUNTRIES_PER_PAGE:(page + 1) * COUNTRIES_PER_PAGE]
    ]
    rows.append(pager(lang, f"svc:{service}", page, pages))
    rows.append([back_btn(lang, "buy"), home_btn(lang)])
    await show(call, t(lang, "choose_country", service=name, page=page + 1, pages=pages), kb(*rows))


async def find_offer(service: str, country: int, fresh: bool = False):
    for cid, cost, count, price in await catalog.offers(service, fresh=fresh):
        if cid == country:
            return cost, count, price
    return None


@router.callback_query(F.data.startswith("c:"))
async def confirm(call: CallbackQuery, user, lang):
    _, service, country = call.data.split(":")
    country = int(country)
    await call.answer()
    offer = await find_offer(service, country, fresh=True)
    if not offer:
        return await show(call, t(lang, "no_numbers"), kb(back_btn(lang, f"svc:{service}:0")))
    _cost, count, price = offer
    text = t(lang, "confirm", service=escape(catalog.service_name(service)),
             country=escape(catalog.country_name(country, lang)), price=fmt_money(price),
             count=count, balance=fmt_money(user["balance"]))
    if user["balance"] < price:
        markup = kb(
            btn(t(lang, "btn_topup"), "topup", GREEN, cb="topup"),
            back_btn(lang, f"svc:{service}:0"),
        )
        text += "\n\n" + t(lang, "not_enough", price=fmt_money(price), balance=fmt_money(user["balance"]))
    else:
        markup = kb(
            btn(t(lang, "btn_confirm_buy", price=fmt_money(price)), "buy", GREEN, cb=f"b:{service}:{country}"),
            back_btn(lang, f"svc:{service}:0"),
        )
    await show(call, text, markup)


@router.callback_query(F.data.startswith("b:"))
async def purchase(call: CallbackQuery, bot: Bot, lang):
    _, service, country = call.data.split(":")
    country = int(country)
    user_id = call.from_user.id
    back = kb(back_btn(lang, f"svc:{service}:0"))

    offer = await find_offer(service, country, fresh=True)
    if not offer:
        await call.answer()
        return await show(call, t(lang, "no_numbers"), back)
    cost, _count, price = offer
    if not await db.charge(user_id, price):
        user = await db.get_user(user_id)
        await call.answer()
        return await show(call, t(lang, "not_enough", price=fmt_money(price), balance=fmt_money(user["balance"])),
                          kb(btn(t(lang, "btn_topup"), "topup", GREEN, cb="topup"), back_btn(lang, "buy")))

    await call.answer(t(lang, "buying").split(" ", 1)[-1])
    try:
        activation_id, phone = await grizzly.get_number(service, country, max_price=cost)
    except Exception as exc:
        await db.add_balance(user_id, price)
        code = exc.code if isinstance(exc, GrizzlyError) else repr(exc)
        log.warning("getNumber %s/%s failed: %s", service, country, code)
        if code == "NO_BALANCE":
            for admin in config.admin_ids:
                try:
                    await bot.send_message(admin, "⚠️ На балансе Grizzly SMS закончились деньги — "
                                                  "клиенты не могут купить номера. Пополните аккаунт.")
                except Exception:
                    pass
        key = "no_numbers" if code in ("NO_NUMBERS", "WRONG_MAX_PRICE") or "maxPrice" in code else "buy_error"
        return await show(call, t(lang, key), back)

    order_id = await db.create_order(user_id, activation_id, service, country, phone,
                                     price, await catalog.cost_to_kopecks(cost))
    order = await db.get_order(order_id)
    text, markup = order_view.render(order, lang)
    msg = await show(call, text, markup)
    await db.set_order_message(order_id, msg.chat.id, msg.message_id)


@router.message(F.text & ~F.text.startswith("/"))
async def free_text_search(message: Message, lang, state: FSMContext):
    """Любой текст вне сценариев считаем поиском сервиса."""
    if await state.get_state() is not None or not lang:
        return
    await do_search(message, lang, message.text)
