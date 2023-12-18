import datetime

from aiogram import types, Router, F
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import User

router = Router(name='blocks')


@router.my_chat_member(F.chat.type == 'private')
async def blocks(event: types.ChatMemberUpdated, session: AsyncSession):
    if event.new_chat_member.status in ('left', 'kicked'):
        await session.execute(
            update(User).where(User.user_id == event.from_user.id).values(
                status=0, death_date=datetime.datetime.now()
            )
        )
