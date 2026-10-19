"""Справочники сервисов/стран и расчёт цен с наценкой."""
import math
import time

from . import db
from .config import config
from .grizzly import grizzly

# Популярные сервисы показываются на первой странице (коды протокола sms-activate).
POPULAR = ["tg", "wa", "ig", "go", "fb", "tw", "ds", "lf", "vk", "ok",
           "ya", "ma", "mm", "am", "oi", "wb", "ts", "nf", "mt", "av"]

# ID стран протокола sms-activate -> ISO-код (для флага).
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
    if 0 <= country_id < len(_ISO):
        return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in _ISO[country_id])
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
