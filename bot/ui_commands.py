from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat, BotCommandScopeAllGroupChats
from loguru import logger
from aiogram.exceptions import TelegramBadRequest


async def set_bot_commands(bot: Bot, admins):
    user_commands = [
        BotCommand(command='start', description='Перезагрузить бота')
    ]
    admin_commands = [
        BotCommand(command='admin', description='Панель администратора'),
        BotCommand(command='get_logs', description='Получить логи'),
    ]
    group_commands = [
        BotCommand(command='help', description='Помощь'),
    ]
    await bot.set_my_commands(commands=user_commands, scope=BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(commands=group_commands, scope=BotCommandScopeAllGroupChats())
    for admin_id in admins:
        try:
            await bot.set_my_commands(
                commands=[*admin_commands, *user_commands],
                scope=BotCommandScopeChat(
                    chat_id=admin_id
                )
            )
        except TelegramBadRequest:
            logger.warning(f'Administrator {admin_id} don`t start conversation with bot')
