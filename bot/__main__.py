import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from . import catalog, db, emoji, workers
from .common import UserMiddleware
from .config import config
from .cryptomus import cryptomus
from .cryptopay import cryptopay
from .grizzly import grizzly
from .yoomoney import yoomoney
from .handlers import admin, balance, buy, orders, start


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not config.bot_token or not config.grizzly_api_key:
        raise SystemExit("Заполните BOT_TOKEN и GRIZZLY_API_KEY в файле .env")

    await db.init()
    await emoji.load()
    try:
        await catalog.refresh(force=True)
    except Exception:
        logging.exception("Не удалось загрузить список сервисов Grizzly — проверьте GRIZZLY_API_KEY")

    bot = Bot(config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    for observer in (dp.message, dp.callback_query, dp.pre_checkout_query):
        observer.outer_middleware(UserMiddleware())
    # Порядок важен: buy последним — в нём «любой текст = поиск сервиса».
    dp.include_routers(admin.router, start.router, balance.router, orders.router, buy.router)

    await bot.set_my_commands([BotCommand(command="start", description="Main menu · Главное меню")])
    tasks = [asyncio.create_task(workers.orders_loop(bot)),
             asyncio.create_task(workers.payments_loop(bot))]
    try:
        await dp.start_polling(bot)
    finally:
        for task in tasks:
            task.cancel()
        await grizzly.close()
        await cryptopay.close()
        await cryptomus.close()
        await yoomoney.close()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
