from aiogram import types, Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.texts import total as text
from bot.database import User

router = Router(name='start_command')


@router.message(CommandStart())
async def start_command(message: types.Message, command: CommandObject, state: FSMContext, session: AsyncSession):
    await state.clear()
    if command.args:
        await User.process_user(session, message.from_user, ref=command.args)
    else:
        await User.process_user(session, message.from_user)
    await message.answer(
        text.start_message,
    )
    await session.commit()
