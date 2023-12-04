from aiogram import types, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.texts import total as text

router = Router(name='start_command')


@router.message(F.text == 'Главное меню 🔙')
@router.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    await message.answer(
        text.start_message,
    )
    await state.clear()
