from typing import List, Union

from aiogram import types, Router, F, exceptions
from aiogram.filters import Command, StateFilter, CommandObject
from aiogram.fsm.context import FSMContext

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import User, Chat, Subscription, Ref
from bot.utils import statistic, funcs
from bot.texts.admin import referral as text
from bot.keyboards.admin.factory import ReferralCallback, PaginationCallback
from bot.keyboards.admin import inline, reply
from bot.states import RefState

router = Router(name='ref')


@router.message(StateFilter(RefState), F.text == 'Отмена ❌')
@router.message(F.text == 'Рефералы 💵')
async def ref_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text=text.menu,
        reply_markup=reply.ref_menu()
    )


@router.message(F.text == 'Создать рефку ➕')
async def create_ref(message: types.Message, state: FSMContext):
    await state.set_state(RefState.get_ref)
    await message.answer(
        text=text.type_name_ref,
        reply_markup=reply.cancel()
    )


@router.message(RefState.get_ref)
async def get_ref(message: types.Message, state: FSMContext, session: AsyncSession):
    await session.merge(
        Ref(
            ref=message.text
        )
    )
    await session.commit()
    await state.clear()
    await message.answer(
        text=text.create_ref_successful.format(ref=message.text),
        reply_markup=reply.ref_menu()
    )


@router.message(Command('price'))
async def set_price_command(message: types.Message, command: CommandObject, session: AsyncSession, config):
    if command.args:
        price = int(command.args.strip())
        if message.reply_to_message:
            if message.reply_to_message.reply_markup:
                data = message.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data.split(':')
                callback_data = ReferralCallback(
                    action='info',
                    type=data[2],
                    ref=data[3],
                    price=price,
                    page=int(data[5])
                )
                await session.execute(
                    update(Ref).where(Ref.ref == data[3]).values(
                        price=price
                    )
                )
                await session.commit()

                if callback_data.type == 'user':
                    data = await get_data(session, User, callback_data, config.bot.username)
                else:
                    data = await get_data(session, Chat, callback_data, config.bot.username)
                await message.reply_to_message.edit_text(
                    text.user_ref_stat.format(*data),
                    reply_markup=inline.ref_buttons(callback_data)
                )
                await message.delete()


@router.message(RefState.get_price)
async def get_price(message: types.Message, state: FSMContext, session: AsyncSession):
    price = message.text
    if price.isdigit():
        await session.execute(
            update(Ref).where(Ref.ref == (await state.get_data()).get('ref')).values(
                price=price
            )
        )
    else:
        await message.answer(
            text=text.type_digit
        )


@router.message(F.text == 'Список реф. ссылок 💵')
async def refs_list(message: types.Message, state: FSMContext, session: AsyncSession, page: int = 1,
                    edit: bool = False):
    await state.clear()
    refs = (await session.execute(
        select(Ref)
    )).scalars().all()
    method = message.edit_text if edit else message.answer
    try:
        if len(refs) == 0:
            await method(
                text=text.refs_dont_exist
            )
        else:
            await method(
                text=text.refs,
                reply_markup=inline.refs_markups(refs, page)
            )
    except exceptions.TelegramBadRequest:
        await message.delete()
        await message.answer(
            text=text.refs,
            reply_markup=inline.refs_markups(refs, page)
        )


@router.callback_query(ReferralCallback.filter())
async def refs_callbacks(call: types.CallbackQuery, state: FSMContext, callback_data: ReferralCallback,
                         session: AsyncSession, config):
    if callback_data.action == 'info':
        if callback_data.type == 'user':
            data = await get_data(session, User, callback_data, config.bot.username)
            try:
                await call.message.edit_text(
                    text.user_ref_stat.format(*data),
                    reply_markup=inline.ref_buttons(callback_data)
                )
            except exceptions.TelegramBadRequest:
                await call.message.delete()
                await call.message.answer(
                    text.user_ref_stat.format(*data),
                    reply_markup=inline.ref_buttons(callback_data)
                )

        elif callback_data.type == 'chat':
            data = await get_data(session, Chat, callback_data, config.bot.username)
            try:
                await call.message.edit_text(
                    text.chat_ref_stat.format(*data),
                    reply_markup=inline.ref_buttons(callback_data)
                )
            except exceptions.TelegramBadRequest:
                await call.message.delete()
                await call.message.answer(
                    text.chat_ref_stat.format(*data),
                    reply_markup=inline.ref_buttons(callback_data)
                )

    elif callback_data.action == 'change':
        callback_data.type = 'chat' if callback_data.type == 'user' else 'user'
        callback_data.action = 'info'
        await refs_callbacks(call, state, callback_data, session, config)
    elif callback_data.action == 'graph':
        image = await statistic.ref_stat(session, callback_data)
        back = True if len(call.message.reply_markup.inline_keyboard) == 3 else False
        await call.message.delete()
        await call.message.answer_photo(
            types.FSInputFile(image),
            caption=call.message.html_text,
            reply_markup=inline.ref_buttons(callback_data, back=back, graph=False)
        )

    elif callback_data.action == 'del':
        await call.message.edit_text(
            text.confirm_deleting.format(callback_data.ref),
            reply_markup=inline.confirm_deleting(callback_data, PaginationCallback(page=callback_data.page, into='ref'))
        )
    elif callback_data.action == 'delete':
        await session.execute(
            delete(Ref).where(Ref.ref == callback_data.ref)
        )
        await session.commit()
        await call.answer(text.successful_delete.format(callback_data.ref))
        await call.message.delete()
        await refs_list(call.message, state, session, callback_data.page)


@router.message(Command('ref'))
async def ref_cm_user(message: types.Message, state: FSMContext, session: AsyncSession, config):
    await state.clear()
    if len(message.text.split()) > 2:
        return await message.answer('Неправильное использование команды !')
    ref = (await session.execute(
        select(Ref).where(Ref.ref == message.text.split()[1])
    )).scalar()
    if ref is not None:
        callback_data = ReferralCallback(
            action='',
            type='user',
            ref=ref.ref,
            price=ref.price,
            page=0
        )
        data = await get_data(session, User, callback_data, config.bot.username)
        await message.answer(
            text.user_ref_stat.format(*data),
            reply_markup=inline.ref_buttons(callback_data, back=False)
        )
    else:
        return await message.answer(
            'Реф ссылка не найдена'
        )


async def get_data(session: AsyncSession, table: Union[User, Chat], callback: ReferralCallback, username: str):
    times = funcs.get_times()

    total = await funcs.get_count(session, table, table.ref == callback.ref)

    active = await funcs.get_count(session, table, table.ref == callback.ref, table.status == 1)

    data = [
        callback.ref,
        callback.price,
        total, get_price_count(callback.price, total),
        active, funcs.get_percent(total, active), get_price_count(callback.price, active)
    ]
    if table == User:
        subscriptions: List[Subscription] = (await session.execute(select(Subscription))).scalars().all()
        all_sub = []
        for i in subscriptions:
            all_sub = [*i.users, *all_sub]
        subbed = await funcs.get_count(session, table, table.ref == callback.ref, table.user_id.in_(all_sub))
        data.append(subbed)
        data.append(funcs.get_percent(total, subbed))

    for time in times:
        data.append(await funcs.get_count(session, table, table.ref == callback.ref, table.reg_date >= time[0],
                                          table.reg_date < time[1]))
    data.append(username)
    data.append(callback.ref)

    return data


def get_price_count(price, count):
    try:
        return round(price / count, 1)
    except ZeroDivisionError:
        return 0
