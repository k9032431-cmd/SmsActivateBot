from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery

from .. import catalog, db, order_view
from ..common import show
from ..grizzly import grizzly
from ..i18n import fmt_money, t
from ..keyboards import BLUE, GREEN, btn, kb
from .start import home_btn

router = Router()

STATUS_ICON = {db.WAITING: "⏳", db.GOT_CODE: "✅", db.DONE: "🏁", db.CANCELLED: "❌"}


async def own_order(call: CallbackQuery):
    order = await db.get_order(int(call.data.split(":")[1]))
    if not order or order["user_id"] != call.from_user.id:
        await call.answer()
        return None
    return order


async def redraw(call: CallbackQuery, order_id: int, lang):
    order = await db.get_order(order_id)
    text, markup = order_view.render(order, lang)
    msg = await show(call, text, markup)
    if order["status"] in (db.WAITING, db.GOT_CODE):
        await db.set_order_message(order_id, msg.chat.id, msg.message_id)


@router.callback_query(F.data == "orders")
async def orders_list(call: CallbackQuery, lang):
    await call.answer()
    orders = await db.user_orders(call.from_user.id)
    await catalog.refresh()
    if not orders:
        return await show(call, t(lang, "orders_empty"), kb(
            btn(t(lang, "btn_buy"), "buy", GREEN, cb="buy"), home_btn(lang)))
    lines = [t(lang, "orders_title")]
    buttons = []
    for o in orders:
        lines.append(
            f"{STATUS_ICON[o['status']]} <code>+{o['phone']}</code> · {escape(catalog.service_name(o['service']))}"
            f" · {fmt_money(o['price'])}\n      └ {t(lang, 'status_' + o['status'])}"
            + (f" · <code>{escape(o['code'])}</code>" if o["code"] else "")
        )
        if o["status"] in (db.WAITING, db.GOT_CODE):
            buttons.append(btn(f"+{o['phone']} · {catalog.service_name(o['service'])}", "phone", BLUE,
                               cb=f"o:{o['id']}"))
    await show(call, "\n".join(lines), kb(*buttons, home_btn(lang)))


@router.callback_query(F.data.startswith("o:"))
async def open_order(call: CallbackQuery, lang):
    order = await own_order(call)
    if order:
        await call.answer()
        await redraw(call, order["id"], lang)


@router.callback_query(F.data.startswith("oc:"))
async def cancel_order(call: CallbackQuery, lang):
    order = await own_order(call)
    if not order:
        return
    if order["status"] != db.WAITING:
        await call.answer()
        return await redraw(call, order["id"], lang)
    if db.now() - order["created_at"] < 120:
        return await call.answer(t(lang, "cancel_early"), show_alert=True)
    answer = await grizzly.set_status(order["activation_id"], 8)
    if answer != "ACCESS_CANCEL":
        status, _ = await grizzly.get_status(order["activation_id"])
        if status != "CANCEL":
            return await call.answer(t(lang, "cancel_failed"), show_alert=True)
    await db.cancel_and_refund(order["id"])
    await call.answer()
    await redraw(call, order["id"], lang)


@router.callback_query(F.data.startswith("or:"))
async def another_sms(call: CallbackQuery, lang):
    order = await own_order(call)
    if not order:
        return
    if order["status"] == db.GOT_CODE:
        await grizzly.set_status(order["activation_id"], 3)
    await call.answer(t(lang, "another_sms_sent"), show_alert=True)


@router.callback_query(F.data.startswith("of:"))
async def finish_order(call: CallbackQuery, lang):
    order = await own_order(call)
    if not order:
        return
    if order["status"] == db.GOT_CODE:
        await grizzly.set_status(order["activation_id"], 6)
        await db.move_order(order["id"], (db.GOT_CODE,), db.DONE)
    await call.answer()
    await redraw(call, order["id"], lang)
