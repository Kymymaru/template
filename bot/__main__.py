import asyncio
from functools import partial

from loguru import logger

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
)

from redis.asyncio import Redis

from bot.config import config
from bot.handlers import admin, user, group
from bot.middlewares import ThrottlingMiddleware, LoggingMiddleware, DatabaseInstance
from bot.database import Database
from bot.ui_commands import set_bot_commands


async def on_startup(bot: Bot, database: Database):
    if config.bot.skip_updates:
        await bot.delete_webhook(drop_pending_updates=True)
    if not config.bot.polling:
        await bot.set_webhook(f"{config.bot.BASE_URL}{config.bot.MAIN_BOT_PATH}")
    await database.create_tables()
    bot_object = await bot.get_me()
    config.bot.username = bot_object.username
    await set_bot_commands(bot, config.bot.admins)


def main():
    logs_folder = f'../{config.bot.logs_folder_name}/'
    logger.add(sink=logs_folder + 'logs.log', format="[{time}] {level} <lvl>{message}</lvl>", level="INFO")
    logger.add(sink=logs_folder + 'errors.log', format="[{time}] <lvl>{message}</lvl>", level="ERROR")
    '''
    Это сделано для того чтобы когда я скачивал скрипт с сервера, большие файлы логов не качались долго
    '''
    logger.info(f"Attempting Bot Startup")

    database = Database(config.database)

    logger.info("Database Engine Created")

    session = AiohttpSession()
    bot_settings = {"session": session, "parse_mode": ParseMode.HTML, 'disable_web_page_preview': True}
    bot = Bot(token=config.bot.token, **bot_settings)
    if config.bot.use_redis:
        storage = RedisStorage(
            Redis(
                host='localhost',
                db=1
            )
        )
    else:
        storage = MemoryStorage()

    dp = Dispatcher(storage=storage, config=config, database=database)

    admin.reg_routers(dp)
    user.reg_routers(dp)
    group.reg_routers(dp)

    dp.update.middleware(DatabaseInstance())
    dp.message.middleware(ThrottlingMiddleware(throttle_time=config.bot.throttling_time))
    if config.bot.logging:
        dp.update.middleware(LoggingMiddleware())
    dp.callback_query.middleware(CallbackAnswerMiddleware())

    startup = partial(on_startup, database=database)
    dp.startup.register(startup)

    if config.bot.polling:
        asyncio.run(start_polling(dp, bot))
    else:
        app = web.Application()
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=config.bot.MAIN_BOT_PATH)
        setup_application(app, dp, bot=bot)

        logger.success('WEBHOOK STARTED')
        web.run_app(app, host=config.bot.WEB_SERVER_HOST, port=config.bot.WEB_SERVER_PORT)


async def start_polling(dp: Dispatcher, bot: Bot):
    if config.bot.skip_updates:
        await bot.delete_webhook(drop_pending_updates=True)
    else:
        await bot.delete_webhook()
    try:
        updates = dp.resolve_used_update_types()
        logger.opt(colors=True).info('Allowed updates: <fg #00ccff>[%s]</>' % ', '.join(updates))
        logger.success('POLLING STARTED')
        await dp.start_polling(bot, allowed_updates=updates)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    main()
