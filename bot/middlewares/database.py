from typing import Any, Awaitable, Dict, Callable, Union

from aiogram import BaseMiddleware
from aiogram.types import Update
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


class DatabaseInstance(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Union[Update, Any],
            data: Dict[str, Any]
    ) -> Any:
        session: AsyncSession = self.session_pool()
        data['session'] = session
        await handler(event, data)
        if session.is_active:
            await session.close()
