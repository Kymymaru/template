from typing import List

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import User, Chat, Subscription

from bot.texts import total as text
from bot.utils import funcs, statistic

router = Router(name='stats')


@router.message(F.text == 'Статистика 📊')
async def stats_markup(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    times = funcs.get_times()

    total_users = await funcs.get_count(
        session,
        User,
    )

    active_users = await funcs.get_count(
        session,
        User,
        User.status == 1
    )

    subscriptions: List[Subscription] = (await session.execute(select(Subscription))).scalars().all()

    subbed = sum(len(i.users) for i in subscriptions)
    self = await funcs.get_count(
        session,
        User,
        User.ref.is_(None)
    )

    timed_stats_user = [
        await funcs.get_count(
            session,
            User,
            User.reg_date >= time[0],
            User.reg_date < time[1]
        )
        for time in times
    ]
    langs = ''
    result = (await session.execute(
        select(User.lang_code).group_by(User.lang_code).order_by(func.count().desc()).limit(4))
              ).scalars().all()
    for i, item in enumerate(result, start=1):
        count = await funcs.get_count(
            session,
            User,
            User.lang_code == item
        )
        langs += f'{i}. {item.upper()}    ' \
                 f'<code>{count}</code>    ' \
                 f'<code>({funcs.get_percent(total_users, count)}%)</code>\n'

    other_count = await funcs.get_count(
        session,
        User,
        User.lang_code.notin_(result)
    )
    langs += f'{i + 1}. Остальные    ' \
             f'<code>{other_count}</code>    ' \
             f'<code>({funcs.get_percent(total_users, other_count)}%)</code>\n'

    total_chats = await funcs.get_count(
        session,
        Chat,
        Chat.id.isnot(None)
    )

    active_chats = await funcs.get_count(
        session,
        Chat,
        Chat.status == 1
    )
    timed_stats_chat = [
        await funcs.get_count(
            session,
            Chat,
            Chat.reg_date >= time[0],
            Chat.reg_date < time[1]
        )
        for time in times
    ]

    data = [
        total_users,
        self, funcs.get_percent(total_users, self),
        active_users, funcs.get_percent(total_users, active_users),
        (total_users - active_users), funcs.get_percent(total_users, (total_users - active_users)),
        subbed, funcs.get_percent(total_users, subbed),

        *timed_stats_user,

        langs,

        total_chats,
        active_chats, funcs.get_percent(total_chats, active_chats),
        (total_chats - active_chats), funcs.get_percent(total_chats, (total_chats - active_chats)),

        *timed_stats_chat
    ]
    msg = await message.answer_animation(
        'https://media.tenor.com/kOosNeYUmWkAAAAC/loading-buffering.gif',
        caption=text.audit_statistic.format(*data)
    )

    image = await statistic.audit_stat(session)

    await msg.edit_media(
        media=types.InputMediaPhoto(
            media=types.FSInputFile(image),
            caption=text.audit_statistic.format(*data)
        )
    )


@router.message(F.text == 'Прибыль 💰')
async def profit_markup(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    times = funcs.get_times()
    data = [
        (await funcs.get_money(date, session))
        for date in times
    ]
    msg = await message.answer_animation(
        'https://media.tenor.com/kOosNeYUmWkAAAAC/loading-buffering.gif',
        caption=text.payment_statistic.format(*data)
    )
    image = await statistic.payment_stat(session)
    await msg.edit_media(
        media=types.InputMediaPhoto(
            media=types.FSInputFile(image),
            caption=text.payment_statistic.format(*data)
        )
    )
