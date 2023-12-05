from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(
        text='Создать своего персонажа ➕'
    )
    builder.button(
        text='Поиск персонажа 🔍'
    )
    builder.button(
        text='Пользовательские персонажи 🤖'
    )
    builder.button(
        text='Мои персонажи 👥'
    )
    return builder.adjust(1, 1, 2).as_markup(
        resize_keyboard=True,
        input_field_placeholder='Введите /help для получения помощи в использовании'
    )


def cancel():
    builder = ReplyKeyboardBuilder()
    builder.button(
        text='Отмена ❌'
    )
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder='Нажмите кнопку чтобы отменить действие'
    )
