"""Клиент Boomlify: временная почта (адрес + входящие письма)."""
import logging

import aiohttp

from .config import config

log = logging.getLogger(__name__)
CONFIG_URL = "https://gen.boomlify.com/api-config.json"
DEFAULT_API_URL = "https://v1.boomlify.com"

# Сроки, которые поддерживает API (permanent у Boomlify живёт 60 дней).
TIERS = ["10min", "1hour", "1day", "permanent"]


class BoomlifyError(Exception):
    def __init__(self, code: str, status: int = 0):
        super().__init__(code)
        self.code = code
        self.status = status


class Boomlify:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._base: str | None = None
        self._session: aiohttp.ClientSession | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _sess(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def _base_url(self) -> str:
        # Boomlify меняет адрес API, актуальный публикуется в api-config.json.
        if not self._base:
            try:
                async with self._sess().get(CONFIG_URL) as resp:
                    self._base = (await resp.json(content_type=None)).get("API_URL") or DEFAULT_API_URL
            except Exception:
                log.warning("boomlify config unavailable, using default API URL")
                self._base = DEFAULT_API_URL
        return self._base

    async def _call(self, method: str, path: str, **params) -> dict:
        url = await self._base_url() + path
        headers = {"X-API-Key": self.api_key, "Accept": "application/json"}
        async with self._sess().request(method, url, params=params or None, headers=headers) as resp:
            data = await resp.json(content_type=None)
        if resp.status >= 400 or not isinstance(data, dict) or data.get("success") is False:
            code = (data.get("error") or data.get("message")) if isinstance(data, dict) else str(data)
            raise BoomlifyError(str(code)[:200], resp.status)
        return data

    async def create(self, tier: str) -> dict:
        """{'id', 'address', 'expires_at', ...}"""
        data = await self._call("POST", "/api/v1/emails/create", time=tier)
        return data.get("email") or data

    async def messages(self, mail_id: str, limit: int = 20) -> list[dict]:
        """[{'id', 'from', 'to', 'subject', 'body', 'received_at'}] — новые первыми."""
        data = await self._call("GET", f"/api/v1/emails/{mail_id}/messages", limit=limit, offset=0)
        return data.get("messages_list") or data.get("messages") or []


boomlify = Boomlify(config.boomlify_api_key)
