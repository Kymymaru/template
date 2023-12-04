from aiogram.filters import BaseFilter


class AdminFilter(BaseFilter):
    async def __call__(self, event, config) -> bool:
        return event.from_user.id in config.bot.admins
