from aiogram import types, Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.texts import total as text
from bot.database import Database

router = Router(name='start_command')


@router.message(CommandStart())
async def start_command(message: types.Message, command: CommandObject, state: FSMContext, session: AsyncSession,
                        database: Database):
    await state.clear()
    if command.args:
        await database.user.process_user(session, message.from_user, ref=command.args)
    else:
        await database.user.process_user(session, message.from_user)
    await message.answer(
        text.start_message,
    )
