"""Клиент Crypto Pay API (@CryptoBot)."""
import aiohttp

from .config import config


class CryptoPayError(Exception):
    pass


class CryptoPay:
    def __init__(self, token: str, testnet: bool = False):
        self.token = token
        self.base = "https://testnet-pay.crypt.bot/api/" if testnet else "https://pay.crypt.bot/api/"
        self._session: aiohttp.ClientSession | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    async def _call(self, method: str, **params):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        async with self._session.post(self.base + method, json=params,
                                      headers={"Crypto-Pay-API-Token": self.token}) as resp:
            data = await resp.json(content_type=None)
        if not data.get("ok"):
            raise CryptoPayError(str(data.get("error")))
        return data["result"]

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def create_invoice(self, amount_rub: float, payload: str, description: str) -> dict:
        # Счёт выставляется в рублях, клиент платит любой из перечисленных криптовалют по курсу CryptoBot.
        return await self._call(
            "createInvoice",
            currency_type="fiat",
            fiat="RUB",
            amount=f"{amount_rub:.2f}",
            accepted_assets="USDT,TON,BTC,ETH,LTC,TRX,USDC,BNB",
            description=description,
            payload=payload,
            expires_in=3600,
        )

    async def get_invoices(self, invoice_ids: list[str]) -> list[dict]:
        result = await self._call("getInvoices", invoice_ids=",".join(invoice_ids))
        return result.get("items", [])


cryptopay = CryptoPay(config.cryptopay_token, config.cryptopay_testnet)
