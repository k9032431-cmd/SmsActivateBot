"""Фоновые задачи: ожидание СМС по заказам и проверка крипто-платежей."""
import asyncio
import logging

from aiogram import Bot

from . import db, order_view
from .config import config
from .grizzly import grizzly
from .handlers.balance import check_crypto

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


async def _process(bot: Bot, order) -> None:
    status, code = await grizzly.get_status(order["activation_id"])
    expired = db.now() - order["created_at"] > config.order_timeout_min * 60

    if status == "OK" and code and code != order["code"]:
        await db.move_order(order["id"], (db.WAITING, db.GOT_CODE), db.GOT_CODE, code=code)
        await _send_card(bot, order, new_message=True)
        return

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


async def crypto_loop(bot: Bot) -> None:
    while True:
        try:
            payments = await db.pending_payments("crypto")
            for i in range(0, len(payments), 100):
                await check_crypto(bot, payments[i:i + 100])
        except Exception:
            log.exception("crypto loop")
        await asyncio.sleep(15)
