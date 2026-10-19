"""SQLite-хранилище. Все суммы — в копейках (int), чтобы не терять точность."""
import time

import aiosqlite

from .config import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY,
    username    TEXT,
    full_name   TEXT,
    lang        TEXT,
    balance     INTEGER NOT NULL DEFAULT 0,
    banned      INTEGER NOT NULL DEFAULT 0,
    created_at  INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL,
    activation_id  TEXT NOT NULL,
    service        TEXT NOT NULL,
    country        INTEGER NOT NULL,
    phone          TEXT NOT NULL,
    price          INTEGER NOT NULL,
    cost           INTEGER NOT NULL,
    status         TEXT NOT NULL,
    code           TEXT,
    chat_id        INTEGER,
    message_id     INTEGER,
    created_at     INTEGER NOT NULL,
    updated_at     INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS orders_user ON orders(user_id);
CREATE TABLE IF NOT EXISTS payments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    method       TEXT NOT NULL,
    amount       INTEGER NOT NULL,
    external_id  TEXT,
    pay_url      TEXT,
    status       TEXT NOT NULL,
    created_at   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS payments_status ON payments(status);
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# Статусы заказа
WAITING = "waiting"      # номер выдан, ждём СМС
GOT_CODE = "got_code"    # код получен, можно запросить ещё
DONE = "done"            # завершён
CANCELLED = "cancelled"  # отменён, деньги возвращены

_db: aiosqlite.Connection | None = None


def now() -> int:
    return int(time.time())


async def init() -> None:
    global _db
    _db = await aiosqlite.connect(config.db_path)
    _db.row_factory = aiosqlite.Row
    await _db.executescript(SCHEMA)
    await _db.commit()


async def close() -> None:
    if _db:
        await _db.close()


def db() -> aiosqlite.Connection:
    assert _db is not None, "db.init() не вызван"
    return _db


# ---------- users ----------

async def get_user(user_id: int) -> aiosqlite.Row | None:
    async with db().execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cur:
        return await cur.fetchone()


async def upsert_user(user_id: int, username: str | None, full_name: str) -> aiosqlite.Row:
    await db().execute(
        "INSERT INTO users (id, username, full_name, created_at) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET username = excluded.username, full_name = excluded.full_name",
        (user_id, username, full_name, now()),
    )
    await db().commit()
    return await get_user(user_id)


async def set_lang(user_id: int, lang: str) -> None:
    await db().execute("UPDATE users SET lang = ? WHERE id = ?", (lang, user_id))
    await db().commit()


async def set_banned(user_id: int, banned: bool) -> bool:
    cur = await db().execute("UPDATE users SET banned = ? WHERE id = ?", (int(banned), user_id))
    await db().commit()
    return cur.rowcount > 0


async def add_balance(user_id: int, amount: int) -> bool:
    cur = await db().execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    await db().commit()
    return cur.rowcount > 0


async def charge(user_id: int, amount: int) -> bool:
    """Атомарно списывает сумму, если хватает баланса."""
    cur = await db().execute(
        "UPDATE users SET balance = balance - ? WHERE id = ? AND balance >= ?",
        (amount, user_id, amount),
    )
    await db().commit()
    return cur.rowcount > 0


async def all_user_ids() -> list[int]:
    async with db().execute("SELECT id FROM users WHERE banned = 0") as cur:
        return [r[0] for r in await cur.fetchall()]


# ---------- orders ----------

async def create_order(user_id: int, activation_id: str, service: str, country: int,
                       phone: str, price: int, cost: int) -> int:
    cur = await db().execute(
        "INSERT INTO orders (user_id, activation_id, service, country, phone, price, cost, status, "
        "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, activation_id, service, country, phone, price, cost, WAITING, now(), now()),
    )
    await db().commit()
    return cur.lastrowid


async def get_order(order_id: int) -> aiosqlite.Row | None:
    async with db().execute("SELECT * FROM orders WHERE id = ?", (order_id,)) as cur:
        return await cur.fetchone()


async def set_order_message(order_id: int, chat_id: int, message_id: int) -> None:
    await db().execute("UPDATE orders SET chat_id = ?, message_id = ? WHERE id = ?",
                       (chat_id, message_id, order_id))
    await db().commit()


async def move_order(order_id: int, from_statuses: tuple[str, ...], to_status: str,
                     code: str | None = None) -> bool:
    """Меняет статус, только если заказ сейчас в одном из from_statuses. Защищает от двойного возврата."""
    marks = ",".join("?" * len(from_statuses))
    cur = await db().execute(
        f"UPDATE orders SET status = ?, code = COALESCE(?, code), updated_at = ? "
        f"WHERE id = ? AND status IN ({marks})",
        (to_status, code, now(), order_id, *from_statuses),
    )
    await db().commit()
    return cur.rowcount > 0


async def cancel_and_refund(order_id: int) -> bool:
    order = await get_order(order_id)
    if not order or not await move_order(order_id, (WAITING,), CANCELLED):
        return False
    await add_balance(order["user_id"], order["price"])
    return True


async def user_bought_count(user_id: int) -> int:
    async with db().execute(
        "SELECT COUNT(*) FROM orders WHERE user_id = ? AND status IN (?, ?)", (user_id, GOT_CODE, DONE)
    ) as cur:
        return (await cur.fetchone())[0]


async def active_orders() -> list[aiosqlite.Row]:
    async with db().execute("SELECT * FROM orders WHERE status IN (?, ?)", (WAITING, GOT_CODE)) as cur:
        return await cur.fetchall()


async def user_orders(user_id: int, limit: int = 10) -> list[aiosqlite.Row]:
    async with db().execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
    ) as cur:
        return await cur.fetchall()


# ---------- payments ----------

async def create_payment(user_id: int, method: str, amount: int) -> int:
    cur = await db().execute(
        "INSERT INTO payments (user_id, method, amount, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
        (user_id, method, amount, now()),
    )
    await db().commit()
    return cur.lastrowid


async def set_payment_external(payment_id: int, external_id: str, pay_url: str | None = None) -> None:
    await db().execute("UPDATE payments SET external_id = ?, pay_url = ? WHERE id = ?",
                       (external_id, pay_url, payment_id))
    await db().commit()


async def get_payment(payment_id: int) -> aiosqlite.Row | None:
    async with db().execute("SELECT * FROM payments WHERE id = ?", (payment_id,)) as cur:
        return await cur.fetchone()


async def complete_payment(payment_id: int, external_id: str | None = None) -> aiosqlite.Row | None:
    """Помечает платёж оплаченным и зачисляет деньги. Возвращает платёж, если зачисление произошло сейчас."""
    cur = await db().execute(
        "UPDATE payments SET status = 'paid', external_id = COALESCE(?, external_id) "
        "WHERE id = ? AND status = 'pending'",
        (external_id, payment_id),
    )
    await db().commit()
    if cur.rowcount == 0:
        return None
    payment = await get_payment(payment_id)
    await add_balance(payment["user_id"], payment["amount"])
    return payment


async def expire_payment(payment_id: int) -> None:
    await db().execute("UPDATE payments SET status = 'expired' WHERE id = ? AND status = 'pending'",
                       (payment_id,))
    await db().commit()


async def pending_payments(method: str) -> list[aiosqlite.Row]:
    async with db().execute(
        "SELECT * FROM payments WHERE status = 'pending' AND method = ? AND external_id IS NOT NULL",
        (method,),
    ) as cur:
        return await cur.fetchall()


# ---------- settings ----------

async def get_setting(key: str, default: str | None = None) -> str | None:
    async with db().execute("SELECT value FROM settings WHERE key = ?", (key,)) as cur:
        row = await cur.fetchone()
    return row[0] if row else default


async def set_setting(key: str, value: str) -> None:
    await db().execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    await db().commit()


async def del_setting(key: str) -> None:
    await db().execute("DELETE FROM settings WHERE key = ?", (key,))
    await db().commit()


async def settings_with_prefix(prefix: str) -> dict[str, str]:
    async with db().execute("SELECT key, value FROM settings WHERE key LIKE ?", (prefix + "%",)) as cur:
        return {r[0][len(prefix):]: r[1] for r in await cur.fetchall()}


# ---------- stats ----------

async def stats() -> dict:
    async def one(sql: str, *args) -> int:
        async with db().execute(sql, args) as cur:
            row = await cur.fetchone()
        return row[0] or 0

    day_ago = now() - 86400
    return {
        "users": await one("SELECT COUNT(*) FROM users"),
        "users_day": await one("SELECT COUNT(*) FROM users WHERE created_at >= ?", day_ago),
        "orders": await one("SELECT COUNT(*) FROM orders WHERE status IN ('got_code', 'done')"),
        "orders_day": await one(
            "SELECT COUNT(*) FROM orders WHERE status IN ('got_code', 'done') AND created_at >= ?", day_ago),
        "revenue": await one("SELECT SUM(price) FROM orders WHERE status IN ('got_code', 'done')"),
        "profit": await one("SELECT SUM(price - cost) FROM orders WHERE status IN ('got_code', 'done')"),
        "profit_day": await one(
            "SELECT SUM(price - cost) FROM orders WHERE status IN ('got_code', 'done') AND created_at >= ?",
            day_ago),
        "deposits": await one("SELECT SUM(amount) FROM payments WHERE status = 'paid'"),
        "balances": await one("SELECT SUM(balance) FROM users"),
    }
