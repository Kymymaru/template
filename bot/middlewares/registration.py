import datetime
from typing import Callable, Awaitable, Any, Dict, Union

import sqlalchemy.exc
from aiogram import BaseMiddleware, types, html
from aiogram.types import Update

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database import User, Chat

from loguru import logger


# def is_user_link(text: str) -> bool:
#     digit_count = 0
#     for char in text:
#         if char.isdigit():
#             digit_count += 1
#             if digit_count > 5:
#                 return True
#     return False


async def process_user(chat_type, from_user, ref, session: AsyncSession):
    request = await session.execute(
        select(User).where(User.user_id == from_user.id)
    )
    user: User = request.scalar()
    if user is None and chat_type == 'private':
        user = User(
            user_id=from_user.id,
            ref=ref,
            name=html.quote(from_user.first_name),
            username=from_user.username,
            lang_code=from_user.language_code if from_user.language_code is not None else 'ru',
            status=1,
            reg_date=datetime.date.today(),
            death_date=None,
            last_activity=datetime.datetime.now(),
        )
        await session.merge(
            user
        )
        logger.info('New User: {}{}'.format(user.user_id, f'\tFrom Ref: {user.ref}' if user.ref is not None else ''))
    else:
        if chat_type == 'private':
            user.name = html.quote(from_user.first_name)
            user.status = 1
            user.last_activity = datetime.datetime.now()
    try:
        await session.commit()
    except sqlalchemy.exc.IntegrityError:
        pass
    return user


async def process_chat(from_chat, ref, status, session: AsyncSession):
    request = await session.execute(
        select(Chat).where(Chat.chat_id == from_chat.id)
    )
    chat: Chat = request.scalar()
    if chat is None:
        chat = Chat(
            chat_id=from_chat.id,
            title=html.quote(from_chat.title),
            ref=ref,
            status=status,
            reg_date=datetime.date.today(),
            death_date=None,
            data={}
        )
        await session.merge(chat)
        logger.info(f'New Chat: {chat.chat_id}')
    else:
        chat.title = html.quote(from_chat.title)
        chat.status = status
    try:
        await session.commit()
    except sqlalchemy.exc.IntegrityError:
        pass
    return chat


class RegistrationMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: types.Update,
            data: Dict[str, Any]
    ) -> Any:
        session: AsyncSession = data['session']
        from_chat = data['event_chat']
        chat_type = from_chat.type
        from_user = data['event_from_user']
        if event.event_type == 'message':
            if event.message.text is not None:
                text = event.message.text
                if ' ' in text and text.split()[0].startswith('/start'):
                    args = text.split()[1]
                else:
                    args = None
            else:
                args = None
        else:
            args = None
        ref = args if args is not None else None
        # ref = args if args is not None and not is_user_link(args) else None
        if chat_type in ['group', 'supergroup']:
            status = 0
            if isinstance(event, types.Message):
                status = 1
            chat = await process_chat(from_chat, ref, status, session)
            data['chat'] = chat
        user = await process_user(chat_type, from_user, ref, session)
        data['user'] = user
        await handler(event, data)
