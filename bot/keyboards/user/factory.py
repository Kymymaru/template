from aiogram.filters.callback_data import CallbackData


class PaymentsCallback(CallbackData, prefix='payments'):
    action: str
    payment_id: str
    amount: str
    price: str
