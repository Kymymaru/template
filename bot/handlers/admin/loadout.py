import asyncio

import aiofiles
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import User, Chat
from bot.keyboards.admin.factory import LoadoutCallback
from bot.states import LoadoutState
from bot.texts.admin import loadout as text
from bot.keyboards.admin import inline

router = Router(name='loadout')


@router.message(F.text == 'Выгрузка 🗳')
async def loadout(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text.main,
        reply_markup=inline.loadout()
    )


@router.callback_query(LoadoutCallback.filter())
async def loadout_call(call: types.CallbackQuery, callback_data: LoadoutCallback, state: FSMContext,
                       session: AsyncSession):
    data = callback_data
    await call.message.delete()
    if data.count == 'all':
        if data.type == 'users':
            statement = select(User.user_id).where(User.status == 1)
        else:
            statement = select(Chat.chat_id).where(Chat.status == 1)
        message = await call.message.answer(text.request_processing)
        await asyncio.create_task(do_loadout(message=message, session=session, statement=statement))
    elif data.count == 'last':
        await state.update_data(type=data.type)
        await call.message.answer(text.get_count)
        await state.set_state(LoadoutState.get_count)
    elif data.count == 'file':
        msg = await call.message.answer(text.loading)
        await call.message.answer_document(
            document=types.FSInputFile('ids.txt'),
            caption=text.last_loadout_file
        )
        await msg.delete()


@router.message(LoadoutState.get_count)
async def loadout_state(message: types.Message, state: FSMContext, session: AsyncSession):
    count = message.text
    if count.isdigit():
        count = int(count)
        if count <= 0:
            return await message.answer(text.type_a_integer)
        data = await state.get_data()
        if data['type'] == 'users':
            statement = select(User.user_id).where(User.status == 1).order_by(User.id.desc()).limit(count)
        else:
            statement = select(Chat.chat_id).where(Chat.status == 1).order_by(Chat.id.desc()).limit(count)
        message = await message.answer(text.request_processing)
        await asyncio.create_task(do_loadout(message=message, session=session, statement=statement))
    else:
        await message.answer(text.type_a_integer)


async def do_loadout(message: types.Message, session: AsyncSession, statement):
    request = await session.execute(statement)
    user_ids = request.scalars().all()
    async with aiofiles.open('ids.txt', 'w') as f:
        for user_id in user_ids:
            await f.write(f'{user_id}\n')
    await message.delete()
    await message.answer_document(
        document=types.FSInputFile('ids.txt'),
        caption=text.request.format(len(user_ids))
    )
