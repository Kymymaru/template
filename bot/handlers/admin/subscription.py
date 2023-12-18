from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin.factory import SubscriptionCallback
from bot.states import SubscriptionsState
from bot.database import Subscription, User
from bot.texts.admin import subscription as text
from bot.keyboards.admin import inline, reply

router = Router(name='subscription')


@router.message(F.text == 'Обяз. Подписка 🔐')
async def main(message: types.Message, state: FSMContext, session: AsyncSession, page: int = 1, edit: bool = False):
    subscriptions = (await session.execute(select(Subscription))).scalars().all()
    keyboard = inline.subscriptions_markup(subscriptions, page)
    method = message.edit_text if edit else message.answer
    await method(
        text=text.main,
        reply_markup=keyboard
    )
    await state.clear()


@router.callback_query(SubscriptionCallback.filter())
async def subscriptions_callbacks(call: types.CallbackQuery, callback_data: SubscriptionCallback,
                                  state: FSMContext, session: AsyncSession):
    data = callback_data
    if data.action == 'page':
        return await main(call.message, state, session, page=data.page, edit=True)
    if data.action == 'add':
        await state.set_state(SubscriptionsState.get_message)
        message_id = (await call.message.edit_text(
            text.get_message,
            reply_markup=inline.cancel
        )).message_id
        await state.update_data(message_id=message_id)
    elif data.action == 'info':
        await go_to_subscription(call, data, session)
    elif data.action == 'small_info':
        subscription = (await session.get(Subscription, data.id))
        await call.answer(
            text.small_info.format(
                subscription.chat_id,
                subscription.title,
                subscription.link
            ),
            show_alert=True
        )
    elif 'status' in data.action:
        data.status = int(not data.status)
        info = f'Канал/Бот {data.numerate_id} исключён из списка обяз. подписки ❎'
        if bool(data.status):
            info = f'Канал/Бот {data.numerate_id} добавлен в список обяз. подписки ✅'
        await session.execute(update(Subscription).where(Subscription.id == data.id).values(status=data.status))
        await call.answer(info)
        if '_' in data.action:
            return await go_to_subscription(call, data, session)
        await main(call.message, state, session, page=data.page, edit=True)
    elif data.action == 'del':
        await call.message.edit_text(
            text.confirm_delete.format(data.numerate_id),
            reply_markup=inline.confirm_deleting(data)
        )
    elif data.action == 'delete':
        await session.execute(delete(Subscription).where(Subscription.id == data.id))
        await call.answer(text.delete.format(data.numerate_id))
        await main(call.message, state, session, page=data.page, edit=True)


@router.callback_query(F.data == 'cancel', SubscriptionsState.get_message)
@router.callback_query(F.data == 'cancel', SubscriptionsState.get_link)
async def canceling_on_get_post_state(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await main(call.message, state, session, edit=True)


@router.message(SubscriptionsState.get_message)
async def get_post_state(message: types.Message, state: FSMContext):
    message_id = (await state.get_data()).get('message_id')
    await message.bot.delete_message(
        message.from_user.id,
        message_id=message_id
    )
    await message.delete()
    if message.forward_from:
        chat_id = message.forward_from.id
        if not message.forward_from.is_bot:
            message_id = (await message.answer('Пересланное сообщение не от бота!',
                                               reply_markup=inline.cancel)).message_id
            return await state.update_data(message_id=message_id)
        is_bot = 1
        title = message.forward_from.first_name
    elif message.forward_from_chat:
        chat_id = message.forward_from_chat.id
        is_bot = 0
        title = message.forward_from_chat.title
    else:
        message_id = (await message.answer(text.get_message,
                                           reply_markup=inline.cancel)).message_id
        return await state.update_data(message_id=message_id)

    await state.set_data({
        'chat_id': chat_id,
        'is_bot': is_bot,
        'title': title
    })
    await state.set_state(SubscriptionsState.get_link)
    message_id = (await message.answer(
        text.get_link,
        reply_markup=inline.cancel
    )).message_id
    await state.update_data(message_id=message_id)


@router.message(SubscriptionsState.get_link)
async def get_sent_count_state(message: types.Message, state: FSMContext, session: AsyncSession):
    message_id = (await state.get_data()).get('message_id')
    await message.bot.delete_message(
        message.from_user.id,
        message_id=message_id
    )
    await message.delete()
    link = message.text
    if 't.me' in link:
        data = await state.get_data()
        await session.merge(Subscription(
            chat_id=data['chat_id'],
            title=data['title'],
            is_bot=data['is_bot'],
            link=link,
        ))
        await message.answer(text.success_add, reply_markup=reply.main_admin())
        await main(message, state, session)
    else:
        message_id = (await message.answer(text.get_link,
                                           reply_markup=inline.cancel)).message_id
        await state.update_data(message_id=message_id)


async def go_to_subscription(call: types.CallbackQuery, data: SubscriptionCallback,
                             session: AsyncSession):
    subscription = (await session.get(Subscription, data.id))
    total_count = (
        await session.execute(select(func.count()).select_from(User).where(User.user_id.in_(subscription.users)))
    ).scalar()
    live_count = (
        await session.execute(
            select(func.count()).select_from(User).where(User.user_id.in_(subscription.users), User.status == 1))
    ).scalar()

    await call.message.edit_text(
        text.info.format(
            subscription.chat_id,
            subscription.title,
            subscription.link,
            total_count,
            live_count
        ),
        reply_markup=inline.subscription_keyboard(subscription, data)
    )
