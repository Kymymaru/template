import datetime

from aiogram import types, Router, F, Bot
from aiogram.enums import ChatMemberStatus
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import Chat, Database
from bot.texts.group import member as text

router = Router(name='member')


@router.message(F.left_chat_member)
async def on_user_leave(message: types.Message, session: AsyncSession):
    if message.left_chat_member.id == message.bot.id:
        await session.execute(
            update(Chat).where(Chat.chat_id == message.chat.id).values(status=0, death_date=datetime.date.today())
        )


@router.message(F.new_chat_members)
async def on_user_join(message: types.Message, bot: Bot, database: Database, session: AsyncSession):
    for member in message.new_chat_members:
        if member.id == bot.id:
            member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=bot.id
            )
            if member.status == ChatMemberStatus.ADMINISTRATOR:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=text.success
                )
                await database.chat.process_chat(session, message.chat, has_admin_rights=1)
            else:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=text.i_need_permissions
                )
                await database.chat.process_chat(session, message.chat, has_admin_rights=0)
