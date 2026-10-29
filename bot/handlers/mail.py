"""Временная почта (Boomlify): покупка адреса, входящие письма."""
import html
import logging
import re
import time
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from .. import db
from ..boomlify import TIERS, BoomlifyError, boomlify
from ..common import show
from ..config import config
from ..emoji import e
from ..i18n import fmt_money, t
from ..keyboards import BLUE, GREEN, btn, kb

router = Router()
log = logging.getLogger(__name__)

DEFAULT_PRICES = {"10min": 5, "1hour": 10, "1day": 20, "permanent": 50}  # ₽
TIER_SECONDS = {"10min": 600, "1hour": 3600, "1day": 86400, "permanent": 60 * 86400}


async def price(tier: str) -> int:
    """Цена в копейках."""
    rub = float(await db.get_setting(f"mail_price_{tier}", str(DEFAULT_PRICES[tier])))
    return round(rub * 100)


def _expires_ts(created: dict, tier: str) -> int:
    raw = created.get("expires_at")
    if raw:
        try:
            return int(datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp())
        except ValueError:
            pass
    return db.now() + TIER_SECONDS[tier]


def _fmt_time(ts: int) -> str:
    return time.strftime("%d.%m %H:%M", time.localtime(ts))


_CODE_NEAR = re.compile(r"(?:code|код|kod|pin|otp|verification)[^0-9A-Z]{0,40}([A-Z0-9-]{4,10})", re.I)
_DIGITS = re.compile(r"(?<![\d.,])\d{4,8}(?![\d.,])")


def extract_code(subject: str, body: str) -> str | None:
    """Ищет код подтверждения: сначала рядом со словом «код/code», потом просто 4–8 цифр."""
    for text in (subject, body):
        m = _CODE_NEAR.search(text)
        if m and any(ch.isdigit() for ch in m.group(1)):
            return m.group(1)
    for text in (subject, body):
        m = _DIGITS.search(text)
        if m:
            return m.group(0)
    return None


def clean_body(raw: str, limit: int = 700) -> str:
    """HTML письма -> короткий безопасный текст для Telegram."""
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw or "")
    text = re.sub(r"(?i)</?(b|i|u|em|strong|span|a|font|small|big)\b[^>]*>", "", text)  # строчные теги — без пробелов
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", text)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return html.escape(text)


def message_view(mail, msg: dict, lang) -> tuple[str, object]:
    subject = (msg.get("subject") or "—").strip()
    raw_body = msg.get("body") or msg.get("text") or msg.get("html") or ""
    code = extract_code(subject, re.sub(r"<[^>]+>", " ", raw_body))
    text = t(lang, "mail_new", address=html.escape(mail["address"]),
             sender=html.escape(str(msg.get("from") or "—")), subject=html.escape(subject[:200]),
             code_line=t(lang, "mail_code_line", code=html.escape(code)) if code else "",
             body=clean_body(raw_body))
    rows = []
    if code:
        rows.append(btn(t(lang, "btn_copy_code"), "code", GREEN, copy=code))
    rows.append(btn(t(lang, "btn_inbox"), "inbox", BLUE, cb=f"mi:{mail['id']}"))
    return text, kb(*rows)


def mail_card(mail, count: int, lang):
    alive = mail["expires_at"] > db.now()
    if alive:
        text = t(lang, "mail_card", address=html.escape(mail["address"]), expires=_fmt_time(mail["expires_at"]),
                 count=count)
    else:
        text = t(lang, "mail_expired", address=html.escape(mail["address"]), count=count)
    rows = []
    if alive:
        rows.append([btn(t(lang, "btn_copy_mail"), "copy", BLUE, copy=mail["address"]),
                     btn(t(lang, "btn_inbox"), "inbox", BLUE, cb=f"mi:{mail['id']}")])
    rows += [btn(t(lang, "btn_my_mails"), "orders", BLUE, cb="mails"),
             btn(t(lang, "btn_home"), "home", cb="menu")]
    return text, kb(*rows)


@router.callback_query(F.data == "mail")
async def mail_menu(call: CallbackQuery, lang):
    await call.answer()
    rows = [btn(f"{t(lang, 'tier_' + tier)} — {fmt_money(await price(tier))}", "mail", GREEN if i == 0 else BLUE,
                cb=f"mb:{tier}") for i, tier in enumerate(TIERS)]
    rows += [btn(t(lang, "btn_my_mails"), "orders", BLUE, cb="mails"),
             btn(t(lang, "btn_back"), "back", cb="menu")]
    await show(call, t(lang, "mail_menu"), kb(*rows))


@router.callback_query(F.data.startswith("mb:"))
async def mail_buy(call: CallbackQuery, bot: Bot, lang):
    tier = call.data.split(":", 1)[1]
    if tier not in TIERS or not boomlify.enabled:
        return await call.answer()
    user_id = call.from_user.id
    cost = await price(tier)
    if not await db.charge(user_id, cost):
        user = await db.get_user(user_id)
        await call.answer()
        return await show(call, t(lang, "mail_not_enough", missing=fmt_money(cost - user["balance"])), kb(
            btn(t(lang, "btn_topup"), "topup", GREEN, cb="topup"), btn(t(lang, "btn_back"), "back", cb="mail")))
    await call.answer()
    try:
        created = await boomlify.create(tier)
        mail_id, address = str(created["id"]), created["address"]
    except Exception as exc:
        await db.add_balance(user_id, cost)
        log.warning("boomlify create failed: %r", exc)
        status = exc.status if isinstance(exc, BoomlifyError) else 0
        if status in (401, 402, 403, 429):
            for admin in config.admin_ids:
                try:
                    await bot.send_message(admin, f"{e('warning')} Boomlify не создал почту: "
                                                  f"<code>{html.escape(str(exc))}</code>\n"
                                                  "Проверьте ключ, кредиты и лимиты на boomlify.com")
                except Exception:
                    pass
        return await show(call, t(lang, "mail_error"), kb(btn(t(lang, "btn_back"), "back", cb="mail")))
    row_id = await db.create_mail(user_id, mail_id, address, tier, cost, _expires_ts(created, tier))
    text, markup = mail_card(await db.get_mail(row_id), 0, lang)
    await show(call, text, markup)


@router.callback_query(F.data == "mails")
async def my_mails(call: CallbackQuery, lang):
    await call.answer()
    mails = await db.user_mails(call.from_user.id)
    if not mails:
        return await show(call, t(lang, "my_mails_empty"), kb(
            btn(t(lang, "btn_mail"), "mail", GREEN, cb="mail"), btn(t(lang, "btn_back"), "back", cb="menu")))
    lines, buttons = [t(lang, "my_mails_title")], []
    for m in mails:
        alive = m["expires_at"] > db.now()
        status = t(lang, "mail_active") + f" · {_fmt_time(m['expires_at'])}" if alive else t(lang, "mail_expired_short")
        lines.append(f"{e('ok' if alive else 'done')} <code>{html.escape(m['address'])}</code> · <i>{status}</i>")
        if alive:
            buttons.append(btn(m["address"], "mail", BLUE, cb=f"mo:{m['id']}"))
    await show(call, "\n".join(lines), kb(*buttons, btn(t(lang, "btn_mail"), "mail", GREEN, cb="mail"),
                                          btn(t(lang, "btn_back"), "back", cb="menu")))


async def _own_mail(call: CallbackQuery):
    mail = await db.get_mail(int(call.data.split(":")[1]))
    if not mail or mail["user_id"] != call.from_user.id:
        await call.answer()
        return None
    return mail


async def _fetch(mail) -> list[dict]:
    if mail["expires_at"] <= db.now():
        return []
    try:
        return await boomlify.messages(mail["mail_id"])
    except Exception as exc:
        log.warning("boomlify messages %s: %r", mail["id"], exc)
        return []


@router.callback_query(F.data.startswith("mo:"))
async def open_mail(call: CallbackQuery, lang):
    mail = await _own_mail(call)
    if mail:
        await call.answer()
        text, markup = mail_card(mail, len(await _fetch(mail)), lang)
        await show(call, text, markup)


@router.callback_query(F.data.startswith("mi:"))
async def inbox(call: CallbackQuery, lang):
    mail = await _own_mail(call)
    if not mail:
        return
    await call.answer()
    msgs = await _fetch(mail)
    lines = [t(lang, "inbox_title", address=html.escape(mail["address"]))]
    if not msgs:
        lines.append(t(lang, "inbox_empty"))
    for msg in msgs[:5]:
        subject = html.escape((msg.get("subject") or "—")[:80])
        code = extract_code(msg.get("subject") or "", re.sub(r"<[^>]+>", " ", msg.get("body") or ""))
        lines.append(f"{e('inbox')} <b>{subject}</b>\n      {html.escape(str(msg.get('from') or '—'))[:60]}"
                     + (f" · {e('code')} <code>{html.escape(code)}</code>" if code else ""))
        await db.mark_seen(mail["id"], str(msg.get("id")))
    await show(call, "\n".join(lines), kb(
        btn(t(lang, "btn_refresh"), "refresh", BLUE, cb=f"mi:{mail['id']}"),
        btn(t(lang, "btn_back"), "back", cb=f"mo:{mail['id']}"),
    ))
