from typing import List

from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database import Subscription
from bot.keyboards.user.factory import PaymentsCallback
from bot.utils.payok import Bill


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


def check_payment_pay_selection(url: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Ссылка на оплату',
        url=url
    )
    return builder.adjust(1).as_markup()


def check_payment(bill: Bill):
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Ссылка на оплату',
        url=PaymentsCallback(
            action='check_payment',
            payment_id=bill.id,
            amount=bill.amount,
            price=bill.price
        )
    )
    return builder.adjust(1).as_markup()
