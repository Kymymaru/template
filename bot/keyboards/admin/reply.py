from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_admin() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(
        text='Статистика 📊'
    )
    builder.button(
        text='Обяз. Подписка 🔐'
    )
    builder.button(
        text='Рассылка ✉️'
    )
    # builder.button(
    #     text='Прибыль 💰'
    # )
    builder.button(
        text='Рефералы 💵'
    )
    builder.button(
        text='Выгрузка 🗳'
    )
    builder.button(
        text='Показы 👀'
    )
    return builder.adjust(1, 3, 3).as_markup(
        resize_keyboard=True,
        input_field_placeholder='Добро пожаловать в админ панель 🏚'
    )


def ref_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(
        text='Создать рефку ➕'
    )
    builder.button(
        text='Список реф. ссылок 💵'
    )
    builder.button(
        text='Вернутся в админ панель 🔙'
    )
    return builder.adjust(1).as_markup(
        resize_keyboard=True,
        input_field_placeholder='Меню рефералов 💵'
    )


def cancel():
    builder = ReplyKeyboardBuilder()
    builder.button(
        text='Отмена ❌'
    )
    return builder.adjust(1, 3, 3).as_markup(
        resize_keyboard=True,
        input_field_placeholder='Меню рефералов 💵'
    )
