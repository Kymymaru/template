from aiogram.fsm.state import StatesGroup, State


class LoadoutState(StatesGroup):
    get_count = State()


class MailingState(StatesGroup):
    get_post = State()
    get_count = State()
    get_order = State()


class ShowsState(StatesGroup):
    get_post = State()
    get_sent_count = State()


class SubscriptionsState(StatesGroup):
    get_message = State()
    get_link = State()


class RefState(StatesGroup):
    get_ref = State()
    get_price = State()


class CategoryState(StatesGroup):
    get_category_name = State()


class SubCategoryState(StatesGroup):
    get_subcategory_name = State()
    get_category_id = State()
