"""Справочники сервисов/стран и расчёт цен с наценкой."""
import math
import re
import time
from functools import lru_cache

import pycountry

from . import db
from .config import config
from .grizzly import grizzly

# Популярные сервисы показываются на первой странице (коды протокола sms-activate).
POPULAR = ["tg", "wa", "ig", "go", "fb", "tw", "ds", "lf", "vk", "ok",
           "ya", "ma", "mm", "am", "oi", "wb", "ts", "nf", "mt", "av"]

# Названия стран, которые справочник pycountry не узнаёт сам (как их пишет Grizzly).
_NAME_ISO = {
    "usa": "US", "united states": "US", "uk": "GB", "england": "GB", "russia": "RU", "iran": "IR",
    "vietnam": "VN", "laos": "LA", "lao": "LA", "ivory coast": "CI", "cote d'ivoire": "CI",
    "dr congo": "CD", "congo (dem. republic)": "CD", "democratic republic of the congo": "CD",
    "republic of the congo": "CG", "congo": "CG", "south korea": "KR", "north korea": "KP", "korea": "KR",
    "moldova": "MD", "syria": "SY", "tanzania": "TZ", "bolivia": "BO", "venezuela": "VE",
    "macedonia": "MK", "north macedonia": "MK", "kosovo": "XK", "taiwan": "TW", "palestine": "PS",
    "czech republic": "CZ", "swaziland": "SZ", "eswatini": "SZ", "cape verde": "CV", "brunei": "BN",
    "brunei darussalam": "BN", "reunion": "RE", "macao": "MO", "macau": "MO", "hong kong": "HK",
    "timor-leste": "TL", "east timor": "TL", "gambia": "GM", "bahamas": "BS", "salvador": "SV",
    "el salvador": "SV", "saint vincent": "VC", "cayman islands": "KY", "benelux holland": "NL",
    "holland": "NL", "netherlands antilles": "CW", "png": "PG", "ruanda": "RW", "turkey": "TR",
    "micronesia": "FM", "saint kitts and nevis": "KN", "sint maarten": "SX", "vatican": "VA",
    "guinea-bissau": "GW", "kyrgyzstan": "KG", "bosnia": "BA", "virgin islands": "VG",
    "turks and caicos": "TC", "falkland islands": "FK", "burma": "MM", "myanmar": "MM", "libya": "LY",
}


@lru_cache(maxsize=None)
def _iso_by_name(name: str) -> str | None:
    n = " ".join(name.lower().replace("’", "'").split())
    base = re.sub(r"\s*\(.*?\)\s*", " ", n).strip()  # «USA (virtual)» -> «usa»
    for key in (n, base):
        if key in _NAME_ISO:
            return _NAME_ISO[key]
    try:
        return pycountry.countries.lookup(base).alpha_2
    except LookupError:
        pass
    try:
        return pycountry.countries.search_fuzzy(base)[0].alpha_2
    except LookupError:
        return None


def _flag_from_iso(iso: str) -> str:
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso.upper())


# Запасной вариант: ID стран протокола sms-activate -> ISO-код.
_ISO = (
    "RU UA KZ CN PH MM ID MY KE TZ VN KG US IL HK PL GB MG CD NG MO EG IN IE KH LA HT CI GM RS YE ZA RO "
    "CO EE AZ CA MA GH AR UZ CM TD DE LT HR SE IQ NL LV AT BY TH SA MX TW ES IR DZ SI BD SN TR CZ LK PE "
    "PK NZ GN ML VE ET MN BR AF UG AO CY FR PG MZ NP BE BG HU MD IT PY HN TN NI TL BO CR GT AE ZW PR SD "
    "TG KW SV LY JM TT EC SZ OM BA DO SY QA PA CU MR SL JO PT BB BI BJ BN BS BW BZ CF DM GD GE GR GW GY "
    "IS KM KN LR LS MW NA NE RW SK SR TJ MC BH RE ZM AM SO CG CL BF LB GA AL UY MU BT MV GP TM GF FI LC "
    "LU VC GQ DJ AG KY ME DK CH NO AU ER SS ST AW MS AI JP MK SC NC CV US"
).split()

_TTL = 6 * 3600
_services: dict[str, str] = {}
_countries: dict[int, dict] = {}
_loaded_at = 0.0


def flag(country_id: int) -> str:
    """Флаг по названию страны из Grizzly; если название не распознано — по номеру страны."""
    info = _countries.get(country_id)
    for name in (info.get("eng"), info.get("rus")) if info else ():
        iso = _iso_by_name(name) if name else None
        if iso:
            return _flag_from_iso(iso)
    if 0 <= country_id < len(_ISO):
        return _flag_from_iso(_ISO[country_id])
    return "🌐"


async def refresh(force: bool = False) -> None:
    global _loaded_at
    if not force and _services and time.time() - _loaded_at < _TTL:
        return
    services = await grizzly.get_services()
    countries = await grizzly.get_countries()
    if services:
        _services.clear()
        _services.update(services)
    if countries:
        _countries.clear()
        _countries.update(countries)
    _loaded_at = time.time()


async def services() -> dict[str, str]:
    await refresh()
    return _services


def counts() -> tuple[int, int]:
    """(сервисов, стран), округлено вниз до десятков — для красивого «180+»."""
    return len(_services) // 10 * 10, len(_countries) // 10 * 10


def service_name(code: str) -> str:
    return _services.get(code, code)


def country_name(country_id: int, lang: str | None) -> str:
    info = _countries.get(country_id)
    if not info:
        return f"{flag(country_id)} #{country_id}"
    name = info.get("rus") if lang == "ru" else info.get("eng")
    return f"{flag(country_id)} {name or info.get('eng') or country_id}"


async def popular() -> list[tuple[str, str]]:
    all_services = await services()
    return [(c, all_services[c]) for c in POPULAR if c in all_services]


async def search(query: str) -> list[tuple[str, str]]:
    q = query.lower().strip()
    found = [(c, n) for c, n in (await services()).items() if q in n.lower() or q == c]
    found.sort(key=lambda x: (not x[1].lower().startswith(q), x[1].lower()))
    return found


async def markup() -> float:
    return float(await db.get_setting("markup", str(config.default_markup)))


async def usd_rub() -> float:
    return float(await db.get_setting("usd_rub", str(config.default_usd_rub)))


async def low_balance_usd() -> float:
    """Порог уведомления о низком балансе Grizzly, в долларах."""
    return float(await db.get_setting("low_balance_usd", "1"))


async def grizzly_balance_usd(balance: float) -> float:
    return balance if config.grizzly_currency == "USD" else balance / await usd_rub()


async def star_rub() -> float:
    return float(await db.get_setting("star_rub", str(config.default_star_rub)))


async def cost_to_kopecks(cost: float) -> int:
    """Себестоимость у Grizzly -> копейки."""
    rub = cost * (await usd_rub() if config.grizzly_currency == "USD" else 1)
    return math.ceil(rub * 100)


async def sell_price(cost: float) -> int:
    """Цена для клиента в копейках: себестоимость × наценка, округление вверх до целого рубля."""
    kop = await cost_to_kopecks(cost) * await markup()
    return max(100, math.ceil(kop / 100) * 100)


_offers_cache: dict[str, tuple[float, dict]] = {}


async def offers(service: str, fresh: bool = False) -> list[tuple[int, float, int, int]]:
    """[(country_id, cost, count, sell_price)] по возрастанию цены, только где есть номера."""
    await refresh()
    cached = _offers_cache.get(service)
    if not fresh and cached and time.time() - cached[0] < 60:
        prices = cached[1]
    else:
        prices = await grizzly.get_prices(service)
        _offers_cache[service] = (time.time(), prices)
    result = [(cid, cost, count, await sell_price(cost))
              for cid, (cost, count) in prices.items() if count > 0 and cost > 0]
    result.sort(key=lambda x: x[3])
    return result
