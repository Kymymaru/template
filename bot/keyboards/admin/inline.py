from math import ceil
from typing import List, Tuple

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.utils import funcs
from bot.database import Settings, Mailing, Show, Subscription, Ref
from bot.keyboards.admin.factory import LoadoutCallback, MailingCallback, ReferralCallback, PaginationCallback, \
    ShowsCallback, SubscriptionCallback

cancel = InlineKeyboardBuilder().button(
    text='Отмена', callback_data='cancel'
).as_markup()


def confirm_deleting(data: CallbackData, data_for_cancel: PaginationCallback = None):
    builder = InlineKeyboardBuilder()
    data.action = 'delete'
    builder.button(
        text='Подтвердить ✅',
        callback_data=data.pack()
    )
    data.action = 'page'
    builder.button(
        text='Отмена ❌',
        callback_data=data.pack() if data_for_cancel is None else data_for_cancel.pack()
    )
    return builder.adjust(1).as_markup()


def add_pagination(
        builder: InlineKeyboardBuilder,
        length: int = 7,
        from_pagination_to: str = '',
        page: int = 1,
) -> InlineKeyboardBuilder:
    if page > 1:
        builder.button(
            text='⏮',
            callback_data=PaginationCallback(page=page - 1, into=from_pagination_to).pack()
        )
    if length > 1:
        builder.button(
            text=f'{page} / {length}',
            callback_data='none'
        )
    if page < length:
        builder.button(
            text='⏭',
            callback_data=PaginationCallback(page=page + 1, into=from_pagination_to).pack()
        )
    return builder


def loadout():
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Всю базу пользователей',
        callback_data=LoadoutCallback(type='users', count='all').pack()
    )
    builder.button(
        text='Последних пользователей',
        callback_data=LoadoutCallback(type='users', count='last').pack()
    )
    builder.button(
        text='Всю Базу чатов(групп)',
        callback_data=LoadoutCallback(type='chats', count='all').pack()
    )
    builder.button(
        text='Последние чаты(группы)',
        callback_data=LoadoutCallback(type='users', count='last').pack()
    )
    builder.button(
        text='Получить последний файл выгрузки',
        callback_data=LoadoutCallback(type='None', count='file').pack()
    )
    return builder.adjust(2, 2, 1).as_markup()


def mailing_menu(settings: Settings, mailing: Mailing):
    builder = InlineKeyboardBuilder()
    size = [2, 2]
    builder.button(
        text='✉ ПОМЕНЯТЬ ПОСТ' if settings is not None and settings.message_id is not None else '✉ Отправить пост',
        callback_data=MailingCallback(action='post').pack()
    )
    builder.button(
        text='🏞 Предосмотр',
        callback_data=MailingCallback(action='preview').pack()
    )
    builder.button(
        text='👤 Количество',
        callback_data=MailingCallback(action='count').pack()
    )
    builder.button(
        text='👥 Порядок',
        callback_data=MailingCallback(action='order').pack()
    )
    if mailing:
        builder.button(
            text='🔄 Обновить',
            callback_data=MailingCallback(action='refresh').pack()
        )
        size.append(1)
    builder.button(
        text='✅ Запустить рассылку' if not mailing else '⭕ Остановить рассылку',
        callback_data=MailingCallback(action='start_mailing' if not mailing else 'stop_mailing').pack()
    )
    builder.button(
        text='🏠 Главное меню',
        callback_data=MailingCallback(action='main_menu').pack()
    )
    size.append(2)
    return builder.adjust(*size).as_markup()


def choice(prefix: str, buttons=None, general_buttons=None):
    builder = InlineKeyboardBuilder()
    if buttons is not None:
        for button in buttons:
            builder.button(
                text=button['text'],
                callback_data=button['callback_data']
            )
    else:
        buttons = []
    builder.button(
        text='🏠 Главное меню',
        callback_data=f'{prefix}:main_menu'
    )
    if general_buttons is not None:
        for button in general_buttons:
            builder.button(
                text=button['text'],
                callback_data=button['callback_data']
            )
    return builder.adjust(*[1 for i in range(len(buttons))], 1 + len(general_buttons)).as_markup()


def refs_markups(refs: List[Ref], page: int):
    rows_in_page = 10
    chunk_size = 3
    builder = InlineKeyboardBuilder()
    length = ceil(len(refs) / (rows_in_page * chunk_size))
    refs = refs[(rows_in_page * chunk_size) * (page - 1):(rows_in_page * chunk_size) * page]
    for ref in refs:
        data = ReferralCallback(
            action='info',
            type='user',
            ref=ref.ref,
            price=ref.price,
            page=page
        )
        builder.button(
            text=ref.ref,
            callback_data=data.pack()
        )
    size = [
        len(refs[i * chunk_size:(i + 1) * chunk_size])
        for i in range(int(len(refs) / chunk_size))
    ]
    builder = add_pagination(builder, length, from_pagination_to='ref', page=page)

    return builder.adjust(*size).as_markup()


def ref_buttons(data: ReferralCallback, graph: bool = True, back: bool = True) -> dict:
    builder = InlineKeyboardBuilder()
    size = []
    data.action = 'change'
    builder.button(
        text='Посмотреть статистику {} 📊'.format('чатов' if data.type == 'user' else 'юзеров'),
        callback_data=data.pack()
    )
    size.append(1)
    data.action = 'del'
    builder.button(
        text='Удалить ❌',
        callback_data=data.pack()
    )
    if graph:
        data.action = 'graph'
        builder.button(
            text='Получить график 📈',
            callback_data=data.pack()
        )
        size.append(2)
    else:
        size.append(1)
    if back and data.page != 0:
        data.action = 'main'
        builder.button(
            text='Назад 🔙',
            callback_data=PaginationCallback(
                page=data.page,
                into='ref'
            )
        )
        size.append(1)
    return builder.adjust(*size).as_markup()


def show_markups(shows: List[Show], page: int):
    count_in_page = 7
    builder = InlineKeyboardBuilder()
    if shows is not None:
        size = []
        length = ceil(len(shows) / count_in_page) if count_in_page else 1
        shows_in_page = shows[count_in_page * (page - 1):count_in_page * page]
        for i, show in enumerate(shows_in_page, start=1 if page == 1 else (count_in_page * (page - 1) + 1)):
            numerate_id = funcs.numerate(i)
            data = ShowsCallback(
                action='info',
                id=show.id,
                numerate_id=numerate_id,
                page=str(page),
                status=show.status
            )
            builder.button(
                text=numerate_id,
                callback_data=data.pack()
            )
            data.action = 'progress'
            builder.button(
                text=f'{show.sent} / {show.need_to_sent}',
                callback_data=data.pack()
            )
            data.action = 'status'
            builder.button(
                text='Вкл 🟢' if show.status == 1 else 'Выкл 🔴',
                callback_data=data.pack()
            )
            data.action = 'del'
            builder.button(
                text='🗑',
                callback_data=data.pack()
            )
            size.append(4)
        if page == length or length == 0:
            data = ShowsCallback(
                action='add',
                id=1,
                numerate_id='1',
                page=str(page),
                status='1'
            )
            builder.button(
                text='➕',
                callback_data=data.pack()
            )
            size.append(1)

    builder = add_pagination(builder, length, from_pagination_to='shows', page=page)
    size.append(3)
    builder.adjust(*size)
    return builder.as_markup()


def subscriptions_markup(subscriptions: List[Subscription], page: int):
    count_in_page = 7
    builder = InlineKeyboardBuilder()
    if subscriptions is not None:
        size = []
        length = ceil(len(subscriptions) / count_in_page) if count_in_page else 1
        subscriptions_in_page = subscriptions[count_in_page * (page - 1):count_in_page * page]
        for i, subscription in enumerate(subscriptions_in_page,
                                         start=1 if page == 1 else (count_in_page * (page - 1) + 1)):
            numerate_id = funcs.numerate(i)
            data = SubscriptionCallback(
                action='info',
                id=subscription.id,
                numerate_id=numerate_id,
                page=str(page),
                status=subscription.status
            )
            builder.button(
                text=numerate_id,
                callback_data=data.pack()
            )
            data.action = 'small_info'
            builder.button(
                text=subscription.title,
                callback_data=data.pack()
            )
            data.action = 'status'
            builder.button(
                text='Вкл 🟢' if subscription.status == 1 else 'Выкл 🔴',
                callback_data=data.pack()
            )
            data.action = 'del'
            builder.button(
                text='🗑',
                callback_data=data.pack()
            )
            size.append(4)
        if page == length or length == 0:
            data = SubscriptionCallback(
                action='add',
                id=1,
                numerate_id='1',
                page=str(page),
                status='1'
            )
            builder.button(
                text='➕',
                callback_data=data.pack()
            )
            size.append(1)

    builder = add_pagination(builder, length, from_pagination_to='subscriptions', page=page)
    size.append(3)
    return builder.adjust(*size).as_markup()


def subscription_keyboard(subscription: Subscription, data: SubscriptionCallback):
    builder = InlineKeyboardBuilder()
    data.action = 'status_'
    builder.button(
        text='Вкл 🟢' if subscription.status == 1 else 'Выкл 🔴',
        callback_data=data.pack()
    )
    data.action = 'del'
    builder.button(
        text='🗑',
        callback_data=data.pack()
    )
    data.action = 'page'
    builder.button(
        text='Назад 🔙',
        callback_data=data.pack()
    )
    return builder.adjust(2, 1).as_markup()
