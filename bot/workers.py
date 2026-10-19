"""Фоновые задачи: ожидание СМС по заказам и проверка крипто-платежей."""
import asyncio
import logging

from aiogram import Bot

from . import catalog, db, order_view
from .emoji import e
from .config import config
from .grizzly import grizzly
from .handlers.balance import check_crypto, check_one

log = logging.getLogger(__name__)


async def _send_card(bot: Bot, order, reason: str | None = None, new_message: bool = False) -> None:
    """Обновляет карточку заказа. new_message=True — шлёт новое сообщение, чтобы пришло уведомление."""
    order = await db.get_order(order["id"])
    user = await db.get_user(order["user_id"])
    text, markup = order_view.render(order, user["lang"], reason)
    if new_message or not order["message_id"]:
        if order["message_id"]:
            try:
                await bot.edit_message_reply_markup(chat_id=order["chat_id"], message_id=order["message_id"],
                                                    reply_markup=None)
            except Exception:
                pass
        msg = await bot.send_message(order["user_id"], text, reply_markup=markup)
        await db.set_order_message(order["id"], msg.chat.id, msg.message_id)
        return
    try:
        await bot.edit_message_text(text, chat_id=order["chat_id"], message_id=order["message_id"],
                                    reply_markup=markup)
    except Exception:
        await bot.send_message(order["user_id"], text, reply_markup=markup)


_shown_left: dict[int, int] = {}


async def _tick(bot: Bot, order) -> None:
    """Раз в минуту обновляет таймер и прогресс-бар в карточке ожидающего заказа."""
    left = order_view.minutes_left(order)
    if _shown_left.get(order["id"]) == left or not order["message_id"]:
        return
    _shown_left[order["id"]] = left
    user = await db.get_user(order["user_id"])
    text, markup = order_view.render(order, user["lang"])
    try:
        await bot.edit_message_text(text, chat_id=order["chat_id"], message_id=order["message_id"],
                                    reply_markup=markup)
    except Exception:
        pass


async def _process(bot: Bot, order) -> None:
    status, code = await grizzly.get_status(order["activation_id"])
    expired = db.now() - order["created_at"] > config.order_timeout_min * 60

    if status == "OK" and code and code != order["code"]:
        await db.move_order(order["id"], (db.WAITING, db.GOT_CODE), db.GOT_CODE, code=code)
        await _send_card(bot, order, new_message=True)
        return

    if order["status"] == db.WAITING and not expired:
        await _tick(bot, order)

    if order["status"] == db.GOT_CODE:
        if expired:
            await grizzly.set_status(order["activation_id"], 6)
            if await db.move_order(order["id"], (db.GOT_CODE,), db.DONE):
                await _send_card(bot, order)
        return

    # WAITING: кода ещё не было
    if status == "CANCEL" or expired:
        if status != "CANCEL":
            answer = await grizzly.set_status(order["activation_id"], 8)
            if answer != "ACCESS_CANCEL":
                status, code = await grizzly.get_status(order["activation_id"])
                if status == "OK" and code:
                    return  # код пришёл в последний момент — обработаем на следующем круге
                if status != "CANCEL":
                    log.warning("cannot cancel order %s: %s / %s", order["id"], answer, status)
                    return
        if await db.cancel_and_refund(order["id"]):
            await _send_card(bot, order, reason="timeout", new_message=True)


async def orders_loop(bot: Bot) -> None:
    while True:
        try:
            for order in await db.active_orders():
                try:
                    await _process(bot, order)
                except Exception:
                    log.exception("order %s", order["id"])
        except Exception:
            log.exception("orders loop")
        await asyncio.sleep(5)


LOW_BALANCE_CHECK_SEC = 300
LOW_BALANCE_REMIND_SEC = 3 * 3600


async def _notify_admins(bot: Bot, text: str) -> None:
    for admin in config.admin_ids:
        try:
            await bot.send_message(admin, text)
        except Exception:
            log.warning("cannot notify admin %s", admin)


async def low_balance_loop(bot: Bot) -> None:
    """Раз в 5 минут проверяет баланс Grizzly и предупреждает админов, если он ниже порога.
    Пока баланс низкий — напоминает раз в 3 часа; после пополнения сообщает, что всё в порядке."""
    alerted_at = 0.0
    while True:
        try:
            balance = await grizzly.get_balance()
            usd = await catalog.grizzly_balance_usd(balance)
            threshold = await catalog.low_balance_usd()
            shown = f"{balance:.2f} {'$' if config.grizzly_currency == 'USD' else '₽'}"
            if usd < threshold:
                if not alerted_at or db.now() - alerted_at >= LOW_BALANCE_REMIND_SEC:
                    await _notify_admins(bot, (
                        f"{e('warning')} <b>Низкий баланс Grizzly SMS</b>\n\n"
                        f"{e('wallet')} Осталось: <b>{shown}</b>"
                        + (f" (≈ ${usd:.2f})" if config.grizzly_currency != "USD" else "") + "\n"
                        f"{e('bell')} Порог: <b>${threshold:g}</b>\n\n"
                        "Пополните баланс на grizzlysms.com, иначе клиенты не смогут купить номера."))
                    alerted_at = db.now()
            elif alerted_at:
                await _notify_admins(bot, f"{e('ok')} Баланс Grizzly пополнен: <b>{shown}</b>")
                alerted_at = 0.0
        except Exception:
            log.exception("low balance check")
        await asyncio.sleep(LOW_BALANCE_CHECK_SEC)


async def payments_loop(bot: Bot) -> None:
    """Проверяет неоплаченные счета CryptoBot, Cryptomus и ЮMoney и зачисляет оплаченные."""
    while True:
        try:
            payments = await db.pending_payments("crypto")
            for i in range(0, len(payments), 100):
                await check_crypto(bot, payments[i:i + 100])
            for method in ("cryptomus", "ym_card", "ym_wallet"):
                for payment in await db.pending_payments(method):
                    try:
                        await check_one(bot, payment)
                    except Exception:
                        log.exception("payment %s", payment["id"])
        except Exception:
            log.exception("payments loop")
        await asyncio.sleep(20)
