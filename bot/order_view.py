"""Карточка заказа: текст и кнопки в зависимости от статуса."""
from html import escape

from . import catalog, db
from .config import config
from .i18n import fmt_money, t
from .keyboards import BLUE, GREEN, RED, btn, kb


def minutes_left(order) -> int:
    total = config.order_timeout_min * 60
    return max(0, -(-(total - (db.now() - order["created_at"])) // 60))


def render(order, lang: str | None, reason: str | None = None):
    params = dict(
        left=minutes_left(order),
        phone=order["phone"],
        service=escape(catalog.service_name(order["service"])),
        country=escape(catalog.country_name(order["country"], lang)),
        price=fmt_money(order["price"]),
        code=escape(order["code"] or ""),
    )
    home = btn(t(lang, "btn_home"), "home", cb="menu:new")
    back_home = btn(t(lang, "btn_home"), "home", cb="menu")
    status = order["status"]
    if status == db.WAITING:
        return t(lang, "order_waiting", **params), kb(
            [btn(t(lang, "btn_copy_phone"), "phone", BLUE, copy=f"+{order['phone']}"),
             btn(t(lang, "btn_cancel_order"), "cancel", RED, cb=f"oc:{order['id']}")],
            home,
        )
    if status == db.GOT_CODE:
        return t(lang, "order_code", **params), kb(
            btn(t(lang, "btn_copy_code"), "code", GREEN, copy=order["code"] or ""),
            [btn(t(lang, "btn_another_sms"), "sms", BLUE, cb=f"or:{order['id']}"),
             btn(t(lang, "btn_finish"), "ok", GREEN, cb=f"of:{order['id']}")],
            home,
        )
    again = btn(t(lang, "btn_buy_more"), "buy", GREEN, cb=f"svc:{order['service']}:0")
    if status == db.DONE:
        return t(lang, "order_done", **params), kb(again, back_home)
    key = "order_timeout" if reason == "timeout" else "order_cancelled"
    return t(lang, key, **params), kb(again, back_home)
