from aiogram import Dispatcher
from loguru import logger

from . import (
    start,
    subscription,
    blocks,
)

from bot.middlewares import SubscriptionMiddleware


def reg_routers(dp: Dispatcher):
    handlers = [
        start,
        subscription,
        blocks,
    ]
    for handler in handlers:
        handler.router.message.middleware(SubscriptionMiddleware())
        handler.router.callback_query.middleware(SubscriptionMiddleware())

        dp.include_router(handler.router)
    logger.opt(colors=True).info(
        '<fg #00ff99>[%s]</> user handlers imported' % ', '.join([handler.router.name for handler in handlers])
    )
