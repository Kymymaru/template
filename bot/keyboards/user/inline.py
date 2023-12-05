from typing import List

from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database import Subscription


def buttons_for_sub(subscriptions: List[Subscription]):
    builder = InlineKeyboardBuilder()
    for subscription in subscriptions:
        builder.button(
            text=subscription.title,
            url=subscription.link
        )
    builder.button(
        text='Я подписался ✅',
        callback_data='check_sub'
    )
    return builder.adjust(1).as_markup()
