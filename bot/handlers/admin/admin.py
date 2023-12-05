from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import reply
from bot.texts import total as text
from bot.database import User

router = Router(name='admin_command')


@router.message(F.text == 'Вернутся в админ панель 🔙')
@router.message(Command('admin'))
async def admin_command(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    await User.process_user(session, message.from_user)
    await message.answer(
        text=text.admin_command,
        reply_markup=reply.main_admin()
    )
    await session.commit()