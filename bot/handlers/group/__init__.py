from aiogram import Dispatcher
from loguru import logger
from aiogram.enums import ChatType
from bot.filters.chat_type import ChatTypeFilter

from . import (
    member,
)


def reg_routers(dp: Dispatcher):
    handlers = [
        member,
    ]
    for handler in handlers:
        handler.router.message.filter(ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]))
        dp.include_router(handler.router)
    logger.opt(colors=True).info(
        '<fg #00ff99>[%s]</> group handlers imported' % ', '.join([handler.router.name for handler in handlers])
    )
