from aiogram import Dispatcher
from loguru import logger

from . import (
    admin,
    loadout,
    mailing,
    pagination,
    referral,
    shows,
    statistic,
    subscription,
    get_logs
)
from bot.filters.admin import AdminFilter


def reg_routers(dp: Dispatcher):
    handlers = [
        admin,
        loadout,
        mailing,
        pagination,
        referral,
        shows,
        statistic,
        subscription,
        get_logs
    ]
    for handler in handlers:
        handler.router.message.filter(AdminFilter())

        dp.include_router(handler.router)
    logger.opt(colors=True).info(
        '<fg #6600ff>[%s]</> admin handlers imported' % ', '.join([handler.router.name for handler in handlers])
    )
