import datetime

from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import User, Bill
from bot.keyboards.user import inline
from bot.keyboards.user.factory import PaymentsCallback
from bot.utils.ru_kassa import payment

router = Router(name='payments')


@router.callback_query(PaymentsCallback.filter())
async def payments_callback(call: types.CallbackQuery, callback_data: PaymentsCallback,
                            state: FSMContext,
                            session: AsyncSession,
                            user: User):
    await state.clear()
    data = callback_data
    if data.action == 'create_payment':
        bill = await payment.create_bill(
            data.amount,
            data.bill_id,
        )
        await call.message.answer(
            'Оплатите сумму по кнопке ниже',
            reply_markup=inline.check_payment(bill)
        )
    elif data.action == 'check_payment':
        paid = await payment.check_payment(payment_id=data.bill_id)
        if paid is True:
            # await session.merge(
            #     Bill(
            #         bill_id=data.bill_id,
            #         amount=data.amount,
            #
            #         user_id=call.from_user.id,
            #         ref=user.ref,
            #         bill_date=datetime.date.today()
            #     )
            # )
            await session.execute(update(User).where(User.user_id == user.user_id).values(is_vip=1999999999))
            await session.commit()
            await call.message.edit_text(
                'Оплата получена, теперь вы можете видеть имена пользователей!'
            )
        elif paid is False:
            await call.answer(
                'Оплата еще не получена!'
            )
        else:
            await call.answer(
                paid
            )


