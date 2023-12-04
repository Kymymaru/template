from aiogram import types, Router
from aiogram.filters import Command
import shutil
import platform
import os

router = Router(name='get_logs')


@router.message(Command('get_logs'))
async def get_logs_command(message: types.Message, config):
    await message.answer('Начинаю архивацию логов...\nЭто может занять некоторое время')
    system_info = platform.system()
    if system_info == "Windows":
        archive_name = f'../{config.bot.logs_folder_name}' + '.zip'
    else:
        archive_name = f'../{config.bot.logs_folder_name}' + '.tar.gz'

    # Создание архива
    if system_info == "Windows":
        archive_format = 'zip'
    else:
        archive_format = 'gztar'
    shutil.make_archive(f'../{config.bot.logs_folder_name}',
                        archive_format,
                        f'../{config.bot.logs_folder_name}')
    archive_path = os.path.abspath(archive_name)
    await message.answer_document(
        document=types.FSInputFile(
            archive_path
        )
    )
    os.remove(archive_path)
