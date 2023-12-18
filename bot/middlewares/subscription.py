from typing import Callable, Awaitable, Any, Dict, Union, List
from aiogram import BaseMiddleware, types
from aiogram.types import Update
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import Subscription, User
from bot.texts.user import subscription as text
from bot.keyboards.user import inline


async def process(event, subscription: Subscription, session: AsyncSession):
    if not subscription.is_bot:
        try:
            user = await event.bot.get_chat_member(subscription.chat_id, event.bot.id)
            if user.status != 'administrator':
                return True
        except Exception as err:
            logger.error(err)
            return True
        try:
            user = await event.bot.get_chat_member(subscription.chat_id, event.from_user.id)
            if user.status not in ['left', None]:
                if event.from_user.id not in subscription.users:
                    subscription.users.append(event.from_user.id)
                    await session.execute(
                        update(Subscription).where(Subscription.id == subscription.id).values(users=subscription.users)
                    )
                return True
        except Exception as err:
            logger.error(err)
            return True
    else:
        if event.from_user.id not in subscription.users:
            subscription.users.append(event.from_user.id)
            await session.execute(
                update(Subscription).where(Subscription.id == subscription.id).values(users=subscription.users)
            )
        return True


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Union[types.Message, types.CallbackQuery],
            data: Dict[str, Any]
    ) -> Any:
        chat_type = event.chat.type if isinstance(event, types.Message) else event.message.chat.type
        session: AsyncSession = data['session']
        if chat_type == 'private':
            if isinstance(event, types.Message) and event.text is not None and event.text.startswith('/start'):
                if len(event.text.split()) == 2:
                    await User.process_user(session, event.from_user, 1, ref=event.text.split()[1])
            subscriptions: List[Subscription] = (await session.execute(
                select(Subscription).where(Subscription.status == 1))
                                                 ).scalars().all()
            dont_subbed = []
            bots = []
            for i in subscriptions:
                if i.is_bot:
                    bots.append(i)
                else:
                    if not await process(event, i, session):
                        dont_subbed.append(i)
            if len(dont_subbed) == 0:
                return await handler(event, data)
            else:
                data = [*dont_subbed, *bots]
                if isinstance(event, types.CallbackQuery):
                    if event.data == 'check_sub':
                        return await event.answer(text.dont_subbed, show_alert=True)
                    try:
                        await event.message.edit_text(
                            text.subscribe,
                            reply_markup=inline.buttons_for_sub(data)
                        )
                    except:
                        await event.message.delete()
                        await event.message.answer(
                            text.subscribe,
                            reply_markup=inline.buttons_for_sub(data)
                        )
                else:
                    await event.answer(
                        text.subscribe,
                        reply_markup=inline.buttons_for_sub(data)
                    )
        else:
            return await handler(event, data)
