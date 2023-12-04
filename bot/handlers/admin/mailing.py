import datetime
import random

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import Mailing, Settings, User
from bot.keyboards.admin.factory import MailingCallback
from bot.states import MailingState
from bot.texts.admin import mailing as text
from bot.keyboards.admin import inline, reply
from bot.utils import funcs, mailing as mailing_util


router = Router(name='mailing')


@router.message(F.text == 'Рассылка ✉️')
async def main_mailing_menu(
        message: types.Message,
        state: FSMContext,
        session: AsyncSession,
        config,
        edit: bool = False
):
    mailing: Mailing = (await session.execute(select(Mailing))).scalar()
    settings: Settings = (await session.execute(select(Settings))).scalar()

    count = settings.count if settings else 0
    order = settings.order if settings else 1

    users_count = (await session.execute(select(func.count()).select_from(User).where(User.status == 1))).scalar()
    users_count = count if count and users_count > count else users_count

    mailing_speed = config.bot.mailing_speed
    status_text = ""
    if mailing:
        time_start = mailing.start
        m_count = mailing.mailing_count if mailing.mailing_count else 1
        m_limit = mailing.mailing_limit

        time_now = datetime.datetime.now().timestamp()
        elapsed_time = time_now - time_start
        send_rate = m_count / elapsed_time
        remaining_elements = m_limit - m_count
        remaining_time_seconds = (-send_rate + (
                send_rate ** 2 + 2 * 0.02 * remaining_elements) ** 0.5) / 0.02

        end = funcs.sec_to_time(round(remaining_time_seconds), maximum='hours')

        status_text = text.status.format(
            m_count, m_limit,
            round(m_count / m_limit * 100, 2) if m_limit else 0,

            f'{end["days"]}д. {end["hours"]}ч. {end["minutes"]}м. {end["seconds"]}с.',
        )
        mailing_speed = mailing.speed
    mailing_text = text.settings.format(
        'Все' if count == 0 else funcs.splitting(count),
        {0: 'Рандом', 1: 'С начала', 2: 'С конца'}[order],
        mailing_speed,
        f'<b><i>{funcs.splitting(users_count)}</i></b> человек',
        status_text,
    )

    keyboard = inline.mailing_menu(settings, mailing)
    method = message.edit_text if edit else message.answer
    await method(mailing_text, reply_markup=keyboard)
    await state.clear()


@router.callback_query(MailingCallback.filter())
async def mailing_callback_commands(
        call: types.CallbackQuery,
        callback_data: MailingCallback,
        state: FSMContext,
        session: AsyncSession,
        config
):
    data = callback_data
    if data.action == 'main':
        return await main_mailing_menu(call.message, state, session, config, edit=True)
    elif data.action == 'main_menu':
        await call.message.delete()
        await call.message.answer(
            text.back_to_admin_menu,
            reply_markup=reply.main_admin()
        )
    elif data.action == 'refresh':
        try:
            return await main_mailing_menu(call.message, state, session, config, edit=True)
        except:
            pass
    elif data.action == 'post':
        message_id = (await call.message.edit_text(
            text.send_your_post,
            reply_markup=inline.choice(
                'mailing',
                general_buttons=[{'text': 'Назад 🔙', 'callback_data': 'mailing:main'}]
            )
        )).message_id
        await state.update_data(message_id=message_id)
        await state.set_state(MailingState.get_post)

    elif data.action == 'preview':
        settings: Settings = (await session.execute(select(Settings))).scalar()
        if settings is None or settings.message_id is None:
            return await call.message.answer(text.post_dont_exist)
        try:
            await call.bot.copy_message(
                call.from_user.id,
                settings.chat_id,
                settings.message_id,
                reply_markup=settings.keyboard
            )
        except Exception as err:
            await call.message.edit_text(text.error.format(funcs.escape(str(err))))
    elif data.action == 'count':
        message_id = (await call.message.edit_text(
            text.send_count_people,
            reply_markup=inline.choice(
                'mailing',
                [{'text': 'Все пользователи', 'callback_data': 'all_users'}],
                [{'text': 'Назад 🔙', 'callback_data': 'mailing:main'}]
            )
        )).message_id
        await state.update_data(message_id=message_id)
        await state.set_state(MailingState.get_count)
    elif data.action == 'order':
        message_id = (await call.message.edit_text(
            text.choice_order,
            reply_markup=inline.choice(
                'mailing',
                [{'text': 'С начала', 'callback_data': 'order:start'},
                 {'text': 'Рандом', 'callback_data': 'order:random'},
                 {'text': 'С конца', 'callback_data': 'order:end'}],
                [{'text': 'Назад 🔙', 'callback_data': 'mailing:main'}]
            )
        )).message_id
        await state.update_data(message_id=message_id)
        await state.set_state(MailingState.get_order)
    elif data.action == 'start_mailing':
        mailing = (await session.execute(select(Mailing))).scalar()
        if mailing:
            return await call.message.answer(text.ongoing)
        await call.message.edit_text(
            text.confirm,
            reply_markup=inline.choice(
                'mailing',
                [{'text': '✅ ЗAПУСТИТЬ ✅', 'callback_data': 'mailing:start'}],
                [{'text': 'Назад 🔙', 'callback_data': 'mailing:main'}]
            )
        )
    elif data.action == 'start':
        mailing = (await session.execute(select(Mailing))).scalar()
        if mailing:
            return await call.message.answer(text.ongoing)
        settings: Settings = (await session.execute(select(Settings))).scalar()
        if settings is None:
            await call.message.edit_text(text.post_dont_exist)
            return await main_mailing_menu(call.message, state, session, config)
        limit = None if settings.count == 0 else settings.count
        if settings.order == 1:
            users = (await session.execute(select(User.user_id).where(User.status == 1).limit(limit))).scalars().all()
        else:
            users = (await session.execute(
                select(User.user_id).where(User.status == 1).order_by(User.id.desc()).limit(limit))
                     ).scalars().all()
        if settings.order == 0:
            random.shuffle(users)

        if not users or settings.chat_id is None:
            return await call.message.answer(text.false)

        await call.message.delete()
        await call.message.answer(text.mailing_is_started, reply_markup=reply.main_admin())
        await mailing_util.start(
            session,
            settings,
            call.bot,
            call.from_user.id,
            users,
            config.bot.mailing_speed,
        )
    elif data.action == 'stop_mailing':
        mailing = (await session.execute(select(Mailing))).scalar()
        if not mailing:
            return await main_mailing_menu(call.message, state, session, config, edit=True)
        await call.message.edit_text(text.stop)
        await mailing_util.stop(session)
    await call.answer()


@router.message(MailingState.get_post)
async def get_mailing_post(message: types.Message, state: FSMContext, session: AsyncSession, config):
    message_id = (await state.get_data()).get('message_id')
    await message.bot.delete_message(
        message.from_user.id,
        message_id
    )
    settings: Settings = (await session.execute(select(Settings))).scalar()
    buttons = [] if message.reply_markup else None

    if buttons is not None:
        for row in message.reply_markup.inline_keyboard:
            rows = []
            for button in row:
                rows.append(
                    {'text': button.text,
                     'url': button.url}
                )
            buttons.append(rows)
    keyboard = {'inline_keyboard': buttons}
    if settings is None:
        await session.merge(Settings(
            chat_id=message.from_user.id,
            message_id=message.message_id,
            keyboard=keyboard,
            order=1,
            count=0
        ))
    else:
        await session.execute(update(Settings).where(Settings.id == settings.id).values(
            chat_id=message.from_user.id, message_id=message.message_id,
            keyboard=keyboard)
        )
    await session.commit()
    return await main_mailing_menu(message, state, session, config)


@router.callback_query(F.data == 'all_users', MailingState.get_count)
async def get_count_call(call: types.CallbackQuery, state: FSMContext, session: AsyncSession, config):
    settings: Settings = (await session.execute(select(Settings))).scalar()
    if settings is None:
        await session.merge(Settings(order=1, count=0))
    else:
        await session.execute(update(Settings).where(Settings.id == settings.id).values(count=0))
    await session.commit()
    return await main_mailing_menu(call.message, state, session, config, edit=True)


@router.message(MailingState.get_count)
async def get_count_message(message: types.Message, state: FSMContext, session: AsyncSession, config):
    count = message.text
    if count.isdigit():
        count = int(count)
        if count < 0:
            raise ValueError
        message_id = (await state.get_data()).get('message_id')
        await message.bot.delete_message(
            message.from_user.id,
            message_id
        )
        await message.delete()
        settings: Settings = (await session.execute(select(Settings))).scalar()
        if settings is None:
            await session.merge(Settings(order=1, count=count))
        else:
            await session.execute(update(Settings).where(Settings.id == settings.id).values(count=count))
        await session.commit()
        return await main_mailing_menu(message, state, session, config)
    else:
        await message.answer('Введите число!')


@router.callback_query(F.data.startswith('order'), MailingState.get_order)
async def get_order(call: types.CallbackQuery, state: FSMContext, session: AsyncSession, config):
    order = {'random': 0, 'start': 1, 'end': 2}[call.data.split(':')[1]]
    settings: Settings = (await session.execute(select(Settings))).scalar()
    if settings is None:
        await session.merge(Settings(order=order, count=0))
    else:
        await session.execute(update(Settings).where(Settings.id == settings.id).values(order=order))
    await session.commit()
    return await main_mailing_menu(call.message, state, session, config, edit=True)
