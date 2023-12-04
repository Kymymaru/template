from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.keyboards.admin import reply
from bot.texts import total as text

router = Router(name='admin_command')


@router.message(F.text == 'Вернутся в админ панель 🔙')
@router.message(Command('admin'))
async def admin_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text=text.admin_command,
        reply_markup=reply.main_admin()
    )
