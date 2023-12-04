from aiogram import types, Router, F

from bot.texts.user import subscription as text

router = Router(name='check_sub')


@router.callback_query(F.data == 'check_sub')
async def check_sub(call: types.CallbackQuery):
    await call.message.edit_text(
        text.subbed,
    )
