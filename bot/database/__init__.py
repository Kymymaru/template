from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.config import DB
from .models import *


class Database:
    user: User = User
    chat: Chat = Chat

    def __init__(self, database: DB):
        self.config = database
        self.engine = create_async_engine(
            url='mysql+aiomysql://'
                f'{database.user}:'
                f'{database.password}@'
                f'{database.host}/'
                f'{database.database}',
            echo=False, pool_size=20, max_overflow=10
        )
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)

    def get_session(self) -> AsyncSession:
        return self.session_maker()

    async def create_tables(self):
        async with self.engine.begin() as conn:
            if self.config.debug:
                await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
