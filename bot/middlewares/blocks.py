import datetime
from typing import Callable, Awaitable, Any, Dict

from sqlalchemy import update
from aiogram import BaseMiddleware, types
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import User


class BlocksMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: types.ChatMemberUpdated,
            data: Dict[str, Any]
    ) -> Any:
        time = datetime.datetime.now()

        session: AsyncSession = data['session']
        if event.chat.type == 'private':
            user_id = event.from_user.id
            if event.new_chat_member.status in ('left', 'kicked'):
                status = 0
            else:
                status = 1
            await session.execute(
                update(User).where(User.user_id == user_id).values(status=status, death_date=time)
            )
            await session.commit()
        return handler(event, data)

