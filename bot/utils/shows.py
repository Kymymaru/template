import random
from typing import Union

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from sqlalchemy import select, update as upd
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import Show
from bot.keyboards.admin.factory import ShowsCallback
from bot.utils import funcs


async def send_show(session: AsyncSession, event: Union[types.Message, types.CallbackQuery],
                    username: str,
                    show: Union[Show, None] = None,
                    check: bool = True):
    if show is None:
        shows: Show = (await session.execute(select(Show))).scalars().all()
        if len(shows) <= 0:
            return
        show = random.choice([show for show in shows if show.status == 1])
        if show is None:
            return

    if check:
        if event.from_user.id in show.users:
            return
    keyboard = show.keyboard
    event = event if isinstance(event, types.Message) else event.message
    if show.file_type == 'text':
        if check:
            show.users.append(event.from_user.id)
            await session.execute(upd(Show).where(Show.id == show.id).values(sent=show.sent + 1, users=show.users))
            await session.commit()
        return await event.answer(
            text=funcs.format_text(event.from_user, show.text, username),
            reply_markup=show.keyboard
        )
    if show.file_type == 'photo':
        method = event.answer_photo
    elif show.file_type == 'video':
        method = event.answer_video
    elif show.file_type == 'voice':
        method = event.answer_voice
    elif show.file_type == 'animation':
        method = event.answer_animation
    elif show.file_type == 'video_note':
        method = event.answer_video_note
    else:
        method = event.answer_document
    try:
        if not check:
            if keyboard is not None:
                keyboard['inline_keyboard'].append(
                    [
                        {
                            'text': 'Закрыть ❌',
                            'callback_data': ShowsCallback(
                                action='close',
                                id=1,
                                numerate_id='1',
                                page='1',
                                status='1'
                            ).pack()
                        }
                    ]
                )
            else:
                keyboard = InlineKeyboardBuilder().button(
                    text='Закрыть ❌',
                    callback_data=ShowsCallback(
                        action='close',
                        id=1,
                        numerate_id='1',
                        page='1',
                        status='1'
                    ).pack()
                ).as_markup()
        await method(
            show.file_id,
            caption=funcs.format_text(event.from_user, show.text, username),
            reply_markup=keyboard
        )
        if check:
            show.users.append(event.from_user.id)
            await session.execute(upd(Show).where(Show.id == show.id).values(sent=show.sent + 1, users=show.users))
            await session.commit()
    except Exception as err:
        logger.error(err)
