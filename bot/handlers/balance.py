import logging
import math

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from .. import catalog, db
from ..common import show
from ..config import config
from ..cryptomus import NETWORK_BY_CODE, NETWORKS, cryptomus
from ..cryptomus import FAILED as CRYPTOMUS_FAILED
from ..cryptomus import PAID as CRYPTOMUS_PAID
from ..cryptopay import cryptopay
from ..yoomoney import CARD as YM_CARD
from ..yoomoney import WALLET as YM_WALLET
from ..yoomoney import yoomoney
from ..i18n import fmt_money, t
from ..keyboards import BLUE, GREEN, btn, grid, kb
from .start import home_btn

router = Router()
log = logging.getLogger(__name__)

PRESETS = [100, 250, 500, 1000, 2500, 5000]
MAX_TOPUP = 100_000
# метод: (текст кнопки, эмодзи, цвет)
METHODS = {
    "ym_card": ("btn_pay_ym_card", "card", GREEN),
    "ym_wallet": ("btn_pay_ym_wallet", "wallet", BLUE),
    "card": ("btn_pay_card", "card", BLUE),
    "cryptomus": ("btn_pay_cryptomus", "crypto", BLUE),
    "crypto": ("btn_pay_crypto", "diamond", BLUE),
    "stars": ("btn_pay_stars", "star", BLUE),
}
YM_TYPES = {"ym_card": YM_CARD, "ym_wallet": YM_WALLET}


class Topup(StatesGroup):
    amount = State()


def method_enabled(method: str) -> bool:
    if method == "crypto":
        return cryptopay.enabled
    if method == "cryptomus":
        return cryptomus.enabled
    if method in YM_TYPES:
        return yoomoney.enabled
    if method == "card":
        return bool(config.payment_provider_token)
    return method == "stars"


@router.callback_query(F.data == "topup")
async def topup(call: CallbackQuery, user, lang, state: FSMContext):
    await state.clear()
    await call.answer()
    buttons = [btn(t(lang, label), emoji, style, cb=f"pm:{m}")
               for m, (label, emoji, style) in METHODS.items() if method_enabled(m)]
    await show(call, t(lang, "topup", balance=fmt_money(user["balance"])), kb(*buttons, btn(t(lang, "btn_back"), "back", cb="menu")))


@router.callback_query(F.data.startswith("pm:"))
async def choose_amount(call: CallbackQuery, lang, state: FSMContext):
    method = call.data.split(":")[1]
    await call.answer()
    if method not in METHODS or not method_enabled(method):
        return await show(call, t(lang, "pay_unavailable"), kb(btn(t(lang, "btn_back"), "back", cb="topup")))
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
    if method == "cryptomus":
        return await show(call, *network_screen(lang, int(amount)))
    await create_payment(bot, call.from_user.id, lang, method, int(amount))


def network_screen(lang, amount_rub: int):
    buttons = [btn(label, cb=f"cn:{amount_rub}:{code}", style=BLUE) for code, label, _, _ in NETWORKS]
    return (t(lang, "choose_network", amount=fmt_money(amount_rub * 100)),
            kb(*grid(buttons, 2), btn(t(lang, "btn_back"), "back", cb="pm:cryptomus")))


@router.callback_query(F.data.startswith("cn:"))
async def network_chosen(call: CallbackQuery, bot: Bot, lang):
    _, amount, code = call.data.split(":")
    await call.answer()
    await create_payment(bot, call.from_user.id, lang, "cryptomus", int(amount), network=code)


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
    if method == "cryptomus":
        text, markup = network_screen(lang, amount)
        return await message.answer(text, reply_markup=markup)
    await create_payment(bot, message.from_user.id, lang, method, amount)


async def create_payment(bot: Bot, user_id: int, lang, method: str, amount_rub: int, network: str | None = None):
    if method not in METHODS or not method_enabled(method):
        return await bot.send_message(user_id, t(lang, "pay_unavailable"))
    if method == "cryptomus" and network not in NETWORK_BY_CODE:
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

    if method == "cryptomus":
        _, label, coin, net = NETWORK_BY_CODE[network]
        try:
            invoice = await cryptomus.create_invoice(amount_rub, f"pay{payment_id}", coin, net)
        except Exception:
            log.exception("cryptomus createInvoice")
            return await bot.send_message(user_id, t(lang, "pay_unavailable"), reply_markup=kb(back))
        await db.set_payment_external(payment_id, invoice["uuid"], invoice.get("url"))
        pay_amount = invoice.get("payer_amount") or invoice.get("payment_amount") or "—"
        currency = invoice.get("payer_currency") or coin
        address = invoice.get("address")
        rows = []
        if address:
            rows.append([btn(t(lang, "btn_copy_address"), "copy", BLUE, copy=address),
                         btn(t(lang, "btn_copy_amount"), "money", BLUE, copy=str(pay_amount))])
        if invoice.get("url"):
            rows.append(btn(t(lang, "btn_pay_page"), "crypto", GREEN, url=invoice["url"]))
        rows += [btn(t(lang, "btn_check_pay"), "refresh", BLUE, cb=f"pc:{payment_id}"), back]
        text = t(lang, "cryptomus_invoice", coin=label, pay_amount=pay_amount, currency=currency,
                 network=label.split(" · ")[-1], address=address or "—", amount=fmt_money(amount))
        return await bot.send_message(user_id, text, reply_markup=kb(*rows))

    if method in YM_TYPES:
        label = f"pay{payment_id}"
        url = await yoomoney.pay_url(amount_rub, label, YM_TYPES[method], description)
        await db.set_payment_external(payment_id, label, url)
        return await bot.send_message(user_id, t(lang, "ym_invoice", method=t(lang, METHODS[method][0]),
                                                 amount=fmt_money(amount)), reply_markup=kb(
            btn(t(lang, "btn_pay"), "card", GREEN, url=url),
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
            await _credit(bot, payment)
        elif item["status"] == "expired":
            await db.expire_payment(payment["id"])


async def _credit(bot: Bot, payment) -> None:
    paid = await db.complete_payment(payment["id"])
    if paid:
        user = await db.get_user(paid["user_id"])
        await notify_paid(bot, paid, user["lang"])


async def check_cryptomus(bot: Bot, payment) -> None:
    info = await cryptomus.info(payment["external_id"])
    status = info.get("payment_status") or info.get("status")
    if status in CRYPTOMUS_PAID:
        await _credit(bot, payment)
    elif status in CRYPTOMUS_FAILED:
        await db.expire_payment(payment["id"])


async def check_yoomoney(bot: Bot, payment) -> None:
    op = await yoomoney.find_payment(payment["external_id"])
    # ЮMoney присылает сумму за вычетом своей комиссии, поэтому допускаем расхождение до 10%.
    if op and float(op.get("amount", 0)) * 100 >= payment["amount"] * 0.9:
        await _credit(bot, payment)
    elif db.now() - payment["created_at"] > 86400:
        await db.expire_payment(payment["id"])


async def check_one(bot: Bot, payment) -> None:
    if payment["method"] == "crypto":
        await check_crypto(bot, [payment])
    elif payment["method"] == "cryptomus":
        await check_cryptomus(bot, payment)
    elif payment["method"] in YM_TYPES:
        await check_yoomoney(bot, payment)


@router.callback_query(F.data.startswith("pc:"))
async def check_payment(call: CallbackQuery, bot: Bot, lang):
    payment = await db.get_payment(int(call.data.split(":")[1]))
    if not payment or payment["user_id"] != call.from_user.id:
        return await call.answer()
    if payment["status"] == "pending" and payment["external_id"]:
        try:
            await check_one(bot, payment)
        except Exception:
            log.exception("check payment %s", payment["id"])
        payment = await db.get_payment(payment["id"])
    if payment["status"] == "paid":
        await call.answer()
        await call.message.edit_reply_markup(reply_markup=None)
    else:
        await call.answer(t(lang, "pay_not_found"), show_alert=True)
