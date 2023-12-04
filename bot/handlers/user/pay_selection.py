from contextlib import suppress

from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import User
from bot.keyboards.user import inline
from bot.keyboards.user.factory import PaymentsCallback
from bot.utils.pay_selection import payment, PaySelectionError

router = Router(name='payments')


@router.callback_query(PaymentsCallback.filter())
async def payments_callback(call: types.CallbackQuery, callback_data: PaymentsCallback,
                            state: FSMContext):
    await state.clear()
    data = callback_data
    if data.action == 'create_payment':
        url = await payment.get_link(
            int(data.days),
            data.amount,
            call.from_user.id,
        )
        await call.message.answer(
            'Оплатите сумму по кнопке ниже',
            reply_markup=inline.check_payment_pay_selection(url)
        )


@router.message(Command('unsub'))
async def unsub(message: types.Message):
    await message.answer(
        'Вы хотите отменить продление подписки?',
        reply_markup={'inline_keyboard': [
            [
                {'text': 'Да', 'callback_data': 'unsub:yes'},
                {'text': 'Нет', 'callback_data': 'unsub:no'},
            ],
        ]},
    )


@router.callback_query(F.data.startswith('unsub'))
async def unsub_callback(call: types.CallbackQuery, session: AsyncSession):
    user = await session.get(User, call.from_user.id)

    with suppress(PaySelectionError):
        await payment.cancel_subs(call.from_user.id, user.re_bill_id)

    user.re_bill_id = None
    await session.commit()

    await call.message.edit_text('Готово ✅')
