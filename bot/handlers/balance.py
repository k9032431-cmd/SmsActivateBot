import logging
import math

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from .. import catalog, db
from ..common import show
from ..config import config
from ..cryptopay import cryptopay
from ..i18n import fmt_money, t
from ..keyboards import BLUE, GREEN, btn, grid, kb
from .start import home_btn

router = Router()
log = logging.getLogger(__name__)

PRESETS = [100, 250, 500, 1000, 2500, 5000]
MAX_TOPUP = 100_000
METHODS = {
    "crypto": ("btn_pay_crypto", "crypto"),
    "stars": ("btn_pay_stars", "star"),
    "card": ("btn_pay_card", "card"),
}


class Topup(StatesGroup):
    amount = State()


def method_enabled(method: str) -> bool:
    if method == "crypto":
        return cryptopay.enabled
    if method == "card":
        return bool(config.payment_provider_token)
    return method == "stars"


@router.callback_query(F.data == "topup")
async def topup(call: CallbackQuery, user, lang, state: FSMContext):
    await state.clear()
    await call.answer()
    styles = {"crypto": BLUE, "stars": GREEN, "card": BLUE}
    buttons = [btn(t(lang, label), emoji, styles[m], cb=f"pm:{m}")
               for m, (label, emoji) in METHODS.items() if method_enabled(m)]
    await show(call, t(lang, "topup", balance=fmt_money(user["balance"])), kb(*buttons, home_btn(lang)))


@router.callback_query(F.data.startswith("pm:"))
async def choose_amount(call: CallbackQuery, lang, state: FSMContext):
    method = call.data.split(":")[1]
    await call.answer()
    if method not in METHODS or not method_enabled(method):
        return await show(call, t(lang, "pay_unavailable"), kb(home_btn(lang)))
    await state.set_state(Topup.amount)
    await state.update_data(method=method)
    presets = [btn(f"{a} ₽", "money", GREEN, cb=f"pa:{method}:{a}") for a in PRESETS if a >= config.min_topup_rub]
    await show(call, t(lang, "choose_amount", method=t(lang, METHODS[method][0]), min=config.min_topup_rub),
               kb(*grid(presets, 3), btn(t(lang, "btn_back"), "back", cb="topup")))


@router.callback_query(F.data.startswith("pa:"))
async def amount_button(call: CallbackQuery, bot: Bot, lang, state: FSMContext):
    _, method, amount = call.data.split(":")
    await state.clear()
    await call.answer()
    await create_payment(bot, call.from_user.id, lang, method, int(amount))


@router.message(Topup.amount, F.text)
async def amount_text(message: Message, bot: Bot, lang, state: FSMContext):
    try:
        amount = int(float(message.text.replace(",", ".").replace("₽", "").strip()))
    except ValueError:
        amount = 0
    if not config.min_topup_rub <= amount <= MAX_TOPUP:
        return await message.answer(t(lang, "bad_amount", min=config.min_topup_rub))
    method = (await state.get_data()).get("method")
    await state.clear()
    await create_payment(bot, message.from_user.id, lang, method, amount)


async def create_payment(bot: Bot, user_id: int, lang, method: str, amount_rub: int):
    if method not in METHODS or not method_enabled(method):
        return await bot.send_message(user_id, t(lang, "pay_unavailable"))
    amount_rub = max(config.min_topup_rub, min(MAX_TOPUP, amount_rub))
    amount = amount_rub * 100
    payment_id = await db.create_payment(user_id, method, amount)
    back = btn(t(lang, "btn_back"), "back", cb="topup")
    description = t(lang, "stars_invoice_desc", amount=fmt_money(amount))

    if method == "crypto":
        try:
            invoice = await cryptopay.create_invoice(amount_rub, str(payment_id), description)
        except Exception:
            log.exception("cryptopay createInvoice")
            return await bot.send_message(user_id, t(lang, "pay_unavailable"), reply_markup=kb(back))
        url = invoice.get("bot_invoice_url") or invoice.get("pay_url")
        await db.set_payment_external(payment_id, str(invoice["invoice_id"]), url)
        return await bot.send_message(user_id, t(lang, "crypto_invoice", amount=fmt_money(amount)), reply_markup=kb(
            btn(t(lang, "btn_pay"), "crypto", GREEN, url=url),
            btn(t(lang, "btn_check_pay"), "refresh", BLUE, cb=f"pc:{payment_id}"),
            back,
        ))

    if method == "stars":
        stars = max(1, math.ceil(amount_rub / await catalog.star_rub()))
        prices = [LabeledPrice(label=fmt_money(amount), amount=stars)]
        currency, token, pay_text = "XTR", "", f"{t(lang, 'btn_pay')} {stars} ⭐"
    else:
        prices = [LabeledPrice(label=fmt_money(amount), amount=amount)]
        currency, token, pay_text = "RUB", config.payment_provider_token, f"{t(lang, 'btn_pay')} {fmt_money(amount)}"

    await bot.send_invoice(
        chat_id=user_id,
        title=t(lang, "btn_topup"),
        description=description,
        payload=f"pay:{payment_id}",
        provider_token=token,
        currency=currency,
        prices=prices,
        reply_markup=kb(btn(pay_text, "star" if method == "stars" else "card", GREEN, pay=True), back),
    )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    payment = None
    if query.invoice_payload.startswith("pay:"):
        payment = await db.get_payment(int(query.invoice_payload.split(":")[1]))
    ok = bool(payment and payment["status"] == "pending" and payment["user_id"] == query.from_user.id)
    await query.answer(ok=ok, error_message=None if ok else "Invoice expired")


@router.message(F.successful_payment)
async def successful_payment(message: Message, lang):
    sp = message.successful_payment
    if not sp.invoice_payload.startswith("pay:"):
        return
    payment = await db.complete_payment(int(sp.invoice_payload.split(":")[1]), sp.telegram_payment_charge_id)
    if payment:
        await notify_paid(message.bot, payment, lang)


async def notify_paid(bot: Bot, payment, lang):
    user = await db.get_user(payment["user_id"])
    await bot.send_message(payment["user_id"], t(lang, "pay_ok", amount=fmt_money(payment["amount"]),
                                                 balance=fmt_money(user["balance"])),
                           reply_markup=kb(btn(t(lang, "btn_buy"), "buy", GREEN, cb="buy"), home_btn(lang)))
    for admin in config.admin_ids:
        try:
            await bot.send_message(admin, f"💰 Пополнение {fmt_money(payment['amount'])} · {payment['method']} · "
                                          f"<code>{payment['user_id']}</code>")
        except Exception:
            pass


async def check_crypto(bot: Bot, payments) -> None:
    """Проверяет счета CryptoBot и зачисляет оплаченные. Используется и кнопкой, и фоновой задачей."""
    if not payments:
        return
    by_invoice = {p["external_id"]: p for p in payments}
    for item in await cryptopay.get_invoices(list(by_invoice)):
        payment = by_invoice.get(str(item["invoice_id"]))
        if not payment:
            continue
        if item["status"] == "paid":
            paid = await db.complete_payment(payment["id"])
            if paid:
                user = await db.get_user(paid["user_id"])
                await notify_paid(bot, paid, user["lang"])
        elif item["status"] == "expired":
            await db.expire_payment(payment["id"])


@router.callback_query(F.data.startswith("pc:"))
async def check_payment(call: CallbackQuery, bot: Bot, lang):
    payment = await db.get_payment(int(call.data.split(":")[1]))
    if not payment or payment["user_id"] != call.from_user.id:
        return await call.answer()
    if payment["status"] == "pending" and payment["external_id"]:
        try:
            await check_crypto(bot, [payment])
        except Exception:
            log.exception("check crypto")
        payment = await db.get_payment(payment["id"])
    if payment["status"] == "paid":
        await call.answer()
        await call.message.edit_reply_markup(reply_markup=None)
    else:
        await call.answer(t(lang, "pay_not_found"), show_alert=True)
