from typing import Any, Awaitable, Dict, Callable, Union

from aiogram import BaseMiddleware
from aiogram.types import Update

from bot.database import Database


class DatabaseInstance(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Union[Update, Any],
            data: Dict[str, Any]
    ) -> Any:
        database: Database = data['database']
        async with database.get_session() as session:
            async with session.begin():
                data['session'] = session
                await handler(event, data)
