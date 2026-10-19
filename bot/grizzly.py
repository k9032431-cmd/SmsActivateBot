"""Клиент Grizzly SMS (протокол совместим с sms-activate)."""
import json
import logging

import aiohttp

from .config import config

API_URL = "https://api.grizzlysms.com/stubs/handler_api.php"
log = logging.getLogger(__name__)


class GrizzlyError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class Grizzly:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session: aiohttp.ClientSession | None = None

    async def _request(self, action: str, **params) -> str:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        query = {"api_key": self.api_key, "action": action}
        query.update({k: str(v) for k, v in params.items() if v is not None})
        async with self._session.get(API_URL, params=query) as resp:
            text = (await resp.text()).strip()
        log.debug("grizzly %s %s -> %s", action, params, text[:200])
        return text

    async def _json(self, action: str, **params):
        text = await self._request(action, **params)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise GrizzlyError(text) from None

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_balance(self) -> float:
        text = await self._request("getBalance")
        if not text.startswith("ACCESS_BALANCE:"):
            raise GrizzlyError(text)
        return float(text.split(":", 1)[1])

    async def get_services(self) -> dict[str, str]:
        data = await self._json("getServicesList")
        return {s["code"]: s["name"] for s in data.get("services", [])}

    async def get_countries(self) -> dict[int, dict]:
        data = await self._json("getCountries")
        items = data.values() if isinstance(data, dict) else data
        return {int(c["id"]): c for c in items}

    async def get_prices(self, service: str, country: int | None = None) -> dict[int, tuple[float, int]]:
        """{country_id: (цена в валюте Grizzly, количество номеров)}"""
        data = await self._json("getPrices", service=service, country=country)
        result = {}
        for country_id, services in (data or {}).items():
            info = services.get(service) if isinstance(services, dict) else None
            if info:
                result[int(country_id)] = (float(info["cost"]), int(info["count"]))
        return result

    async def get_number(self, service: str, country: int, max_price: float | None = None) -> tuple[str, str]:
        text = await self._request("getNumber", service=service, country=country, maxPrice=max_price)
        if not text.startswith("ACCESS_NUMBER:"):
            raise GrizzlyError(text)
        _, activation_id, phone = text.split(":", 2)
        return activation_id, phone

    async def get_status(self, activation_id: str) -> tuple[str, str | None]:
        """('WAIT' | 'OK' | 'CANCEL' | 'RETRY' | 'RESEND' | ошибка, код)"""
        text = await self._request("getStatus", id=activation_id)
        if text.startswith("STATUS_OK:"):
            return "OK", text.split(":", 1)[1]
        if text.startswith("STATUS_WAIT_RETRY"):
            return "RETRY", None
        return {
            "STATUS_WAIT_CODE": ("WAIT", None),
            "STATUS_WAIT_RESEND": ("RESEND", None),
            "STATUS_CANCEL": ("CANCEL", None),
        }.get(text, (text, None))

    async def set_status(self, activation_id: str, status: int) -> str:
        return await self._request("setStatus", id=activation_id, status=status)


grizzly = Grizzly(config.grizzly_api_key)
