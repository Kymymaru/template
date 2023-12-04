from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin.factory import PaginationCallback

from .subscription import main as subscription
from .shows import main as shows
from .referral import refs_list


router = Router(name='pagination')


@router.callback_query(PaginationCallback.filter())
async def pagination_handler(call: types.CallbackQuery, callback_data: PaginationCallback,
                             state: FSMContext, session: AsyncSession, config):
    data = callback_data
    if data.into == 'ref':
        await refs_list(call.message, state, session, data.page, True)
    if data.into == 'subscriptions':
        await subscription(call.message, state, session, int(data.page), True)
    elif data.into == 'shows':
        await shows(call.message, state, session, int(data.page), True)
