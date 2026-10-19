import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _list_int(value: str) -> list[int]:
    return [int(x) for x in value.replace(" ", "").split(",") if x]


@dataclass(frozen=True)
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    admin_ids: list[int] = field(default_factory=lambda: _list_int(os.getenv("ADMIN_IDS", "")))
    grizzly_api_key: str = os.getenv("GRIZZLY_API_KEY", "")
    # Валюта баланса аккаунта Grizzly: RUB или USD. Если USD — цены переводятся в рубли по USD_RUB_RATE.
    grizzly_currency: str = os.getenv("GRIZZLY_CURRENCY", "RUB").upper()
    cryptopay_token: str = os.getenv("CRYPTOPAY_TOKEN", "")
    cryptopay_testnet: bool = os.getenv("CRYPTOPAY_TESTNET", "0") == "1"
    # Токен платёжного провайдера из @BotFather (ЮKassa и т.п.) для оплаты картой в рублях.
    payment_provider_token: str = os.getenv("PAYMENT_PROVIDER_TOKEN", "")
    bot_name: str = os.getenv("BOT_NAME", "SMS Number Bot")
    support_username: str = os.getenv("SUPPORT_USERNAME", "")
    channel_url: str = os.getenv("CHANNEL_URL", "")
    db_path: str = os.getenv("DB_PATH", "bot.db")
    order_timeout_min: int = int(os.getenv("ORDER_TIMEOUT_MIN", "20"))

    # Значения по умолчанию; меняются из админ-панели и хранятся в БД.
    default_markup: float = float(os.getenv("MARKUP", "2.0"))
    default_usd_rub: float = float(os.getenv("USD_RUB_RATE", "95"))
    default_star_rub: float = float(os.getenv("STAR_RUB_RATE", "1.8"))
    min_topup_rub: int = int(os.getenv("MIN_TOPUP_RUB", "50"))


config = Config()
