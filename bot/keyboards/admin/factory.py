from aiogram.filters.callback_data import CallbackData


class PaginationCallback(CallbackData, prefix='page'):
    page: int
    into: str


class ReferralCallback(CallbackData, prefix='ref'):
    action: str
    type: str = 'user'
    ref: str
    price: int
    page: int


class SubscriptionCallback(CallbackData, prefix='subscription'):
    action: str
    id: int = None
    numerate_id: str = None
    page: int = None
    status: int = None


class ShowsCallback(CallbackData, prefix='shows'):
    action: str
    id: int = None
    numerate_id: str = None
    page: int = None
    status: int = None


class LoadoutCallback(CallbackData, prefix='loadout'):
    type: str
    count: str


class MailingCallback(CallbackData, prefix='mailing'):
    action: str
