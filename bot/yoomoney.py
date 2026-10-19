"""Приём оплаты на кошелёк ЮMoney: картой (Мир, Visa, Mastercard) или с кошелька ЮMoney.

Клиент платит через форму ЮMoney, бот находит платёж по метке (label) в истории операций.
Для истории нужен токен: его можно получить командой `sudo smsbot yoomoney`.
"""
from urllib.parse import urlencode

import aiohttp

from .config import config

QUICKPAY_URL = "https://yoomoney.ru/quickpay/confirm"
HISTORY_URL = "https://yoomoney.ru/api/operation-history"

CARD = "AC"    # банковская карта
WALLET = "PC"  # кошелёк ЮMoney


class YooMoney:
    def __init__(self, wallet: str, token: str):
        self.wallet = wallet
        self.token = token
        self._session: aiohttp.ClientSession | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.wallet and self.token)

    def _sess(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def pay_url(self, amount_rub: int, label: str, payment_type: str, title: str) -> str:
        """Ссылка на форму оплаты. ЮMoney сам перенаправляет на страницу с готовой суммой."""
        params = {
            "receiver": self.wallet,
            "quickpay-form": "button",
            "targets": title,
            "paymentType": payment_type,
            "sum": amount_rub,
            "label": label,
        }
        url = f"{QUICKPAY_URL}?{urlencode(params)}"
        try:
            async with self._sess().post(url, allow_redirects=True) as resp:
                if resp.status < 400 and "yoomoney.ru" in str(resp.url) and str(resp.url) != url:
                    return str(resp.url)
        except aiohttp.ClientError:
            pass
        return url

    async def find_payment(self, label: str) -> dict | None:
        """Успешный входящий платёж с этой меткой или None."""
        async with self._sess().post(
            HISTORY_URL,
            data={"label": label, "type": "deposition", "records": 10},
            headers={"Authorization": f"Bearer {self.token}"},
        ) as resp:
            data = await resp.json(content_type=None)
        for op in data.get("operations", []):
            if op.get("label") == label and op.get("status") == "success" and op.get("direction") == "in":
                return op
        return None


yoomoney = YooMoney(config.yoomoney_wallet, config.yoomoney_token)
