"""Клиент Cryptomus: счёт на конкретную монету и сеть, клиент получает адрес и сумму."""
import base64
import hashlib
import json

import aiohttp

from .config import config

API_URL = "https://api.cryptomus.com/v1/"

# (код в callback, подпись на кнопке, монета, сеть Cryptomus)
NETWORKS = [
    ("usdt_trc", "USDT · TRC20", "USDT", "TRON"),
    ("usdt_bep", "USDT · BEP20", "USDT", "BSC"),
    ("usdt_ton", "USDT · TON", "USDT", "TON"),
    ("ton", "TON", "TON", "TON"),
    ("trx", "TRX · TRC20", "TRX", "TRON"),
    ("btc", "Bitcoin", "BTC", "BTC"),
    ("ltc", "Litecoin", "LTC", "LTC"),
    ("eth", "Ethereum", "ETH", "ETH"),
]
NETWORK_BY_CODE = {n[0]: n for n in NETWORKS}

PAID = {"paid", "paid_over"}
FAILED = {"cancel", "fail", "system_fail"}


class CryptomusError(Exception):
    pass


class Cryptomus:
    def __init__(self, merchant_id: str, api_key: str):
        self.merchant_id = merchant_id
        self.api_key = api_key
        self._session: aiohttp.ClientSession | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.merchant_id and self.api_key)

    async def _call(self, method: str, params: dict) -> dict:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        # Подпись считается от того же самого тела, которое уходит в запросе.
        body = json.dumps(params, separators=(",", ":"))
        sign = hashlib.md5(base64.b64encode(body.encode()) + self.api_key.encode()).hexdigest()
        headers = {"merchant": self.merchant_id, "sign": sign, "Content-Type": "application/json"}
        async with self._session.post(API_URL + method, data=body, headers=headers) as resp:
            data = await resp.json(content_type=None)
        if not isinstance(data, dict) or data.get("state") != 0:
            raise CryptomusError(str(data.get("message") or data.get("errors") or data)[:300])
        return data["result"]

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def create_invoice(self, amount_rub: float, order_id: str, coin: str, network: str) -> dict:
        return await self._call("payment", {
            "amount": f"{amount_rub:.2f}",
            "currency": "RUB",
            "to_currency": coin,
            "network": network,
            "order_id": order_id,
            "lifetime": 3600,
            "is_payment_multiple": False,
        })

    async def info(self, uuid: str) -> dict:
        return await self._call("payment/info", {"uuid": uuid})


cryptomus = Cryptomus(config.cryptomus_merchant_id, config.cryptomus_api_key)
