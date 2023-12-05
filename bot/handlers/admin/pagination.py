from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin.factory import PaginationCallback
from bot.database import Category
from bot.keyboards.admin import inline

from .subscription import main as subscription
from .shows import main as shows
from .referral import refs_list
from .categories import categories_list, subcategories_list

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
    elif data.into == 'categories_for_subcategory_creating':
        categories = (await session.execute(
            select(Category)
        )).scalars().all()
        await call.message.edit_reply_markup(
            reply_markup=inline.choose_categories_for_create_subcategory(categories, page=callback_data.page)
        )
    elif data.into == 'admin_categories_list':
        await categories_list(call.message, session, callback_data.page, edit=True)
    elif data.into == 'admin_subcategories_list':
        await subcategories_list(call.message, session, callback_data.page, edit=True)
